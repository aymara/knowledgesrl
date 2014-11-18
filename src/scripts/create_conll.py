#!/usr/bin/env python3

""""Create a CoNLL corpus from FrameNet fulltext data tokens

This CoNLL corpus will then be lemmatized using WordNet, and parsed using
TurboParser.
"""

from pathlib import Path
from xml.etree import ElementTree as ET
import os

from nltk.corpus import wordnet

from paths import FRAMENET_FULLTEXT

xmlns = 'http://framenet.icsi.berkeley.edu'
conll_dir = Path(FRAMENET_FULLTEXT).parents[1] / 'framenet_turpobarsed'

os.makedirs(str(conll_dir), exist_ok=True)

for fulltext_filename in Path(FRAMENET_FULLTEXT).glob('*.xml'):
    fulltext_xml = ET.ElementTree(file=str(fulltext_filename))
    conll_file = open(str(conll_dir / (fulltext_filename.stem + '.conll')), 'w')

    for sentence in fulltext_xml.findall('{{{}}}sentence'.format(xmlns)):
        word_id = 1
        sentence_text = sentence.find('{{{}}}text'.format(xmlns)).text
        for word_label in sentence.findall('{{{0}}}annotationSet/{{{0}}}layer[@name="PENN"]/{{{0}}}label'.format(xmlns)):
            start = int(word_label.get('start'))
            end = int(word_label.get('end'))
            word = sentence_text[start:end+1]

            morphy_lemma = wordnet.morphy(word.lower())
            lemma = morphy_lemma if morphy_lemma is not None else word

            print('\t'.join([str(word_id), word, lemma] + ['_'] * 7), file=conll_file)
            word_id += 1
        print(file=conll_file)

print('Wrote files in {}'.format(str(conll_dir)))
