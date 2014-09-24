#!/usr/bin/env python3
"""
Provides a mapping from exotic source names to unified ones. The goal is to
separate sentences coming from the same source. Also provides tools to maintain
that mapping.
"""

import sys
from xml.etree import ElementTree as ET
from collections import Counter

def get_xmlns(dico_file):
    DICOENVIRO_XMLNS = 'http://olst.ling.umontreal.ca/dicoenviro/'
    DICOINFO_XMLNS = 'http://olst.ling.umontreal.ca/dicoinfo/'

    if 'info' in dico_file:
        return DICOINFO_XMLNS
    elif 'enviro' in dico_file:
        return DICOENVIRO_XMLNS
    else:
        raise Exception('Unknown file {}'.format(dico_file))

def merged_source(dico, source):
    if 'enviro' in dico: 
        if source.startswith('CHANG_') or source.startswith('CHANG '):
            source = source[6:]

        if 'IPCC' in source:
            return 'IPCC'
        elif 'CANADA' in source:
            return 'CANADA'
        elif 'EUROPA' in source:
            return 'EUROPA'

        if 'CLICHE' in source:
            return 'CLICHE'
        elif 'AOMGMR' in source:
            return 'AOMGMR'
        elif 'INSU' in source:
            return 'INSU'
        elif 'MEDDEFR' in source:
            return 'MEDD'
        elif 'BOURQUE' in source:
            return 'BOURQUE'

    return source

if __name__ == '__main__':
    dico_file = sys.argv[1]
    dicoxml = ET.ElementTree(file=dico_file)
    xmlns = get_xmlns(dico_file)

    source_count = Counter()
    for contexte in dicoxml.findall('lexie/contextes/{{{0}}}contexte'.format(xmlns)):
        source_count[unified_source(dico_file, contexte.get('source'))] += 1

    for source in source_count.most_common():
        print(source)
