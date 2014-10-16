#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads the files containing the syntactic parser output"""

from conllreader import SyntacticTreeBuilder


class FNParsedReader:
    """A simple object that can read the syntactic parser output and
    build the corresponding syntactic trees.
    
    :var annotation_path: str -- The path to the annotated corpus.
    :var sentences_data: str List -- The parser output for each sentence in the current file.
    :var tree: SyntacticTreeNode -- The tree corresponding to the current sentence.
    """
    
    def __init__(self):
        self.sentences_data = []

    def load_file(self, filename):
        """Set the current file to filename, and fill sentences_data
        accordingly. Not affected by newlines at the end of the file.
        
        :param filename: The file to load.
        :type filename: str.
        """
        
        with open(str(filename), encoding='UTF-8') as content:
            self.sentences_data = content.read().split("\n\n")
            if self.sentences_data[len(self.sentences_data) - 1] == "":
                del self.sentences_data[len(self.sentences_data) - 1]
        
    def sentence_trees(self):
        """Yield all sentence trees in order. To be used with enumerate()"""
        for sentence_id, sentence in enumerate(self.sentences_data):
            tree_builder = SyntacticTreeBuilder(sentence)
            for tree in tree_builder.tree_list:
                yield sentence_id, tree_builder.sentence, tree
