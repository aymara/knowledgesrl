#!/usr/bin/env python3

import copy
from collections import OrderedDict
from xml.etree import ElementTree as ET
import json

import colorama
from colorama import Fore
from nltk.corpus import verbnet
from nltk.corpus import verbenet

import paths
from .rolemapping import RoleMapping
from .dicoxml import deindent_text
from .kicktionary import kicktionary_frames


def xmlcontext_to_frame(lang, xmlns, lexie, contexte):
    indented_sentence_text = contexte.find('{{{0}}}contexte-texte'.format(xmlns)).text
    sentence_text = deindent_text(indented_sentence_text)

    subcategorization_frame = ET.Element('SYNTAX')
    role = None

    for child in contexte:
        last_role = role
        role = None

        # predicate (TODO auxiliaires)
        if (child.tag == '{{{0}}}lexie-att'.format(xmlns) and
                'auxiliaire' not in child.attrib):
            predicate_lemma = child.get("lemme", deindent_text(child.text))
            predicate_lemma = predicate_lemma.lower().strip()
            ET.SubElement(subcategorization_frame, 'VERB')

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

            # role_filler = dicoxml.get_all_text(child)
            # TODO extract headword

            phrase_type_per_lang = {
                'en': {'Pro': 'NP', 'AdvP': 'ADV', 'Clause': 'S', 'PP': 'PP', 'NP': 'NP'},
                'fr': {'Pro': 'NP', 'SN': 'NP', 'SP': 'PP', 'Prop': 'S', 'SAdv': 'ADV'}
            }

            vn_phrase_type = phrase_type_per_lang[lang][phrase_type]

            if vn_phrase_type == 'PP':
                assert 'preposition' in groupe_syntaxique.attrib
                ET.SubElement(
                    subcategorization_frame, 'PREP',
                    value=groupe_syntaxique.get('preposition'))
                ET.SubElement(subcategorization_frame, 'NP', value=role)
            else:
                ET.SubElement(subcategorization_frame, vn_phrase_type, value=role)

    return sentence_text, subcategorization_frame


def get_dico_examples(lang, dico, xmlns):
    xml_dico = ET.ElementTree(file=dico)
    for lexie in xml_dico.findall('lexie'):
        if not lexie.get('no'):
            continue

        frame_name = '{}.{}'.format(lexie.get('id'), lexie.get('no'))
        for contexte in lexie.findall('contextes/{{{0}}}contexte'.format(xmlns)):
            sentence_text, subcategorization_frame = xmlcontext_to_frame(lang, xmlns, lexie, contexte)
            yield (frame_name, lexie.get('id'), sentence_text, subcategorization_frame)


def debug(should_debug, stuff, end='\n'):
    if should_debug:
        if stuff:
            for part in stuff:
                print(part, end=' ')
        print(end=end)


def matches_verbnet_frame(gold_syntax, vn_syntax):
    vn_subcat = [syntax_part.tag for syntax_part in vn_syntax]
    dico_subcat = [syntax_part.tag for syntax_part in gold_syntax]

    return dico_subcat == vn_subcat


def remove_before_v(syntax):
    syntax = copy.deepcopy(syntax)
    new_syntax = ET.Element('SYNTAX')

    found_v = False
    for part in syntax:
        if part.tag == 'VERB':
            found_v = True

        if found_v:
            new_syntax.append(part)

    return new_syntax


def map_gold_frame(vn_id, gold_syntax, role_mapping_lexie):
    if vn_id not in role_mapping_lexie:
        return ET.Element('SYNTAX')

    mapped_gold_syntax = ET.Element('SYNTAX')
    for part in gold_syntax:
        if part.tag != 'PREP' and part.get('value'):
            ET.SubElement(mapped_gold_syntax, part.tag, value=role_mapping_lexie[vn_id][part.get('value')])
        else:
            mapped_gold_syntax.append(part)

    return mapped_gold_syntax


def syntax_to_str(syntax):
    str_parts = []

    if not(list(syntax)):  # no children
        return '-'

    for part in syntax:
        if part.tag == 'VERB':
            str_parts.append('V')
        elif part.tag == 'NP':
            str_parts.append('NP.{}'.format(part.get('value')))
        elif part.tag == 'PREP':
            if part.find('SELRESTRS'):
                selrestr_list = []
                for selrestr in part.findall('SELRESTRS/SELRESTR'):
                    selrestr = part.find('SELRESTRS/SELRESTR')
                    selrestr_list.append('{}{}'.format(selrestr.get('Value'), selrestr.get('type')))
                str_parts.append('-'.join(selrestr_list))
            else:
                str_parts.append(part.get('value'))
        else:
            str_parts.append(part.tag)

    return ' '.join(str_parts)


def analyze_constructs(examples, role_mapping, evaluation_sets, verbnet):
    annotated_sentences, lemma_in_vn = 0, 0
    n_correct_frames, n_frames = 0, 0
    n_correct_roles, n_roles = 0, 0
    n_classes_in_list, n_classes = 0, 0

    for lexie, lemma, sentence_text, gold_syntax in examples:
        d = sentence_text in [sentence for source, sentence in evaluation_sets['train']]
        test_context = sentence_text in [sentence for source, sentence in evaluation_sets['test']]

        debug(d, [])

        if d == test_context:
            print(d, test_context, sentence_text)
        assert d != test_context

        debug(d, [lexie, lemma, sentence_text])
        if test_context:
            annotated_sentences += 1

        # First possible error: lemma does not exist in VerbNet
        if not verbnet.classids(lemma):
            continue

        if test_context:
            lemma_in_vn += 1
            n_frames += 1

        considered_syntax = []
        for vn_frame in verbnet.frames_for_lemma(lemma):
            vn_syntax = vn_frame['frame'].find('SYNTAX')
            # If sentence starts with a verb, remove anything that's before
            # the verb in VerbNet
            if next(iter(gold_syntax)).tag == 'VERB':
                vn_syntax = remove_before_v(vn_syntax)
            considered_syntax.append((vn_frame['classid'], vn_syntax))

        # Use an OrderedDict for now to get the same behavior than
        # with the tuple list
        vn_syntax_matches = OrderedDict()
        for classid, vn_syntax in considered_syntax:
            if matches_verbnet_frame(gold_syntax, vn_syntax):
                if classid not in vn_syntax_matches:
                    vn_syntax_matches[classid] = []
                # check if vn_syntax is already in there?
                vn_syntax_matches[classid].append(vn_syntax)

        # Second possible error: syntactic pattern is not in VerbNet
        if not vn_syntax_matches:
            debug(d, ['   ', Fore.RED, syntax_to_str(gold_syntax), Fore.RESET])
            continue

        if test_context:
            n_correct_frames += 1
            n_classes += 1

        if lexie not in role_mapping:
            raise Exception('Missing lexie {} ({}) in role mapping.'.format(lexie, lemma))

        debug(d, ['   ', Fore.GREEN, syntax_to_str(gold_syntax), '->', syntax_to_str(map_gold_frame(classid, gold_syntax, role_mapping[lexie])), Fore.RESET])

        for classid in vn_syntax_matches:
            debug(d, ['    ', classid, ' -> ',
                [syntax_to_str(vn_syntax) for vn_syntax in
                    vn_syntax_matches[classid]]])

        class_matches = set(vn_syntax_matches.keys()) & set(role_mapping[lexie])
        if not class_matches:
            continue

        if test_context:
            n_classes_in_list += 1

        classid  = next(iter(class_matches))
        vn_syntax = vn_syntax_matches[classid][0]

        if classid not in role_mapping[lexie]:
            continue

        for i, correct_syntax in enumerate(gold_syntax):
            # if this is a 'frame element', not a V or anything else
            if correct_syntax.tag in ['NP', 'S']:
                if role_mapping[lexie] == {}:
                    # missing sense
                    # TODO handle this explicitly using XML annotations
                    pass
                elif classid not in role_mapping[lexie]:
                    raise Exception('{} misses {} class'.format(lexie, classid))
                elif correct_syntax.get('value') not in role_mapping[lexie][classid]:
                    raise Exception('{} misses {} mapping'.format(lexie, correct_syntax.get('value')))

                if test_context:
                    n_roles += 1

                candidate_roles = set()
                candidate_roles.add(list(vn_syntax)[i].get('value'))

                if role_mapping[lexie][classid][correct_syntax.get('value')] in candidate_roles:
                    if test_context:
                        n_correct_roles += 1 / len(candidate_roles)

    print(annotated_sentences, n_frames, n_classes, n_roles)
    print('-                          {:.0%} of lemma tokens are here'.format(lemma_in_vn/annotated_sentences))
    print('- For these tokens,        {:.1%} of constructions are correct'.format(n_correct_frames/n_frames))
    print('- For these constructions, {:.1%} of classes are here'.format(n_classes_in_list/max(n_classes, 1)))
    print('- For these classes,       {:.1%} of roles are correct'.format(n_correct_roles/max(n_roles, 1)))
    print()

if __name__ == '__main__':
    colorama.init()

    verbnet_modules = {
        'fr': verbenet,
        'en': verbnet
    }

    for lang in ['en', 'fr']:
        # DicoInfo, DicoEnviro
        for domain in ['info', 'enviro']:
            dico = {'domain': domain, 'lang': lang}
            print('--- dico{domain}_{lang}'.format(**dico))
            evaluation_sets = {
                'train': json.load(open(str(paths.Paths.ROOT / paths.Paths.DICO_TRAIN.format(**dico)))),
                'test': json.load(open(str(paths.Paths.ROOT / paths.Paths.DICO_TEST.format(**dico))))
            }

            dico_examples = get_dico_examples(lang, str(paths.Paths.ROOT / paths.Paths.DICO_XML.format(**dico)), paths.Paths.DICO_XMLNS[domain])
            role_mapping = RoleMapping(str(paths.Paths.ROOT / paths.Paths.DICO_MAPPING.format(**dico)))

            analyze_constructs(dico_examples, role_mapping, evaluation_sets, verbnet_modules[lang])

        print('--- kicktionary_{}'.format(lang))
        # Kicktionary
        kicktionary_evaluation = {
            'train': json.load(open(str(paths.Paths.ROOT / paths.Paths.KICKTIONARY_SETS.format('train', lang)))),
            'test': json.load(open(str(paths.Paths.ROOT / paths.Paths.KICKTIONARY_SETS.format('test', lang)))),
        }
        kicktionary_examples = kicktionary_frames(lang)
        role_mapping = RoleMapping(str(paths.Paths.KICKTIONARY_ROLES).format(lang))
        analyze_constructs(kicktionary_examples, role_mapping, kicktionary_evaluation, verbnet_modules[lang])
