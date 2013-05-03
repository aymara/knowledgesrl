#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Match Frame to appropriate VerbNet structures"""

from framestructure import *
import unittest
import sys

class EmptyFrameError(Exception):
    """Trying to use an empty frame in a FrameMatcher
    
    :var frame: VerbnetFrame, first frame
    :var predicate: str, predicate
    """
    
    def __init__(self, frame, predicate):
        self.frame = frame
        self.predicate = predicate
        
    def __str__(self):
        return ("Error : tried to use a frame without any slot in frame matching\n"
               "frame : {}\npredicate : {}".format(self.frame, self.predicate))
               
class FrameMatcher():
    def __init__(self, predicate, frame):
        self.predicate = predicate
        self.frame = frame
        self.frame_size = 0
        self.best_score = 0
        self.roles_distribs = []
        
        for i,elem in enumerate(self.frame.structure):
            if FrameMatcher._is_a_slot(elem): self.frame_size += 1
            
        if self.frame_size == 0:
            raise EmptyFrameError(frame, predicate)
    
    def new_match(self, test_frame):
        """Compute the matching score and update the possible roles distribs
            
        :param test_frame: frame to test.
        :type test_frame: VerbnetFrame.
            
        """
        num_match = 0
        model_size = 0
        distrib = []
  
        for elem1,elem2 in zip(self.frame.structure, test_frame.structure):
            if FrameMatcher._is_a_match(elem1, elem2): 
                if FrameMatcher._is_a_slot(elem1):
                    distrib.append(test_frame.roles[len(distrib)])
            else: break
      
        for elem in test_frame.structure:
            if FrameMatcher._is_a_slot(elem): model_size += 1
           
        if model_size == 0:
            print("Warning : tried to use a frame without any slot in frame matching\n"
                  "predicate : {}\nframe 1 : {}\nframe 2 : {}".format(
                    self.predicate, self.frame, test_frame),
                  sys.stderr)
            return
        
        num_match = len(distrib)
        score = int(100 * (num_match / self.frame_size + num_match / model_size))
        
        if score > self.best_score: self.roles_distribs = []    
        if score >= self.best_score:
            self.roles_distribs.append(distrib)
            self.best_score = score
    
    def possible_distribs(self):
        """Compute the lists of possible roles for each slots
        
        :returns: str lists list -- The lists of possible roles for each slot
        """
        result = []
        for distrib in self.roles_distribs:
            for i,role in enumerate(distrib):
                if len(result) <= i: result.append([])
                if not role in result[i]: result[i].append(role)
        
        return result
            
    @staticmethod
    def _is_a_slot(elem):
        """Tell wether an element represent a slot
        
        :param elem: The element.
        :type elem: str.
        :returns: bool -- True if elem represents a solt, False otherwise
        """
        
        return elem[0].isupper() and elem != "V"

    @staticmethod        
    def _is_a_match(elem1, elem2):
        """Tell wether two elements can be considered as a match
        
        :param elem1: first element.
        :type elem1: str.
        :param elem2: second element.
        :type elem2: str.
        :returns: bool -- True if this is a match, False otherwise
        """
        
        return elem1 in elem2.split("/")
        
class frameMatcherTest(unittest.TestCase):
     def test_1(self):
        frame1 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], [])
        frame2 = VerbnetFrame(["NP", "V", "NP", "for", "NP"], ["Agent", "Patient", "Role1"])
        frame3 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], ["Agent", "Patient", "Role2"])
        frame4 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], ["Agent", "Patient", "Role3"])

        matcher = FrameMatcher("predicate", frame1)
        matcher.new_match(frame2)
        self.assertEqual(matcher.best_score, int(100 * 4 / 3))
        matcher.new_match(frame3)
        matcher.new_match(frame4)
        self.assertEqual(matcher.best_score, 200)
        self.assertEqual(matcher.possible_distribs(), [["Agent"], ["Patient"], ["Role2", "Role3"]])
        
     def test_2(self):
        frame1 = VerbnetFrame(["to", "be"], [])
        frame2 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], ["Agent", "Patient", "Role3"])

        with self.assertRaises(EmptyFrameError):
            matcher = FrameMatcher("predicate", frame1)
            matcher.new_match(frame2)
            
     def test_3(self):
        frame1 = VerbnetFrame(["NP", "V", "with", "NP"], [])
        frame2 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], ["Agent", "Patient", "Role3"])

        matcher = FrameMatcher("predicate", frame1)
        matcher.new_match(frame2)
        self.assertEqual(matcher.best_score, int(100 / 2 + 100 / 3))
            
if __name__ == "__main__":
    unittest.main()
        
