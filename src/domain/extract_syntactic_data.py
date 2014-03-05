#!/usr/bin/env python3

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
from rolemapping import RoleMapping
from dicoxml import deindent_text, get_all_text


def retrieve_constructs(dico, xmlns):
    frames_for_lexie = collections.defaultdict(list)

    xml_dico = ET.ElementTree(file=dico)
    for lexie in xml_dico.findall('lexie'):
        frame_name = '{}.{}'.format(lexie.get('id'), lexie.get('no'))
        for contexte in lexie.findall('contextes/{{{0}}}contexte'.format(xmlns)):

            indented_sentence_text = contexte.find('{{{0}}}contexte-texte'.format(xmlns)).text
            sentence_text = deindent_text(indented_sentence_text)
            sentence_hash = sha256(sentence_text.encode('utf-8')).hexdigest()

            subcategorization_frame = verbnet.Syntax()

            for child in contexte:
                # predicate (TODO auxiliaires)
                if (child.tag == '{{{0}}}lexie-att'.format(xmlns) and
                        not 'auxiliaire' in child.attrib):
                    predicate_lemma = child.get("lemme", deindent_text(child.text))
                    predicate_lemma = predicate_lemma.lower().strip()
                    subcategorization_frame.append({'type': 'V'})

                # frame element
                elif child.tag == '{{{0}}}participant'.format(xmlns):
                    groupe_syntaxique = child.find(
                        "{{{0}}}fonction-syntaxique/{{{0}}}groupe-syntaxique".format(xmlns))
                    phrase_type = groupe_syntaxique.get('nom')

                    role = child.get('role')
                    core = True if child.get('type') == 'Act' else False
                    role_filler = get_all_text(child)

                    if phrase_type == 'Pro':
                        phrase_type = 'NP'
                    elif phrase_type == 'AdvP':
                        phrase_type = 'ADV'
                    elif phrase_type == 'Clause':
                        # TODO analysis to write info in SYNRESTRS maybe
                        phrase_type = 'NP'

                    if core:
                        if phrase_type == 'PP':
                            assert 'preposition' in groupe_syntaxique.attrib
                            subcategorization_frame.append({
                                'type': 'PREP',
                                'value': groupe_syntaxique.get('preposition')
                            })
                            subcategorization_frame.append({'type': 'NP', 'role': role})
                        else:
                            subcategorization_frame.append({'type': phrase_type, 'role': role})

            frames_for_lexie[frame_name].append((sentence_hash, subcategorization_frame))

    return frames_for_lexie


def debug(should_debug, stuff, end='\n'):
    if should_debug:
        if stuff:
            for part in stuff:
                print(part, end=' ')
        print(end=end)


def matches_verbnet_frame(dico_frame, vn_frame):
    vn_subcat = [syntax_part['type'] for syntax_part in vn_frame.syntax]
    dico_subcat = [syntax_part['type'] for syntax_part in dico_frame]

    return dico_subcat == vn_subcat


def analyze_constructs(lexie_groups, frames_for_lexie, classes_for_predicate, to_verbnet):
    annotated_sentences, lemma_in_vn = 0, 0
    valid_frames, missing_frames = 0, 0
    n_correct_roles, n_wrong_roles = 0, 0

    for lexie in frames_for_lexie:
        lemma = lexie.split('.')[0]

        if not lexie in to_verbnet:
            raise Exception(lexie)

        for sentence_hash, dico_frame in frames_for_lexie[lexie]:
            d = sentence_hash in lexie_groups['train']  # debug
            test_context = sentence_hash in lexie_groups['test']  # score

            debug(d, [lexie])
            if test_context:
                annotated_sentences += 1

            # First possible error: lemma does not exist in VerbNet
            if lemma not in classes_for_predicate:
                continue

            if test_context:
                lemma_in_vn += 1

            vn_frame_matches = set()
            for vn_class in classes_for_predicate[lemma]:
                for vn_frame in vn_class.all_frames():
                    if matches_verbnet_frame(dico_frame, vn_frame):
                        vn_frame_matches.add(vn_frame)

            # Second possible error: syntactic pattern is not in VerbNet
            if not vn_frame_matches:
                debug(d, ['    ', Fore.RED, dico_frame, Fore.RESET])
                if test_context:
                    missing_frames += 1
                continue

            debug(d, ['    ', Fore.GREEN, dico_frame, Fore.RESET, vn_frame_matches])
            if test_context:
                valid_frames += 1

            for i, correct_syntax in enumerate(dico_frame):
                # if this is a 'frame element', not a V or anything else
                if 'role' in correct_syntax:
                    candidate_roles = set()

                    for frame in vn_frame_matches:
                        candidate_roles.add(frame.syntax[i]['role'])

                    if to_verbnet[lexie] == {}:
                        if test_context:
                            n_wrong_roles += 1
                    elif to_verbnet[lexie][correct_syntax.get('role')] in candidate_roles:
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
    #vn_reader = verbnetreader.VerbnetReader(paths.VERBNET_PATH, replace_pp = False)
    #normalized_frames = normalize_vn_frames(vn_reader.frames_for_verb)

    for dico in paths.DICOS:
        print(dico['xml'])
        lexies = {
            'train': pickle.load(open(os.path.join(dico['root'], dico['train']), 'rb')),
            'test': pickle.load(open(os.path.join(dico['root'], dico['test']), 'rb'))
        }

        frames_for_lexie = retrieve_constructs(os.path.join(dico['root'], dico['xml']), dico['xmlns'])
        analyze_constructs(lexies,
                           frames_for_lexie,
                           verbnet.classes_for_predicate,
                           RoleMapping(os.path.join(dico['root'], dico['mapping'])))
