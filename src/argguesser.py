#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Extract frames, predicates and arguments from a corpus, using only syntactic annotations 

    Defines the class ArgGuesser

"""

from conllparsedreader import ConllParsedReader
from framenetframe import FrameInstance, Predicate, Word, Arg
from verbnetprepclasses import all_preps
from argheuristic import find_args
import headwordextractor

import options
import logging


class ArgGuesser():
    """ 
    :var frames_for_verb: lemma -> VerbnetOfficialFrame list - Used to know
        which predicates are in VerbNet.
    :var filename: str -- The name of the current CoNLL file.

    """

    predicate_pos = [
        "VERB",  # UD
        "MD", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ",
        # French tags:
        "V", "VIMP", "VINF", "VPP", "VPR", "VS"]

    subject_deprels = [
        "LGS",  # Logical subject -> should we keep this (36 args) ?
        "SBJ", "SUB"
        # UD below
        "nsubj",
        "csubj",
    ]

    non_core_deprels = [
        "DIR", "EXT", "LOC",
        "MNR", "PRP", "PUT", "TMP",
        # UD below
        "obl",
        "vocative",
        "expl",
        "dislocated",
        "advcl",
        "advmod*",
        "discourse",
        "aux",
        "cop",
        "mark",
        "nmod",
        "appos",
        "nummod",
        "acl",
        "amod",
        "det",
        "clf",
        "case",
        "conj",
        "cc",
        "fixed",
        "flat",
        "list",
        "parataxis",
        "compound",
        "orphan",
        "goeswith",
        "reparandum",
        "punct",
        "root",
        "dep"
    ]

    args_deprels = subject_deprels + [
        "DIR",
        "BNF",   # the 'for' phrase for verbs that undergo dative shift
        "DTV",   # the 'to' phrase for verbs that undergo dative shift
        "OBJ",   # direct or indirect object or clause complement
        "OPRD",  # object complement
        "PRD",   # predicative complement
        "VMOD",
        # UD below
        "obj",
        "iobj",
        "ccomp",
        "xcomp",
    ]

    # Source : http://www.comp.leeds.ac.uk/ccalas/tagsets/upenn.html
    pos_conversions = {
        "$": "NP",
        "CD": "NP",   # Cardinal number ("The three of us")
        "DT": "NP",   # Determiner ("this" or "that")
        "JJ": "ADJ",
        "JJR": "NP",  # Comparative
        "JJS": "NP",  # Superlative
        "MD": "S",    # Modal verb
        "NOUN": "NP", 
        "NN": "NP", 
        "NNP": "NP", 
        "NNPS": "NP", 
        "NNS": "NP",
        "NP": "NP", 
        "NPS": "NP",
        "PP": "PP",
        "PRP": "NP",
        "RB": "ADV",
        "TO": "to S",
        "VERB": "S",  # Base form of a verb
        "VB": "S",  # Base form of a verb
        "VBD": "S", 
        "VBG": "S_ING",
        "VBN": "ADJ",  # Participe, as "fed" in "He got so fed up that..."
        "VBP": "S", 
        "VBZ": "S",
        "WDT": "NP",  # Relative determiners ("that what whatever which whichever")
        # French conversions
        "NC": "NP",
        "PRO": "NP",
        "V": "S",
    }

    acceptable_phrase_type = ["NP", "PP", "S_ING", "S"]

    complex_pos = ["IN", "WP"]

    def __init__(self, frames_for_verb):
        self.frames_for_verb = frames_for_verb
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(options.Options.loglevel)
        self.logger.debug(f"ArgGuesser({str(frames_for_verb)[:100]}...)")

    def frame_instances_from_file(self, filename):
        """ Extracts frames from one file and iterate over them """

        self.logger.debug(f'frame_instances_from_file {filename}')
        conllparsed_reader = ConllParsedReader()
        for sentence_id, sentence, tree in conllparsed_reader.sentence_trees(
                filename):
            self.logger.debug(
                f"frame_instances_from_file sentence {sentence_id}: "
                f"{sentence}")
            for frame in self._sentence_predicates_iterator(sentence_id, 
                                                            sentence, 
                                                            tree, 
                                                            filename):
                yield frame

    def _sentence_predicates_iterator(self, sentence_id, sentence, tree,
                                      filename):
        """ Extracts frames from one sentence and iterate over them """
        self.logger.debug(f'_sentence_predicates_iterator {sentence_id} '
                          f'sentence: {sentence}; tree: {tree}')
        for node in tree:
            # For every verb, looks for its infinitive form in VerbNet, and
            # builds a frame occurrence if it is found
            self.logger.debug(f"_sentence_predicates_iterator on {node.lemma}")
            
            if node.lemma not in self.frames_for_verb:
                self.logger.debug(f"_sentence_predicates_iterator node.lemma "
                                  f"{node.lemma} not in frames_for_verb")
                continue

            if self._is_predicate(node):
                self.logger.debug(f"_sentence_predicates_iterator node.lemma "
                                  f"{node.lemma} is a predicate")
                predicate = Predicate(
                    node.begin_word, 
                    node.begin_word + len(node.word) - 1,
                    node.word, 
                    node.lemma,
                    node.word_id)

                if options.Options.heuristic_rules:
                    args = [self._nodeToArg(x, node) for x in find_args(node)]
                else:
                    args = self._find_args(node)

                args = [x for x in args if self._is_good_phrase_type(x.phrase_type)]

                # Read headwords
                headwords = [None] * len(args)
                for i, arg in enumerate(args):
                    if not arg.instanciated:
                        continue
                    headwords[i] = headwordextractor.headword(arg, tree)

                self.logger.debug('_sentence_predicates_iterator yielding {} {}…'.format(predicate, args))
                yield FrameInstance(
                    sentence=sentence,
                    predicate=predicate,
                    args=args,
                    words=[Word(x.begin, x.end, x.pos) for x in tree],
                    frame_name="",
                    sentence_id=sentence_id,
                    filename=filename,
                    tree=tree,
                    headwords=headwords
                )

    def _is_good_phrase_type(self, phrase_type):
        """ Tells whether a phrase type is acceptable for an argument """
        # If it contains a space, it has been assigned by _get_phrase_type
        if " " in phrase_type:
            return True

        return phrase_type in self.acceptable_phrase_type

    def _find_args(self, node):
        """Returns every arguments of a given node.

        :param node: The node for which descendants are susceptible to be returned.
        :type node: SyntacticTreeNode.
        :returns: Arg List -- The resulting list of arguments.

        """
        self.logger.debug("_find_args")
        base_node = node
        while base_node.deprel in ["VC", "CONJ", "COORD"]:
            base_node = base_node.father

        result = self._find_args_rec(node, node)
        if base_node is not node and base_node.pos in self.predicate_pos:
            result += self._find_args_rec(base_node, base_node)

        result = [x for x in result if x.text != "to"]

        return result

    def _find_args_rec(self, predicate_node, node):
        """Returns every arguments of a given node that is a descendant of another node.
        It is possible that one of the returned arguments corresponds
        to the second node itself.

        :param predicate_node: The node of which we want to obtain arguments.
        :type predicate_node: SyntacticTreeNode.
        :param node: The node for which descendants are susceptible to be returned.
        :type node: SyntacticTreeNode.
        :returns: Arg List -- The resulting list of arguments.

        """
        result = []
        for child in node.children:
            if self._is_arg(child, predicate_node):
                result.append(self._nodeToArg(child, predicate_node))
            elif child.pos not in self.predicate_pos:
                result += self._find_args_rec(predicate_node, child)
        return result

    def _overlap(self, node1, node2):
        return (node1.begin <= node2.begin_word + len(node2.word) - 1 and
                node1.end >= node2.begin_word)

    def _same_side(self, node, child, predicate):
        if node.begin_word < predicate.begin_word:
            return child.end < predicate.begin_word
        return child.begin > predicate.begin_word

    def _nodeToArg(self, node, predicate):
        """ Builds an Arg using the data of a node. """

        # Prevent arguments from overlapping over the predicate
        begin, end = node.begin, node.end
        text = node.flat()

        if self._overlap(node, predicate):
            begin, end = node.begin_word, node.begin_word + len(node.word) - 1
            for child in node.children:
                if self._same_side(node, child, predicate):
                    begin, end = min(begin, child.begin), max(end, child.end)
            root = node
            while root.father is not None:
                root = root.father
            text = root.flat()[begin:end+1]

        return Arg(
            position=node.word_id,
            begin=begin,
            end=end,
            text=text,
            # If the argument isn't continuous, text will not be
            # a substring of frame.sentence
            role="",
            instanciated=True,
            phrase_type=self._get_phrase_type(node),
            annotated=False)

    def _get_phrase_type(self, node):
        # IN = Preposition or subordinating conjunction
        if node.pos == "IN":
            if node.word.lower() in all_preps:
                return "PP"
            return "S"
        # WP = Wh-pronoun
        if node.pos == "WP":
            return node.word.lower()+" S"

        if node.pos in self.pos_conversions:
            return self.pos_conversions[node.pos]
        return node.pos

    def _is_predicate(self, node):
        """Tells whether a node can be used as a predicate for a frame"""
        # Check part-of-speech compatibility
        if node.pos not in self.predicate_pos:
            self.logger.debug(f"_is_predicate {node.lemma} is a possible "
                              f"predicate but not its PoS {node.pos}")
            return False

        # Check that this node is not an auxiliary
        if node.lemma in ["be", "do", "have", "will", "would"]:
            for child in node.children:
                if child.pos in self.predicate_pos and child.deprel == "VC":
                    return False
        return True

    def _is_subject(self, node, predicate_node):
        """Tells whether node is the subject of predicate_node. This is only called
        when node is a brother of predicate_node.
        """
        return ((node is not predicate_node) and
                node.deprel in self.subject_deprels)

    def _is_arg(self, node, predicate_node):
        """Tells whether node is an argument of predicate_node. This is only called
        when node is a descendant of predicate_node.
        """
        self.logger.debug("_is_arg {}: {}".format(node.deprel, (node is not predicate_node) and
                                             node.deprel in self.args_deprels))
        return ((node is not predicate_node) and
                node.deprel in self.args_deprels)
