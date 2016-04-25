#!/usr/bin/env python3
"""
Separates training and test set based on source distribution
"""

from xml.etree import ElementTree as ET
from collections import defaultdict
import json

import paths
from domain import kicktionary
from domain.dicoxml import deindent_text
from .mergesource import merged_source


def split_sources(sentences):
    sentences_for_source = defaultdict(list)
    for source, sentence_text in sentences:
        sentences_for_source[source].append(sentence_text)

    most_common_sources = sorted(sentences_for_source.keys(),
        key=lambda s: (len(sentences_for_source[s]), s), reverse=True)

    train, test = [], []
    for source in most_common_sources:
        if len(train) >= len(test):
            to_extend = test
        else:
            to_extend = train

        for sentence_text in sentences_for_source[source]:
            to_extend.append((source, sentence_text))

    return train, test


def dico_split():
    for dico in paths.Paths.DICOS:
        xmlns = dico['xmlns']
        dicoxml = ET.ElementTree(file=str(dico['xml']))

        sentences = []
        for contexte in dicoxml.findall('lexie/contextes/{{{0}}}contexte'.format(xmlns)):
            source = merged_source(dico['name'], contexte.get('source'))
            sentence_text = deindent_text(contexte.find('{{{0}}}contexte-texte'.format(xmlns)).text)
            sentences.append((source, sentence_text))

        train, test = split_sources(sentences)

        domain_dir = 'enviro' if 'enviro' in dico['name'] else 'info'
        json.dump(
            train,
            open('../data/domain/{}/train_{}.json'.format(domain_dir, dico['name']), 'w'),
            indent=4, ensure_ascii=False)
        json.dump(
            test,
            open('../data/domain/{}/test_{}.json'.format(domain_dir, dico['name']), 'w'),
            indent=4, ensure_ascii=False)

        print('Dumped {} ({}/{}).'.format(dico['name'], len(train), len(test)))


def kicktionary_split():
    all_lus = ET.ElementTree(file=str(paths.Paths.ALL_LUS))

    sentences_sources = {
        "Sychev's back-heel released the speedy winger, who skipped past a defender before feeding Izmailov, whose shot deflected off Urmas Rooba and in.": '75239',
        "The midfield player broke free, fed Nielson on the right, then brilliantly volleyed his return cross into the net.": '79560',
        'Peter Simek, who had been booked five minutes earlier for a foul on Marko Babic, was substituted shortly afterwards and Croatia took control.': '75387',
        'Rosický created the opener seven minutes in as he rounded his marker and crossed from the by-line for Milan Baroš - marked by fellow Liverpool FC player Sami Hyypiä - to turn in.': '75157'}

    for lang in ['en', 'fr']:

        sentences = []
        for frame, lemma, example, sentence_text in kicktionary.lang_examples(all_lus, lang=lang):
            source = example.get('source-text-id')
            if source is None:
                source = sentences_sources.get(sentence_text, '__UNKNOWN_SOURCE__')
            sentences.append((source, sentence_text))

        train, test = split_sources(sentences)

        with open('../data/domain/kicktionary/train_kicktionary_{}.json'.format(lang), 'w') as fp:
            json.dump(train, fp, indent=4, ensure_ascii=False)
        with open('../data/domain/kicktionary/test_kicktionary_{}.json'.format(lang), 'w') as fp:
            json.dump(test, fp, indent=4, ensure_ascii=False)
        print('Dumped kicktionary_{} ({}/{})'.format(lang, len(train), len(test)))

if __name__ == '__main__':
    dico_split()
    kicktionary_split()
