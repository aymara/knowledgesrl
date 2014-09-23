#!/usr/bin/env python3
"""
Separates training and test set based on source distribution
"""

import os.path
import sys
from hashlib import sha256
from xml.etree import ElementTree as ET
from collections import defaultdict, Counter
import pickle

import paths
from domain.dicoxml import deindent_text
from unifysources import unified_source

if __name__ == '__main__':
    for dico in paths.DICOS:
        filename = os.path.join(dico['root'], dico['xml'])
        xmlns = dico['xmlns']
        dicoxml = ET.ElementTree(file=filename)
        sources = defaultdict(list)
        source_count = Counter()

        for contexte in dicoxml.findall('lexie/contextes/{{{0}}}contexte'.format(xmlns)):
            source = unified_source(dico['xml'], contexte.get('source'))
            sentence_text = deindent_text(contexte.find('{{{0}}}contexte-texte'.format(xmlns)).text)
            sources[source].append(sentence_text)
            source_count[source] += 1

        train, test = [], []
        for source, count in source_count.most_common():
            if len(train) >= len(test):
                to_extend = test
            else:
                to_extend = train

            for sentence_text in sources[source]:
                to_extend.append((source, sentence_text))

        domain_dir = 'enviro' if 'enviro' in dico['name'] else 'info'
        pickle.dump(train, open('../data/domain/{}/train_{}.pickle'.format(domain_dir, dico['name']), 'wb'))
        pickle.dump(test, open('../data/domain/{}/test_{}.pickle'.format(domain_dir, dico['name']), 'wb'))
        print('Dumped {}.'.format(dico['name']))
