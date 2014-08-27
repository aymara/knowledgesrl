#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Extract headwords of arguments and determine their WordNet class"""

import os
import sys
import unittest
import random
import pickle
import getopt

from nltk.corpus import wordnet as wn

from framenetparsedreader import FNParsedReader
from framenetallreader import FNAllReader
import framenetreader
import options


class HeadWordExtractor(FNParsedReader):
    """This object uses syntactic annotations to retrieve the headwords of
    arguments, and attributes them a WordNet top synset (currently called class).
    """
    
    def __init__(self):
        FNParsedReader.__init__(self)
    
    def headword(self, arg_text):
        """Returns the headword of an argument, assuming the proper sentence have
        already been selected.
        
        :param arg_text: The argument.
        :type arg_text: str.
        :returns: str -- The headword
        
        """
        if self.tree == None:
            return None
        else:
            return self.tree.closest_match_as_node(arg_text).word
        
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

        # TODO For PoS, not in WN, return PoS instead of synset
        # see commented out test

        if hypernyms[0].name() == entity_synset and len(hypernyms) > 1:
            wordclass = hypernyms[1].name()
        else:
            wordclass = hypernyms[0].name()

        return wordclass
    
    def compute_all_headwords(self, frames, vn_frames):
        """ Fills frame data with the headwords of the arguments.
        
        :param frames: The FrameNet frames as returned by a FrameNetReader.
        :type frames: FrameInstance List.
        :param vn_frames: The frames that we have to complete with headwords.
        :type vn_frames: VerbnetFrameOccurrence List.
        """
        
        for frame, vn_frame in zip(frames, vn_frames):
            self.tree = frame.tree
            
            vn_frame.headwords = [
                self.headword(x.text) for x in frame.args if x.instanciated]
  
class HeadWordExtractorTest(unittest.TestCase):
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
        extractor = HeadWordExtractor()
        extractor.load_file(options.framenet_parsed + filename+".conll")

        reader = framenetreader.FulltextReader(FNAllReader.fulltext_annotations(), False)

        for frame in reader.frames:
            extractor.select_sentence(frame.sentence_id)
            for arg in frame.args:
                extractor.headword(arg.text)

        self.assertEqual(extractor.get_class("soda"), "physical_entity.n.01")
        #self.assertEqual(extractor.get_class("i"), "pronoun")
        
        # get_class should return None for words out of WordNet
        self.assertEqual(extractor.get_class("abcde"), None)

    def sample_args(self, num_sample = 10):
        """Not a unit test. Returns a random sample of argument/node/headword to help.
        
        :param num_sample: The requested number of results
        :type num_sample: int
        :returns: (str, str, str) List -- Some examples of (arg, best_node_text, headword)
        """
        extractor = HeadWordExtractor(options.framenet_parsed)

        sample = []
        for filename in sorted(os.listdir(options.fulltext_corpus)):
            if not filename[-4:] == ".xml": continue

            if filename in self.bad_files: continue
            
            extractor.load_file(options.framenet_parsed + filename)
            
            reader = framenetreader.FulltextReader(options.fulltext_corpus+filename, False)
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
        extractor = HeadWordExtractor()
        extractor.load_file(options.framenet_parsed + filename+".conll")

        reader = framenetreader.FulltextReader(options.fulltext_corpus+filename+".xml", False)

        frame = reader.frames[1]
        extractor.select_sentence(frame.sentence_id)
        self.assertTrue(extractor.headword(frame.args[0].text) == "you")
              
        frame = reader.frames[0]
        self.assertTrue(extractor.headword(frame.args[0].text) == "contribution")

if __name__ == "__main__":
    # The -s option makes the script display some examples of results
    # or write them in a file using pickle
    cli_options = getopt.getopt(sys.argv[1:], "s:", [])
    num_sample = 0
    filename = ""
    
    for opt, value in cli_options[0]:
        if opt == "-s":
            if len(cli_options[1]) >= 1:
                filename = cli_options[1][0]
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
