#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Extract headwords of arguments and determine their WordNet class"""

from nltk.corpus import wordnet as wn


def headword(arg, tree):
    """Returns the headword of an argument, assuming the proper sentence has
    already been selected.

    :param arg: The argument.
    :type arg: Arg.
    :returns: str -- The headword

    """
    headword_node = tree.closest_match_as_node(arg)
    return headword_node.word

    # If another word points to headword with relation PMOD, then we want to
    # choose that word instead: the child of the preposition that is the root
    # of the PP.
    for child in headword_node.children:
        if child.deprel == 'PMOD':
            pass
            #return child.word

    return headword_node.word


def get_class(word):
    """Looks for the WordNet class of a word and returns it.

    :param word: The word
    :type word: str.
    :returns: str -- The class of the word or None if it was not found
    """
    # The class of a word is the highest hypernym, except
    # when this is "entity". In this case, we take the second
    # highest hypernym
    entity_synset = "entity.n.01"

    synsets = wn.synsets(word)
    if not synsets:
        return None

    # Since WSD is complicated, we choose the first synset.
    synset = synsets[0]
    # We also choose the first hypernymy path: even when there are two
    # paths, the top synset is very likely to be the same anyway
    hypernyms = synset.hypernym_paths()[0]

    # TODO For PoS not in WN, return PoS instead of synset
    # (see commented out test)

    if hypernyms[0].name() == entity_synset and len(hypernyms) > 1:
        wordclass = hypernyms[1].name()
    else:
        wordclass = hypernyms[0].name()

    return wordclass
