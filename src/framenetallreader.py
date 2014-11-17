#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads the files containing the syntactic parser output"""

import framenetreader
from conllreader import SyntacticTreeBuilder
import headwordextractor


class PredicateNotFound(Exception):
    pass


class FNAllReader:
    """ Reads simultaneously the fulltext corpus and framenet_parsed
    in order to add information such as passive voice detection to the
    annotated frames.
    This class will one day replace framenetparsedreader.

    :var annotations_path: str -- Path to framenet_parsed
    :var add_non_core_args: boolean -- Indicates whether we also want non-core args
    :var keep_unannotated: boolean -- Indicates whether we want to keep frames without arg annotations
    :var frames: FrameInstance List -- The collected frames
    """

    predicate_pos = ["MD", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
    be_forms = ["am", "are", "be", "been", "being", "is", "was", "were",
        "'m", "'re", "'s"]

    def __init__(self, add_non_core_args=True, keep_unannotated=False):
        self.add_non_core_args = add_non_core_args
        self.keep_unannotated = keep_unannotated

        self.stats = {
            "files": 0
        }

    def iter_frames(self, annotation_file, parse_file):
        """Read the corpus and yield every valid frame"""

        self.stats["files"] += 1
        tree_dict = self.read_syntactic_parses(parse_file)

        reader = framenetreader.FulltextReader(
            annotation_file,
            add_non_core_args=self.add_non_core_args,
            keep_unannotated=self.keep_unannotated,
            tree_dict=tree_dict)

        for frame_instance in reader.frames:
            try:
                sentence_tree_list = tree_dict[frame_instance.sentence_id]
                self.add_syntactic_information(frame_instance, sentence_tree_list[0])
                yield frame_instance
            except PredicateNotFound:
                pass

    def read_syntactic_parses(self, parse_filename):
        """Load the syntactic annotations files.
        Not affected by newlines at the end of the file.

        :param parse_filename: The FrameNet filepath, eg. path/to/ANC__110CYL072.conll
        :type filename: str.
        :returns: list of trees
        """
        with open(str(parse_filename), encoding='UTF-8') as content:
            sentences_data = content.read().split("\n\n")
            if sentences_data[-1] == "":
                del sentences_data[-1]

        tree_dict = {}
        for sentence_id, one_sentence_data in enumerate(sentences_data):
            tree_dict[sentence_id] = SyntacticTreeBuilder(one_sentence_data).tree_list

        return tree_dict

    def add_syntactic_information(self, frame, sentence_tree):
        """
        Add information to a frame using the syntactic annotation: whether it is
        passive or not, and whether the predicate has been found in the tree.

        In some cases (five for the training set), our parser produces
        multiple roots, which mean the resulting tree could only cover one
        part of the sentence.

        In those cases, the function returns False and the frame is not handled
        by our labeler.

        :param frame: The frame
        :type frame: FrameInstance
        """

        # Search verb + passive status
        try:
            search = frame.predicate.text.split()[0].lower()
            predicate_node = [node for node in frame.tree if node.word == search][0]
            frame.passive = FNAllReader.is_passive(predicate_node)
        except IndexError:
            raise PredicateNotFound("\nframenetparsedreader : predicate \"{}\" not found in "
                "sentence {}".format(search, frame.tree.flat()))

        # Read headwords
        for i, arg in enumerate(frame.args):
            if not arg.instanciated:
                continue
            frame.headwords[i] = headwordextractor.headword(arg, sentence_tree)

    @staticmethod
    def is_passive(node):
        """Tell whether a frame's predicate is a passive"""
        if node.pos != "VBN":
            return False
        elif node.father is None:
            return False
        elif node.father.pos not in FNAllReader.predicate_pos:
            return False
        else:
            return node.father.word.lower() in FNAllReader.be_forms
