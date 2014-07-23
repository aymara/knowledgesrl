#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads the files containing the syntactic parser output"""

import unittest
import options
import os

import framenetreader
from conllreader import SyntacticTreeBuilder


class FNAllReader:
    """ Reads simultaneously the fulltext corpus and framenet_parsed
    in order to add information such as passive voice detection to the
    annotated frames.
    This class will one day replace framenetparsedreader.
    
    :var annotations_path: str -- Path to framenet_parsed
    :var corpus_path: str -- Path to framenet fulltext
    :var core_args_only: boolean -- Indicates whether we want only core args
    :var keep_unannotated: boolean -- Indicates whether we want to keep frames without arg annotations
    :var frames: FrameInstance List -- The collected frames
    """
    
    predicate_pos = ["MD", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
    be_forms = ["am", "are", "be", "been", "being", "is", "was", "were",
        "'m", "'re", "'s"]
    
    def __init__(self, corpus_path, annotation_path,
        core_args_only = False, keep_unannotated = False, filename=None):
        self.annotations_path = annotation_path
        self.corpus_path = corpus_path
        self.core_args_only = core_args_only
        self.keep_unannotated = keep_unannotated
        
        self.trees = []
        self.sentences_syntax = []
        self.filename = filename
        
        self.stats = {
            "files":0
        }
    
    def iter_frames(self):
        """Read the corpus and yield every valid frame"""
        
        if self.filename == None:
            files = os.listdir(self.corpus_path)
        else:
            files = [self.filename.replace(".conll", ".xml")]
        
        for filename in sorted(files):
            if not filename[-4:] == ".xml": continue
            
            print(".", file=sys.stderr, end="", flush=True)
            
            self.load_syntactic_parses(filename[:-4])
            
            self.stats["files"] += 1
            
            reader = framenetreader.FulltextReader(
                self.corpus_path + filename,
                core_args_only = self.core_args_only,
                keep_unannotated = self.keep_unannotated,
                trees = self.trees)
            
            for frame_instance in reader.frames:
                if self.add_syntactic_information(frame_instance):
                    yield frame_instance
    
    def load_syntactic_parses(self, filename):
        """Load the syntactic annotations files.
        Not affected by newlines at the end of the file.
        
        :param filename: The FrameNet file name, eg. ANC__110CYL072
        :type filename: str.
        :returns: boolean -- True if the file was correctly loaded, False otherwise.
        """
        self.trees, self.sentences_syntax = [], []
        
        path = self.annotations_path + filename + ".conll"
        
        if not os.path.exists(path):
            return False
            
        with open(path) as content:
            sentences_data = content.read().split("\n\n")
            if sentences_data[-1] == "": del sentences_data[-1]

        for one_sentence_data in sentences_data:
            tree = SyntacticTreeBuilder(one_sentence_data).build_syntactic_tree()
            self.trees.append(tree)
            self.sentences_syntax.append(tree.flat())
            
        return True
        
    def add_syntactic_information(self, frame):
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
        
        search = frame.predicate.text.split()[0].lower()
        found = False
        for node in frame.tree:
            if node.word == search:
                found = True
                predicate_node = node
                break

        if not found:
            #print("\nframenetparsedreader : predicate \"{}\" not found in "
            #    "sentence {}".format(search, frame.tree.flat()))
            return False
        
        frame.passive = FNAllReader.is_passive(predicate_node)
        frame.sentence_id_fn_parsed = 0
        
        return True
    
    @staticmethod
    def is_passive(node):
        """Tell whether a frame's predicate is a passive"""
        if node.pos != "VBN": return False
        if node.father == None: return False
        if node.father.pos not in FNAllReader.predicate_pos: return False
        return node.father.word.lower() in FNAllReader.be_forms
    
class FNAllReaderTest(unittest.TestCase):
    def comp(self, original, parsed):
        return all(
            [x == y or y == "<num>" for x,y in zip(original.split(), parsed.split())]
        )

    def test_sentences_match(self, num_sample = 0):
        print("Checking FrameNetAllReader")
        extractor = FNAllReader(options.fulltext_corpus, options.framenet_parsed)

        frames = [x for x in extractor.iter_frames()]
        frame = frames[28]
        self.assertTrue(frame.sentence == ("a few months ago "
            "you received a letter from me telling the success stories of "
            "people who got jobs with goodwill 's help ."))
        self.assertTrue(frame.predicate.lemma == "receive")
        self.assertTrue(frame.passive == False)
        self.assertTrue(frame.tree.flat() == frame.sentence)
        
        frame = frames[42]
        self.assertTrue(frame.predicate.lemma == "use")
        self.assertTrue(frame.passive == True)

if __name__ == "__main__":
    unittest.main()
