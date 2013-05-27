#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
from collections import defaultdict
import random
import pickle
import getopt

from conllreader import SyntacticTreeBuilder, SyntacticTreeNode
from framenetparsedreader import FNParsedReader
import framenetreader
import paths

class HeadWordExtractor(FNParsedReader):
    def __init__(self, path):
        FNParsedReader.__init__(self, path)
        self.word_classes = {}
        self.special_classes = {}
        self.words = set()
    
    def compute_word_classes(self):
        with open("temp_wordlist", "wb") as picklefile:
            pickle.dump(self.words, picklefile, 2)
        
        os.system("python2.7 wordclassesloader.py")
        
        with open("temp_wordclasses", "rb") as picklefile:
            self.word_classes.update(pickle.load(picklefile))
            
        os.system("rm temp_wordlist temp_wordclasses")
        
        self.word_classes.update(self.special_classes)
    
    def headword(self, arg_text):
        if self.tree == None: return ""
        
        word, pos = self._get_headword(arg_text)
        
        if pos == "PP": self.special_classes[word] = "pronoun"
        elif pos == "NP": self.special_classes[word] = "proper_noun"
        else: self.words.add(word)
        
        return word
        
    def best_node(self, arg_text):
        if self.tree == None: return None
        return self.tree.closest_match_as_node(arg_text)

    def get_class(self, word):
        if word in self.word_classes:
            return self.word_classes[word]
        return "unknown"
    
    def compute_all_headwords(self, frames, vn_frames):
        old_filename = ""
        previous_sentence = 0
        for frame, vn_frame in zip(frames, vn_frames):
            if old_filename != frame.filename:
                self.load_file(frame.filename)
                self.select_sentence(frame.sentence_id)
            elif frame.sentence_id != previous_sentence:
                self.select_sentence(frame.sentence_id)

            vn_frame.headwords = [  
                self.headword(x.text) for x in frame.args if x.instanciated]    
            
            old_filename = frame.filename
            previous_sentence = frame.sentence_id
        
    def _get_headword(self, arg_text):
        node = self.tree.closest_match_as_node(arg_text)
        return node.word, node.pos
  
class HeadWordExtractorTest(unittest.TestCase):
    def comp(self, original, parsed):
        return all(
            [x == y or y == "<num>" for x,y in zip(original.split(), parsed.split())]
        )
        
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
            
    def test_classes(self):
        filename = "ANC__110CYL067"
        extractor = HeadWordExtractor(paths.FRAMENET_PARSED)
        extractor.load_file(filename+".conll")

        reader = framenetreader.FulltextReader(paths.FRAMENET_FULLTEXT+filename+".xml", False)    

        for frame in reader.frames:
            extractor.select_sentence(frame.sentence_id)
            for arg in frame.args:
                extractor.headword(arg.text)

        extractor.words.add("abcde")
        extractor.compute_word_classes()
        self.assertEqual(extractor.get_class("soda"), "physical_entity.n.01")
        self.assertEqual(extractor.get_class("I"), "pronoun")
        self.assertEqual(extractor.get_class("abcde"), "unknown")
        self.assertEqual(extractor.get_class("fghij"), "unknown")

    def sample_args(self, num_sample = 0):
        extractor = HeadWordExtractor(paths.FRAMENET_PARSED)

        sample = []
        for filename in sorted(os.listdir(paths.FRAMENET_FULLTEXT)):
            if not filename[-4:] == ".xml": continue

            if filename in self.bad_files: continue
            
            print(filename, file=sys.stderr)
            
            extractor.load_file(filename)
            
            reader = framenetreader.FulltextReader(paths.FRAMENET_FULLTEXT+filename, False)
            previous_sentence = 0

            for frame in reader.frames:
                if (filename, frame.sentence_id) in self.bad_sentences: continue
   
                if frame.sentence_id != previous_sentence:
                    extractor.select_sentence(frame.sentence_id)
                
                for arg in frame.args:
                    if not arg.instanciated: continue
                    node = extractor.best_node(arg.text)
                    sample.append((arg.text, node.flat(), node.word))
                
                previous_sentence = frame.sentence_id
                
        random.shuffle(sample)
        return sample[0:num_sample]
    
    def test_1(self):
        filename = "ANC__110CYL067"
        extractor = HeadWordExtractor(paths.FRAMENET_PARSED)
        extractor.load_file(filename+".conll")

        reader = framenetreader.FulltextReader(paths.FRAMENET_FULLTEXT+filename+".xml", False)    

        frame = reader.frames[1]
        extractor.select_sentence(frame.sentence_id)
        self.assertTrue(extractor.headword(frame.args[0].text) == "you")
              
        frame = reader.frames[0]
        self.assertTrue(extractor.headword(frame.args[0].text) == "contribution")

if __name__ == "__main__":
    options = getopt.getopt(sys.argv[1:], "s:", [])
    num_sample = 0
    filename = ""

    for opt, value in options[0]:
        if opt == "-s": 
            if len(options[1]) >= 1:
                filename = options[1][0]
            num_sample = int(value)
        
    if num_sample > 0:
        tester = HeadWordExtractorTest()
        result = tester.sample_args(num_sample)
        if filename == "":
            for exemple in result:
                print("{}\n{}\n{}\n".format(exemple[0], exemple[1], exemple[2]))
        else:
            with open(filename, "wb") as picklefile:
                pickle.dump(result, picklefile)
    else:
        unittest.main()
