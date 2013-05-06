#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Match Frame to appropriate VerbNet structures

Based on the 2004 Swier & Stevenson paper: Unsupervised Semantic Role Labeling.

The way frame matching works in Swier&Stevenson 2004 paper is not completely
specified: what happens when VerbNet frame is longer than FrameNet's frame?

Currently, we don't extract any slot when a non-match appears: while it can
make sense to omit objects at the end, it doesn't to omit at the beginning and
take at the end: this could result in a totally different syntactic
construction. But I could be wrong!

For example, if you have in FrameNet "NP V with NP", and VerbNet contains "NP V
NP with NP", what do you do? We decided, for now, to only match the syntactic
subject.
"""

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
        self.best_frames = []
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
        
        i = 0
        j = 0
        index_v_1 = self.frame.structure.index("V")
        index_v_2 = test_frame.structure.index("V")

        while i < len(self.frame.structure) and j < len(test_frame.structure):
            elem1 = self.frame.structure[i]
            elem2 = test_frame.structure[j]

            if FrameMatcher._is_a_match(elem1, elem2): 
                if FrameMatcher._is_a_slot(elem1):  
                    # test_frame.roles can be too short. This will for instance
                    # happen in the "NP V NP S_INF" structure of want-32.1,
                    # where S_INF is given no role
                    if len(distrib) < len(test_frame.roles):
                        distrib.append(test_frame.roles[len(distrib)])
            elif i < index_v_1 or j < index_v_2:
                # If we have not encountered the verb yet, we continue the matching
                # with everything that follows the verb
                # This is for instance to prevent a "NP NP V" construct 
                # from interrupting the matching early
                i = index_v_1
                j = index_v_2
            else: break
               
            i += 1
            j += 1
            
        """ Former less permissive algorithm
        for elem1,elem2 in zip(self.frame.structure, test_frame.structure):
            if FrameMatcher._is_a_match(elem1, elem2): 
                if FrameMatcher._is_a_slot(elem1):
                    # test_frame.roles can be too short. This will for instance
                    # happen in the "NP V NP S_INF" structure of want-32.1,
                    # where S_INF is given no role
                    if len(distrib) < len(test_frame.roles):
                        distrib.append(test_frame.roles[len(distrib)])
            else: break
        """

        for elem in test_frame.structure:
            if FrameMatcher._is_a_slot(elem): model_size += 1
           
        if model_size == 0:
            raise EmptyFrameError(test_frame, self.predicate)
        
        num_match = len(distrib)
        score = int(100 * (num_match / self.frame_size + num_match / model_size))
        
        if score > self.best_score:
            self.roles_distribs = []  
            self.best_frames = []
        if score >= self.best_score:
            self.roles_distribs.append(distrib)
            self.best_frames.append(test_frame)
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
        
        return ((isinstance(elem2, list) and elem1 in elem2) or
            elem1 == elem2)
        
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
        
    def test_4(self):
        frame = VerbnetFrame(['NP', 'V', 'NP'], [])
        matcher = FrameMatcher("begin", frame)
        test_frames = [
            VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Theme']),
            VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Theme']),
            VerbnetFrame(['NP', 'V'], ['Theme']),
            VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Theme']),
            VerbnetFrame(['NP', 'V', ['with'], 'NP'], ['Theme', 'Instrument']),
            VerbnetFrame(['NP', 'V', 'NP', ['with'], 'NP'], ['Agent', 'Theme', 'Instrument']),
            VerbnetFrame(['NP', 'V', 'NP'], ['Instrument', 'Theme'])
        ]
        for test_frame in test_frames:
            matcher.new_match(test_frame)
        print(matcher.best_score)
        print(matcher.possible_distribs())

            
if __name__ == "__main__":
    unittest.main()
        
