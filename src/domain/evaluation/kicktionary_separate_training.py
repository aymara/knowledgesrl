#!/usr/bin/env python3
"""
Separates training and test set based on source distribution
"""

from hashlib import sha256
from xml.etree import ElementTree as ET
from collections import defaultdict, Counter
import pickle
import random

import paths
from domain import kicktionary

all_lus = ET.ElementTree(file=paths.ALL_LUS)

% TODO french
for lang in ['en']:
    hashes = pickle.load(open('hashes_{}.pickle'.format(lang), 'rb'))
    sentences = defaultdict(list)
    for lu_report in all_lus.findall('LU_REPORT'):
        lu = lu_report.find('LEXICAL-UNIT')

        # Skip uninteresting frames
        if lu.get('lang') != lang:
            continue
        elif not lu.get('lu-id').endswith('.v'):
            continue
        
        frame = lu.get('frame')
        for example in lu_report.findall('EXAMPLE'):
            sentence_text = kicktionary.text_from_example(example)
            text_hash = sha256(sentence_text.encode('utf-8')).hexdigest()
            print(sentence_text)
            print(hashes[text_hash])
            sentences[frame].append(text_hash)

    train, test = [], []
    for frame in sentences:
        frame_sentences = sentences[frame]
        random.shuffle(frame_sentences)
        smaller_split = frame_sentences[0:len(frame_sentences)//2]
        longer_split = frame_sentences[len(frame_sentences)//2:len(frame_sentences)]
        if len(train) >= len(test):
            test.extend(longer_split)
            train.extend(smaller_split)
        else:
            test.extend(longer_split)
            train.extend(longer_split)

    print(len(train), len(test))
    pickle.dump(train, open('../data/domain/kicktionary/train_kicktionary_{}.pickle'.format(lang), 'wb'))
    pickle.dump(test, open('../data/domain/kicktionary/test_kicktionary_{}.pickle'.format(lang), 'wb'))
    print('Dumped kicktionary_{}'.format(lang))
