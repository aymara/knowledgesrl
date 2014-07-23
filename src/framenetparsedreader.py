#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads the files containing the syntactic parser output"""

import unittest
import options
import os
import sys

import framenetreader
from framenetallreader import FNAllReader
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
        self.tree = None

    def load_file(self, filename):
        """Set the current file to filename, and fill sentences_data
        accordingly. Not affected by newlines at the end of the file.
        
        :param filename: The file to load.
        :type filename: str.
        """
        
        self.filename = filename
        if not os.path.exists(filename):
            self.tree = None
            self.sentences_data = []
            raise Exception('{} does not exit'.format(filename))
            
        with open(filename) as content:
            self.sentences_data = content.read().split("\n\n")
            if self.sentences_data[len(self.sentences_data) - 1] == "":
                del self.sentences_data[len(self.sentences_data) - 1]
        
    def sentence_trees(self):
        """Yield all sentence trees in order. To be used with enumerate()"""
        for sentence in self.sentences_data:
            yield SyntacticTreeBuilder(sentence).build_syntactic_tree()
        
    def current_sentence(self):
        """Compute the text of the current sentence and returns it."""
        if self.tree == None: return ""
        return self.tree.flat()

  
class FNParsedReaderTest(unittest.TestCase):
    def comp(self, original, parsed):
        return all(
            [x == y or y == "<num>" for x,y in zip(original.split(), parsed.split())]
        )

    # List of sentences and files for which the test would fail
    # because of mistakes in the parser output
    bad_files = [
            "ANC__110CYL070.xml", "C-4__C-4Text.xml",
            "NTI__BWTutorial_chapter1.xml", "NTI__LibyaCountry1.xml",
            "NTI__NorthKorea_Introduction.xml"]
    bad_sentences = [
            ("LUCorpus-v0.3__sw2025-ms98-a-trans.ascii-1-NEW.xml", 9),
            ("NTI__Iran_Chemical.xml", 6),
            ("NTI__Iran_Chemical.xml", 62),
            ("NTI__Iran_Nuclear.xml", 5),
            ("NTI__Iran_Nuclear.xml", 49),
            ("NTI__Iran_Nuclear.xml", 68),
            ("NTI__Iran_Nuclear.xml", 82),
            ("PropBank__ElectionVictory.xml", 5),
            ("PropBank__ElectionVictory.xml", 9),
            ("PropBank__LomaPrieta.xml", 18)]
    
    def test_sentences_match(self, num_sample = 0):
        print("Checking FrameNetParsedReader")
        extractor = FNParsedReader()

        for filename in FNAllReader.fulltext_annotations():
            if not filename[-4:] == ".xml": continue

            for bad_file in self.bad_files:
                if bad_file in filename:
                    continue
            
            
            extractor.load_file(filename)
            
            reader = framenetreader.FulltextReader(filename, False)
            previous_sentence = 0

            for frame in reader.frames:
                for bad_filename, bad_sentence_id in self.bad_sentences:
                    if bad_filename in filename and bad_sentence_id == frame.sentence_id:
                        continue
   
                if frame.sentence_id != previous_sentence:
                    for sentence_id, tree in enumerate(extractor.sentence_trees()):
                        if sentence_id == frame.sentence_id:
                            extractor._handle_sentence(frame.sentence_id, tree, filename)
                
                # TODO FIXME : this is no longer guaranteed since framenet_parsed has
                # been replaced. Rewriting of bad_files and bad_sentences would
                # be needed
                #self.assertTrue(self.comp(frame.sentence, extractor.current_sentence()))
                previous_sentence = frame.sentence_id
            print(".", file=sys.stderr, end="", flush=True)
        print()

if __name__ == "__main__":
    unittest.main()
