#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads the files containing the syntactic parser output in CONLL format

    Defines the class ConllParsedReader

+"""

from conllreader import SyntacticTreeBuilder

import options
import logging
logger = logging.getLogger(__name__)
logger.setLevel(options.Options.loglevel)


class ConllParsedReader:
    """ Reads the syntactic parser output to  build the corresponding syntactic trees. """

    def sentence_trees(self, filename):
        """Yield all sentence trees from filename in order.

        To be used with enumerate().

        :param filename: The file to load.
        :type filename: str.
        """
        logger.debug("ConllParsedReader.sentence_trees(%s)"%filename)

        with open(str(filename), encoding='UTF-8') as content:
            sentences_data = content.read().split("\n\n")
            if sentences_data[len(sentences_data) - 1] == "":
                del sentences_data[len(sentences_data) - 1]

        for sentence_id, sentence in enumerate(sentences_data):
            tree_builder = SyntacticTreeBuilder(sentence)
            for tree in tree_builder.tree_list:
                yield sentence_id, tree_builder.sentence, tree
