#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
from collections import defaultdict
import random

from conllreader import SyntacticTreeBuilder, SyntacticTreeNode
import framenetreader

import pickle

class HeadWordExtractor:
    def __init__(self, path):
        self.annotations_path = path
        
        self.sentences_data = []
        self.tree = None
        
        self.word_classes = {}
        self.special_classes = {}
        self.words = set()
        
    def load_file(self, filename):
        filename = filename.replace(".xml", ".conll")
        with open(self.annotations_path + filename) as content:
            self.sentences_data = content.read().split("\n\n")
        
    def select_sentence(self, sentence_id):
        sentence = self.sentences_data[sentence_id - 1]
        self.tree = SyntacticTreeBuilder(sentence).build_syntactic_tree()
        
    def current_sentence(self):
        return self.tree.flat()
    
    def compute_word_classes(self):
        with open("temp_wordlist", "wb") as picklefile:
            pickle.dump(self.words, picklefile, 2)
        
        os.system("python2.7 wordclassesloader.py")
        
        with open("temp_wordclasses", "rb") as picklefile:
            self.word_classes.update(pickle.load(picklefile))
            
        os.system("rm temp_wordlist temp_wordclasses")
        
        self.word_classes.update(self.special_classes)
    
    def headword(self, arg_text):
        word, pos = self._get_headword(arg_text)
        
        if pos == "PP": self.special_classes[word] = "pronoun"
        elif pos == "NP": self.special_classes[word] = "proper_noun"
        else: self.words.add(word)
        
        return word
    
    def get_class(self, word):
        if word in self.word_classes:
            return self.word_classes[word]
        return "unknown"
        
    def _get_headword(self, arg_text):
        node = self.tree.closest_match_as_node(arg_text)
        return node.word
  
class HeadWordExtractorTest(unittest.TestCase):
    def comp(self, original, parsed):
        return all(
            [x == y or y == "<num>" for x,y in zip(original.split(), parsed.split())]
        )
    
    def test_classes(self):
        corpus_path = "../data/fndata-1.5/fulltext/"
        filename = "ANC__110CYL067"
        extractor = HeadWordExtractor("../data/framenet_parsed/")
        extractor.load_file(filename+".conll")

        reader = framenetreader.FulltextReader(corpus_path+filename+".xml", False)    

        for frame in reader.frames:
            extractor.select_sentence(frame.sentence_id)
            for arg in frame.args:
                extractor.headword(arg.text)

        extractor.words.add("abcde")
        extractor.compute_word_classes()
        self.assertEqual(extractor.get_class("soda"), "physical_entity.n.01")
        self.assertEqual(extractor.get_class("I"), "pronoun")
        self.assertEqual(extractor.get_class("Goodwill"), "proper_noun")
        self.assertEqual(extractor.get_class("abcde"), "unknown")
        self.assertEqual(extractor.get_class("fghij"), "unknown")

    def test_sentences_match(self):
        corpus_path = "../data/fndata-1.5/fulltext/"
        extractor = HeadWordExtractor("../data/framenet_parsed/")
        
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

        for filename in sorted(os.listdir(corpus_path)):
            if not filename[-4:] == ".xml": continue

            if filename in bad_files: continue
            
            print(filename, file=sys.stderr)
            
            extractor.load_file(filename)
            
            reader = framenetreader.FulltextReader(corpus_path+filename, False)
            previous_sentence = 0

            for frame in reader.frames:
                if (filename, frame.sentence_id) in bad_sentences: continue
   
                if frame.sentence_id != previous_sentence:
                    extractor.select_sentence(frame.sentence_id)

                self.assertTrue(self.comp(frame.sentence, extractor.current_sentence()))
                previous_sentence = frame.sentence_id
    
    def test_1(self):
        corpus_path = "../data/fndata-1.5/fulltext/"
        filename = "ANC__110CYL067"
        extractor = HeadWordExtractor("../data/framenet_parsed/")
        extractor.load_file(filename+".conll")

        reader = framenetreader.FulltextReader(corpus_path+filename+".xml", False)    

        frame = reader.frames[1]
        extractor.select_sentence(frame.sentence_id)
        self.assertTrue(extractor.headword(frame.args[0].text) == "you")
              
        frame = reader.frames[0]
        self.assertTrue(extractor.headword(frame.args[0].text) == "contribution")

if __name__ == "__main__":
    unittest.main()
