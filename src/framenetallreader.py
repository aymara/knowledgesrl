#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads the files containing the syntactic parser output"""

import framenetreader
from conllreader import SyntacticTreeBuilder
import framenetreader
import unittest
import paths
import os
import sys

class FNAllReader:
    """ Reads simultaneously the fulltext corpus and framenet_parsed
    in order to add information such as passive voice detection to the
    annotated frames.
    This class will one day replace framenetparsedreader.
    
    :var annotations_path: str -- Path to framenet_parsed
    :var corpus_path: str -- Path to framenet fulltext
    :var core_args_only: boolean -- Indicates whether we want only core args
    :var keep_unannotated: boolean -- Indicates whether we want to keep frames without arg annotations
    :var frames: Frame List -- The collected frames
    """
    
    predicate_pos = ["MD", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
    be_forms = ["am", "are", "be", "been", "being", "is", "was", "were",
        "'m", "'re", "'s"]
    
    def __init__(self, corpus_path, annotation_path,
        core_args_only = False, keep_unannotated = False):
        self.annotations_path = annotation_path
        self.corpus_path = corpus_path
        self.core_args_only = core_args_only
        self.keep_unannotated = keep_unannotated
        
        self.trees = []
        self.sentences_syntax = []
        self.frames = []
        
        self.stats = {
            "files":0
        }
        
        self.handle_corpus()

    def handle_corpus(self):
        """Read the corpus and fill self.frames"""
        files = os.listdir(self.corpus_path)
        
        for filename in sorted(files):
            if not filename[-4:] == ".xml": continue
            
            print(".", file=sys.stderr, end="", flush=True)
            
            reader = framenetreader.FulltextReader(
                self.corpus_path + filename,
                core_args_only = self.core_args_only,
                keep_unannotated = self.keep_unannotated)
            
            if not self.load_syntax_file(filename): continue
            
            self.stats["files"] += 1
            
            matching_id = -1
            previous_sentence_id = -1
            for frame in reader.frames:
                if frame.sentence_id != previous_sentence_id:
                    matching_id = FNAllReader.best_match_sentence(
                        frame.sentence, self.sentences_syntax, matching_id)
                
                if matching_id == -1: continue
                
                self.handle_frame(frame, matching_id)
                
                self.frames.append(frame)
                    
                previous_sentence_id = frame.sentence_id
        print("")
    
    def load_syntax_file(self, filename):
        """Load the data of the syntax annotations files.
        Not affected by newlines at the end of the file.
        
        :param filename: The file to load.
        :type filename: str.
        :returns: boolean -- True if the file was correctly loaded, False otherwise.
        """
        self.trees, self.sentences_syntax = [], []
        
        path = self.annotations_path + filename.replace(".xml", ".conll")
        
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
        
    def handle_frame(self, frame, matching_id):
        """Add information to a frame using the syntax annotation
        
        :param frame: The frame
        :type frame: Frame
        :param matching_id: The position of the matching sentence
        :type matching_id: int
        """
        search = frame.predicate.text.split()[0]
        found = False
        for node in self.trees[matching_id]:
            if node.word == search:
                found = True
                break
        if not found:
            raise Exception("framenetparsedreader : predicate {} not found in "
                "sentence {}".format(search, self.trees[matching_id].flat()))
        
        frame.passive = FNAllReader.is_passive(node)
        frame.tree = self.trees[matching_id]
        frame.sentence_id_fn_parsed = matching_id
    
    @staticmethod
    def is_passive(node):
        """Tell whether a frame's predicate is a passive"""
        if node.pos != "VBN": return False
        if node.father == None: return False
        if node.father.pos not in FNAllReader.predicate_pos: return False
        return node.father.word.lower() in FNAllReader.be_forms
    
    @staticmethod
    def best_match_sentence(sentence, candidates, expected_position):
        best_score, best_index = -1, -1
        
        words_1 = set(sentence.split(" "))
        n = len(candidates)
        for i in range(0, n):
            index = (expected_position + i) % n
            sentence_2 = candidates[index]
            
            if sentence == sentence_2:
                return index

            words_2 = set(sentence_2.split(" "))
            score = len(words_1 & words_2) / (len(words_1) + len(words_2))
            
            if score > best_score:
                best_score, best_index = score, index
        
        if best_score > 0.3: return best_index
        return -1
    
class FNAllReaderTest(unittest.TestCase):
    def comp(self, original, parsed):
        return all(
            [x == y or y == "<num>" for x,y in zip(original.split(), parsed.split())]
        )

    def test_sentences_match(self, num_sample = 0):
        print("Checking FrameNetAllReader")
        extractor = FNAllReader(paths.FRAMENET_FULLTEXT, paths.FRAMENET_PARSED)

        frame = extractor.frames[26]
        self.assertTrue(frame.sentence == ("A few months ago "
            "you received a letter from me telling the success stories of "
            "people who got jobs with Goodwill 's help ."))
        self.assertTrue(frame.predicate.lemma == "receive")
        self.assertTrue(frame.passive == False)
        self.assertTrue(frame.tree.flat() == frame.sentence)
        
        frame = extractor.frames[40]
        self.assertTrue(frame.predicate.lemma == "use")
        self.assertTrue(frame.passive == True)

if __name__ == "__main__":
    unittest.main()
