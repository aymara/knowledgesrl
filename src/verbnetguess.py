#!/usr/bin/env python3
"""Guesses VerbNet XML's DESCRIPTION.primary using SYNTAX

The goal here is to how important is DESCRIPTION.primary (eg. NP V NP) and see
if it can be discarded in favour of <SYNTAX> which is easier to parse as it is
structured.

It's an easy way to make sure our understanding of <SYNTAX> is correct.

"""

import unittest
from distutils.version import LooseVersion
import warnings

from nltk.corpus import verbnet

def classid_to_number(classid):
    number = '-'.join(classid.split('-')[1:])
    # prevent LooseVersion bug: 109-1-1 can't compare with 80.1
    number = number.replace('-', '.')
    return number

def strip_roles(primary):
    out_list = []

    for part in primary.split(' '):
        if '.' or '-' in part:
            without_dot = part.split('.')[0]
            without_dash = without_dot.split('-')[0]
            out_list.append(without_dash)
        else:
            out_list.append(part)

    return ' '.join(out_list)

def check_all_restr(part, value, type_):
    if type(type_) == str:
        type_list = [type_]
    elif type(type_) == list:
        type_list = type_
    else:
        raise Exception('Invalid type {}'.format(type_))

    return any([check_restr(synrestr, value, type_) for synrestr in part.findall('SYNRESTRS/SYNRESTR') for type_ in type_list])

def check_restr(synrestr, value, type_):
    value_found, type_found = synrestr.get('Value'), synrestr.get('type')

    if value == '_' and type_ == '_':
        raise Exception('Both value and type are unrestricted.')
    elif value == '_':
        return type_ == type_found
    elif type_ == '_':
        raise Exception('It makes no sense to only restrict on Value.')
    else:
        # restrict on both type and value
        return type_ == type_found and value == value_found

def syntax_to_primary(syntax):
    out_list = []
    i = 0

    while i < len(syntax):
        part = syntax[i]
        if part.tag == 'NP':

            if check_all_restr(part, '+', 'adv_loc'):
                out_list.append('ADVP')
            elif check_all_restr(part, '+', 'adj'):
                out_list.append('ADJP')

            elif check_all_restr(part, '+', ['that_comp', 'oc_to_inf']):
                out_list.extend(['that', 'S'])
            elif check_all_restr(part, '+', 'how_extract'):
                out_list.extend(['how', 'S'])
            elif check_all_restr(part, '+', 'what_extract'):
                out_list.extend(['what', 'S'])

            elif check_all_restr(part, '+', 'for_comp'):
                out_list.extend(['for', 'NP', 'S_INF'])

            elif check_all_restr(part, '+', 'wh_inf'):
                out_list.extend(['how', 'S_INF'])
            elif check_all_restr(part, '+', 'wh_comp'):
                out_list.extend(['why', 'S'])
            elif check_all_restr(part, '+', 'what_inf'):
                out_list.extend(['what', 'S_INF'])

            elif check_all_restr(part, '+', ['sc_ing', 'ac_ing', 'poss_ing', 'be_sc_ing']):
                out_list.append('S_ING')
            elif check_all_restr(part, '+', ['rs_to_inf', 'vc_to_inf', 'sc_to_inf']):
                out_list.append('S_INF')

            elif check_all_restr(part, '+', ['plural', 'genitive']):
                out_list.append('NP')
            else:
                synrestr = part.find('SYNRESTRS/SYNRESTR')
                if synrestr is not None:
                    print('WHATIS {}{}'.format(synrestr.get('Value'), synrestr.get('type')))
                out_list.append('NP')

        elif part.tag == 'VERB':
            out_list.append('V')
        elif part.tag == 'ADV':
            out_list.append('ADV')
        elif part.tag == 'LEX' and (i == len(syntax) - 1 or syntax[i+1].tag != 'NP'):
            if part.get('value') in ['it', 'there']:
                out_list.append(part.get('value').title())
            else:
                out_list.append(part.get('value'))
        elif part.tag == 'PREP' or part.tag == 'LEX':
            next_part = syntax[i+1]
            assert next_part.tag == 'NP'
            if check_all_restr(next_part, '+', ['sc_ing']):
                out_list.extend(['PP', 'S_ING'])
            elif check_all_restr(next_part, '+', ['oc_ing', 'ac_ing']):
                out_list.append('S_ING')
            elif part.tag == 'LEX' and check_all_restr(next_part, '+', 'adj'):
                out_list.append(part.get('value'))
                out_list.append('ADJ')
            elif part.tag == 'LEX' and (check_all_restr(next_part, '-', 'sentential') or check_all_restr(next_part, '+', 'small_clause')):
                out_list.append(part.get('value'))
                out_list.append('NP')
            else:
                out_list.append('PP')
            i += 1

        i += 1

    return ' '.join(out_list)

class VerbnetGuessTest(unittest.TestCase):
    def test(self):
        skips = [
            'Eggs and cream mix well together.',
            'The eggs and the cream mixed together.'
        ]
        warnings.simplefilter("ignore", ResourceWarning)
        classid_list = sorted(verbnet.classids(), key=lambda c: LooseVersion(classid_to_number(c)))

        i = 0
        for classid in classid_list:
            for vn_frame in verbnet.frames(classid):
                text = vn_frame['frame'].find('EXAMPLES/EXAMPLE').text
                with self.subTest(i=i, msg='{}: {}'.format(classid, text)):
                    if text in skips:
                        continue
                    syntax = vn_frame['frame'].find('SYNTAX')
                    wanted_primary = strip_roles(vn_frame['frame'].find('DESCRIPTION').get('primary'))
                    converted_primary = syntax_to_primary(syntax)

                    self.assertEqual(wanted_primary, converted_primary)
                i += 1

        print('Total : {}'.format(i))
