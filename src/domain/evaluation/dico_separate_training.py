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

for dico in paths.DICOS:
    filename = os.path.join(dico['root'], dico['xml'])
    xmlns = dico['xmlns']
    dicoxml = ET.ElementTree(file=filename)
    sources = defaultdict(list)
    source_count = Counter()

    for contexte in dicoxml.findall('lexie/contextes/{{{0}}}contexte'.format(xmlns)):
        source = contexte.get('source')
        indented_sentence_text = contexte.find('{{{0}}}contexte-texte'.format(xmlns)).text
        text_hash = sha256(deindent_text(indented_sentence_text).encode('utf-8')).hexdigest()
        sources[source].append(text_hash)
        source_count[source] += 1

    train, test = [], []
    for source, count in source_count.most_common():
        if len(train) >= len(test):
            test.extend(sources[source])
        else:
            train.extend(sources[source])

    domain_dir = 'enviro' if 'enviro' in dico['name'] else 'info'
    print(len(train), len(test))
    pickle.dump(train, open('../data/domain/{}/train_{}.pickle'.format(domain_dir, dico['name']), 'wb'))
    pickle.dump(test, open('../data/domain/{}/test_{}.pickle'.format(domain_dir, dico['name']), 'wb'))
    print('Dumped {}.'.format(dico['name']))
