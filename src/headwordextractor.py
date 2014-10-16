#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Extract headwords of arguments and determine their WordNet class"""

from nltk.corpus import wordnet as wn

from framenetparsedreader import FNParsedReader


class HeadWordExtractor(FNParsedReader):
    """This object uses syntactic annotations to retrieve the headwords of
    arguments, and attributes them a WordNet top synset (currently called class).
    """
    
    def __init__(self):
        FNParsedReader.__init__(self)
    
    def headword(self, arg_text, tree):
        """Returns the headword of an argument, assuming the proper sentence have
        already been selected.
        
        :param arg_text: The argument.
        :type arg_text: str.
        :returns: str -- The headword
        
        """
        return tree.closest_match_as_node(arg_text).word
        
    def best_node(self, arg_text):
        """Looks for the closest match of an argument in the syntactic tree.
        This method is only here for debug purposes.
        
        :param arg_text: The argument.
        :type arg_text: str.
        :returns: SyntacticTreeNode -- The nodes which contents match arg_text the best
        
        """
        if self.tree == None: return None
        return self.tree.closest_match_as_node(arg_text)

    def get_class(self, word):
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
        # paths, the top synset is very likely to be the same
        hypernyms = synset.hypernym_paths()[0]

        # TODO For PoS not in WN, return PoS instead of synset
        # (see commented out test)

        if hypernyms[0].name() == entity_synset and len(hypernyms) > 1:
            wordclass = hypernyms[1].name()
        else:
            wordclass = hypernyms[0].name()

        return wordclass
