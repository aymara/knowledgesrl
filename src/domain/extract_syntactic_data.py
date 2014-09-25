#!/usr/bin/env python3

import copy
import collections
import re
from xml.etree import ElementTree as ET
import json
import pickle

import colorama
from colorama import Fore

import paths
import verbnet
from .rolemapping import RoleMapping
from .dicoxml import deindent_text, get_all_text
from .kicktionary import kicktionary_frames

def xmlcontext_to_frame(xmlns, lexie, contexte):
    indented_sentence_text = contexte.find('{{{0}}}contexte-texte'.format(xmlns)).text
    sentence_text = deindent_text(indented_sentence_text)

    subcategorization_frame = verbnet.Syntax()
    role = None

    for child in contexte:
        last_role = role
        role = None

        # predicate (TODO auxiliaires)
        if (child.tag == '{{{0}}}lexie-att'.format(xmlns) and
                not 'auxiliaire' in child.attrib):
            predicate_lemma = child.get("lemme", deindent_text(child.text))
            predicate_lemma = predicate_lemma.lower().strip()
            subcategorization_frame.append({'type': 'V'})

        # frame element
        elif child.tag == '{{{0}}}participant'.format(xmlns) and child.get('type') == 'Act':
            role = child.get('role')

            # Dico* adds various frame elements when they're separated
            # by coordinating conjunctions as in 'I bought umbrellas
            # and pens'
            if role == last_role:
                continue

            groupe_syntaxique = child.find(
                "{{{0}}}fonction-syntaxique/{{{0}}}groupe-syntaxique".format(xmlns))
            phrase_type = groupe_syntaxique.get('nom')

            role_filler = get_all_text(child)

            if phrase_type == 'Pro':
                phrase_type = 'NP'
            elif phrase_type == 'AdvP':
                phrase_type = 'ADV'
            elif phrase_type == 'Clause':
                # TODO analysis to write info in SYNRESTRS maybe
                phrase_type = 'NP'

            if phrase_type == 'PP':
                assert 'preposition' in groupe_syntaxique.attrib
                subcategorization_frame.append({
                    'type': 'PREP',
                    'value': groupe_syntaxique.get('preposition')
                })
                subcategorization_frame.append({'type': 'NP', 'role': role})
            else:
                subcategorization_frame.append({'type': phrase_type, 'role': role})

    return sentence_text, subcategorization_frame


def get_dico_examples(dico, xmlns):
    xml_dico = ET.ElementTree(file=dico)
    for lexie in xml_dico.findall('lexie'):
        frame_name = '{}.{}'.format(lexie.get('id'), lexie.get('no'))
        for contexte in lexie.findall('contextes/{{{0}}}contexte'.format(xmlns)):
            sentence_text, subcategorization_frame = xmlcontext_to_frame(xmlns, lexie, contexte)
            yield (frame_name, lexie.get('id'), sentence_text, subcategorization_frame)


def debug(should_debug, stuff, end='\n'):
    if should_debug:
        if stuff:
            for part in stuff:
                print(part, end=' ')
        print(end=end)


def matches_verbnet_frame(gold_syntax, vn_syntax):
    vn_subcat = [syntax_part['type'] for syntax_part in vn_syntax]
    dico_subcat = [syntax_part['type'] for syntax_part in gold_syntax]

    return dico_subcat == vn_subcat

def remove_before_v(frame):
    frame = copy.deepcopy(frame)
    new_syntax = verbnet.Syntax()

    found_v = False
    for part in frame.syntax:
        if part['type'] == 'V':
            found_v = True
        if found_v:
            new_syntax.append(part)

    frame.syntax = new_syntax
    return frame

def map_gold_frame(vn_id, gold_syntax, role_mapping_lexie):
    if not vn_id in role_mapping_lexie:
        return verbnet.Syntax()

    mapped_gold_syntax = verbnet.Syntax()
    for part in gold_syntax:
        if 'role' in part:
            mapped_gold_syntax.append({'role': role_mapping_lexie[vn_id][part['role']], 'type': part['type']})
        else:
            mapped_gold_syntax.append(part)
    return mapped_gold_syntax

def analyze_constructs(examples, role_mapping, evaluation_sets):
    annotated_sentences, lemma_in_vn = 0, 0
    n_correct_frames, n_frames = 0, 0
    n_correct_roles, n_roles = 0, 0
    n_correct_classes, n_classes = 0, 0

    for lexie, lemma, sentence_text, gold_syntax in examples:
        d = sentence_text in [sentence for source, sentence in evaluation_sets['train']]
        test_context = sentence_text in [sentence for source, sentence in evaluation_sets['test']]

        if d == test_context:
            print(d, test_context, sentence_text)
        assert d != test_context

        debug(d, [lexie, lemma])
        if test_context:
            annotated_sentences += 1

        # First possible error: lemma does not exist in VerbNet
        if lemma not in verbnet.classes_for_predicate:
            continue

        if test_context:
            lemma_in_vn += 1
            n_frames += 1

        considered_syntax = []
        for vn_class in verbnet.classes_for_predicate[lemma]:
            for vn_frame in vn_class.all_frames():
                # If sentence starts with a verb, remove anything that's before
                # the verb in VerbNet
                if gold_syntax[0]['type'] == 'V':
                    vn_frame = remove_before_v(vn_frame)
                considered_syntax.append((vn_class, vn_frame.syntax))

        vn_syntax_matches = []
        for vn_class, vn_syntax in considered_syntax:
            if matches_verbnet_frame(gold_syntax, vn_syntax) and not vn_syntax in vn_syntax_matches:
                vn_syntax_matches.append((vn_class, vn_syntax))

        # Second possible error: syntactic pattern is not in VerbNet
        if not vn_syntax_matches:
            debug(d, ['   ', Fore.RED, gold_syntax, Fore.RESET])
            continue

        if test_context:
            n_correct_frames += 1
            n_classes += 1

        debug(d, ['    ', vn_class.vn_id, vn_syntax])
        debug(d, ['   ',  Fore.GREEN, gold_syntax, Fore.RESET])
        debug(d, ['   ',  Fore.GREEN, map_gold_frame(vn_class.vn_id, gold_syntax, role_mapping[lexie]), Fore.RESET])


        # TODO better choice strategy?
        vn_class, vn_syntax = vn_syntax_matches[0]

        if not vn_class.vn_id in role_mapping[lexie]:
            continue

        if test_context:
                n_correct_classes += 1

        for i, correct_syntax in enumerate(gold_syntax):
            # if this is a 'frame element', not a V or anything else
            if 'role' in correct_syntax:
                if role_mapping[lexie] == {}:
                    # missing sense
                    pass
                elif not vn_class.vn_id in role_mapping[lexie]:
                    break
                    raise Exception('{} misses {} class'.format(lexie, vn_class.vn_id))
                elif correct_syntax.get('role') not in role_mapping[lexie][vn_class.vn_id]:
                    raise Exception('{} misses {} mapping'.format(lexie, correct_syntax.get('role')))


                if test_context:
                    n_roles += 1

                candidate_roles = set()
                candidate_roles.add(vn_syntax[i]['role'])

                if role_mapping[lexie][vn_class.vn_id][correct_syntax.get('role')] in candidate_roles:
                    if test_context:
                        n_correct_roles += 1 / len(candidate_roles)

    print('                         {:.0%} of lemma tokens are here'.format(lemma_in_vn/annotated_sentences))
    print('For these tokens,        {:.1%} of constructions are here'.format(n_correct_frames/n_frames))
    print('For these constructions, {:.1%} of classes are here'.format(n_correct_classes/n_classes))
    print('For these classes,       {:.1%} of roles are correct'.format(n_correct_roles/n_roles))
    print()

if __name__ == '__main__':
    colorama.init()

    for lang in ['en']:
        # DicoInfo, DicoEnviro
        for domain in ['info', 'enviro']:
            dico = {'domain': domain, 'lang': lang}
            print('--- dico{domain}_{lang}'.format(**dico))
            evaluation_sets = {
                'train': json.load(open(str(paths.ROOT / paths.DICO_TRAIN.format(**dico)))),
                'test': json.load(open(str(paths.ROOT / paths.DICO_TEST.format(**dico))))
            }

            dico_examples = get_dico_examples(str(paths.ROOT / paths.DICO_XML.format(**dico)), paths.DICO_XMLNS[domain])
            role_mapping = RoleMapping(str(paths.ROOT / paths.DICO_MAPPING.format(**dico)))

            analyze_constructs(dico_examples, role_mapping, evaluation_sets)

        print('--- kicktionary_{}'.format(lang))
        # Kicktionary
        kicktionary_evaluation = {
            'train': json.load(open(str(paths.ROOT / paths.KICKTIONARY_SETS.format('train', lang)))),
            'test': json.load(open(str(paths.ROOT / paths.KICKTIONARY_SETS.format('test', lang)))),
        }
        kicktionary_examples = kicktionary_frames('en')
        role_mapping = RoleMapping(paths.KICKTIONARY_ROLES)
        analyze_constructs(kicktionary_examples, role_mapping, kicktionary_evaluation)

