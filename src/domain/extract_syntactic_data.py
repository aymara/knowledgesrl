#!/usr/bin/env python3

import copy
import collections
import re
import os.path
from xml.etree import ElementTree as ET
import pickle
from hashlib import sha256

import colorama
from colorama import Fore

import paths
import verbnet
from .rolemapping import RoleMapping
from .dicoxml import deindent_text, get_all_text

def xmlcontext_to_frame(xmlns, lexie, contexte):
    indented_sentence_text = contexte.find('{{{0}}}contexte-texte'.format(xmlns)).text
    sentence_text = deindent_text(indented_sentence_text)
    sentence_hash = sha256(sentence_text.encode('utf-8')).hexdigest()

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

    return sentence_hash, subcategorization_frame


def get_dico_examples(dico, xmlns):
    xml_dico = ET.ElementTree(file=dico)
    for lexie in xml_dico.findall('lexie'):
        frame_name = '{}.{}'.format(lexie.get('id'), lexie.get('no'))
        for contexte in lexie.findall('contextes/{{{0}}}contexte'.format(xmlns)):
            sentence_hash, subcategorization_frame = xmlcontext_to_frame(xmlns, lexie, contexte)
            yield (frame_name, lexie.get('id'), sentence_hash, subcategorization_frame)


def debug(should_debug, stuff, end='\n'):
    if should_debug:
        if stuff:
            for part in stuff:
                print(part, end=' ')
        print(end=end)


def matches_verbnet_frame(dico_syntax, vn_syntax):
    vn_subcat = [syntax_part['type'] for syntax_part in vn_syntax]
    dico_subcat = [syntax_part['type'] for syntax_part in dico_syntax]

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

def analyze_constructs(dico_examples, role_mapping, evaluation_sets):
    annotated_sentences, lemma_in_vn = 0, 0
    valid_frames, missing_frames = 0, 0
    n_correct_roles, n_wrong_roles = 0, 0

    for lexie, lemma, sentence_hash, dico_syntax in dico_examples:
        d = sentence_hash in evaluation_sets['train']  # debug
        test_context = sentence_hash in evaluation_sets['test']  # score

        debug(d, [lexie])
        if test_context:
            annotated_sentences += 1

        # First possible error: lemma does not exist in VerbNet
        if lemma not in verbnet.classes_for_predicate:
            continue

        if test_context:
            lemma_in_vn += 1

        considered_syntax = []
        # TODO assign class too
        for vn_class in verbnet.classes_for_predicate[lemma]:
            for vn_frame in vn_class.all_frames():
                if dico_syntax[0]['type'] == 'V':
                    # Remove anything that's before the verb in VerbNet
                    vn_frame = remove_before_v(vn_frame)
                considered_syntax.append(vn_frame.syntax)

        vn_syntax_matches = []
        for vn_syntax in considered_syntax:
            if matches_verbnet_frame(dico_syntax, vn_syntax) and not vn_syntax in vn_syntax_matches:
                vn_syntax_matches.append(vn_syntax)

        # Second possible error: syntactic pattern is not in VerbNet
        if not vn_syntax_matches:
            debug(d, ['    ', Fore.RED, dico_syntax, Fore.RESET])
            if test_context:
                missing_frames += 1
            continue

        debug(d, ['    ', Fore.GREEN, dico_syntax, Fore.RESET, vn_syntax_matches])
        if test_context:
            valid_frames += 1

        for i, correct_syntax in enumerate(dico_syntax):
            # if this is a 'frame element', not a V or anything else
            if 'role' in correct_syntax:
                candidate_roles = set()

                for syntax in vn_syntax_matches:
                    candidate_roles.add(syntax[i]['role'])

                if role_mapping[lexie] == {}:
                    if test_context:
                        n_wrong_roles += 1
                elif correct_syntax.get('role') not in role_mapping[lexie]:
                    raise Exception('{} misses {} mapping'.format(lexie, correct_syntax.get('role')))
                elif role_mapping[lexie][correct_syntax.get('role')] in candidate_roles:
                    if test_context:
                        n_correct_roles += 1 / len(candidate_roles)
                else:
                    if test_context:
                        n_wrong_roles += 1

    print('{:.0%} of lemma tokens are here'.format(lemma_in_vn/annotated_sentences))
    print('For these tokens, {:.1%} of constructions are here'.format(valid_frames/(valid_frames + missing_frames)))
    print('For those constructions, {:.1%} of roles are correct'.format(n_correct_roles/(n_correct_roles+n_wrong_roles)))

if __name__ == '__main__':
    colorama.init()

    # DicoInfo, DicoEnviro
    for dico in paths.DICOS:
        print(dico['xml'])
        evaluation_sets = {
            'train': pickle.load(open(os.path.join(dico['root'], dico['train']), 'rb')),
            'test': pickle.load(open(os.path.join(dico['root'], dico['test']), 'rb'))
        }

        dico_examples = get_dico_examples(os.path.join(dico['root'], dico['xml']), dico['xmlns'])
        role_mapping = RoleMapping(os.path.join(dico['root'], dico['mapping']))

        analyze_constructs(dico_examples, role_mapping, evaluation_sets)
