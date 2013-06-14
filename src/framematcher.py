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
from collections import defaultdict
import unittest
import sys

matching_algorithm = "sync_predicates"

class EmptyFrameError(Exception):
    """Trying to use an empty frame in a FrameMatcher
    
    :var frame: VerbnetFrame, first frame
    :var predicate: str, predicate
    """
    
    def __init__(self, frame):
        self.frame = frame

    def __str__(self):
        return ("Error : tried to use a frame without any slot in frame matching\n"
               "frame : {}\npredicate : {}".format(self.frame, self.frame.predicate))
               
class FrameMatcher():
    """Handle frame matching for a given frame that we want to annotate.
    
    :var predicate: str -- The frame's predicate (for debug purposes)
    :var frame: VerbnetFrame -- The frame to annotate
    :var best_score: int -- The best score encountered among all the matches
    :var best_frames: VerbnetFrame List -- The frames that achieved this best score (for debug purposes)
    :var num_new_match: int -- The total number of calls to new_match
    :var possible_roles: str Dict List -- A map of possible roles for every slot (the keys contains the VerbNet class from which each role comes)
    :var algo: str -- The algorithm that we want to use
    
    """
    
    def __init__(self, frame, algo = matching_algorithm):
        if frame.num_slots == 0:
            raise EmptyFrameError(frame)

        self.frame = frame
        self.best_score = 0
        self.best_frames = []
        self.num_new_match = 0
        self.possible_roles = [{} for x in range(self.frame.num_slots)] 
        self.algo = algo

    def new_match(self, test_frame):
        """Compute the matching score and update the possible roles distribs
            
        :param test_frame: frame to test.
        :type test_frame: VerbnetFrame.
            
        """
        self.num_new_match += 1
        distrib = [None for x in range(self.frame.num_slots)] 
        num_match = 0

        if self.algo == "baseline":
            # As slots are not attributed in order, we need to keep a list
            # of the slots that have not been attributed yet
            available_slots = []

            for i, x in enumerate(test_frame.slot_types):
                available_slots.append(
                    {"slot_type":x, "pos":i, "prep":test_frame.slot_preps[i]}
                )

            for slot_pos, slot_type in enumerate(self.frame.slot_types):
                # For every slot, try to find a matching slot in available_slots
                i, matching_slot = -1, -1
                
                for test_slot_data in available_slots:
                    # Could have used enumerate, but it looks better like this
                    # as i is used after the loop
                    i += 1

                    # We want a slot that has the same type and the same prep
                    # (or a list slot preps containing our preposition)
                    if test_slot_data["slot_type"] != slot_type:
                        continue
                    if (slot_type == VerbnetFrame.slot_types["prep_object"] and
                        not VerbnetFrame._is_a_match(
                            self.frame.slot_preps[slot_pos], 
                            test_slot_data["prep"])
                    ):
                        continue
                    matching_slot = test_slot_data["pos"]
                    break # Stop at the first good slot we find
                
                if matching_slot != -1:
                    del available_slots[i] # Slot i has been attributed
                    #FIXME : we need to check that enough roles were given in VerbNet
                    if len(test_frame.roles) > matching_slot:
                        distrib[slot_pos] = next(iter(test_frame.roles[matching_slot]))
                        
                num_match += 1
            
        elif self.algo == "sync_predicates":
            """ New algorithm """
            i, j = 0, 0
            index_v_1 = self.frame.structure.index("V")
            index_v_2 = test_frame.structure.index("V")
            slot_1, slot_2 = 0, 0
            num_slots_before_v_1 = 0
            num_slots_before_v_2 = 0
            
            for elem in self.frame.structure:
                if VerbnetFrame._is_a_slot(elem):
                    num_slots_before_v_1 += 1
                elif elem == "V": break
            for elem in test_frame.structure:
                if VerbnetFrame._is_a_slot(elem):
                    num_slots_before_v_2 += 1
                elif elem == "V": break

            while i < len(self.frame.structure) and j < len(test_frame.structure):
                elem1 = self.frame.structure[i]
                elem2 = test_frame.structure[j]

                if VerbnetFrame._is_a_match(elem1, elem2): 
                    if VerbnetFrame._is_a_slot(elem1):
                        num_match += 1
                        # test_frame.roles can be too short. This will for instance
                        # happen in the "NP V NP S_INF" structure of want-32.1,
                        # where S_INF is given no role
                        if slot_2 < len(test_frame.roles):
                            distrib[slot_1] = next(iter(test_frame.roles[slot_2]))
                            slot_1, slot_2 = slot_1 + 1, slot_2 + 1
                elif i < index_v_1 or j < index_v_2:
                    # If we have not encountered the verb yet, we continue the matching
                    # with everything that follows the verb
                    # This is for instance to prevent a "NP NP V" construct 
                    # from interrupting the matching early
                    i, j = index_v_1, index_v_2
                    slot_1, slot_2 = num_slots_before_v_1, num_slots_before_v_2
                else: break
                   
                i, j = i + 1, j + 1
        elif self.algo == "stop_on_fail":     
            """ Former less permissive algorithm """
            for elem1,elem2 in zip(self.frame.structure, test_frame.structure):
                if VerbnetFrame._is_a_match(elem1, elem2): 
                    if VerbnetFrame._is_a_slot(elem1):
                        num_match += 1
                        if num_match - 1 < len(test_frame.roles):
                            distrib[num_match - 1] = next(iter(test_frame.roles[num_match - 1]))
                else: break
        else:
            raise Exception("Unknown matching algorithm : {}".format(self.algo))

        ratio_1 = num_match / self.frame.num_slots
        if test_frame.num_slots == 0:
            ratio_2 = 1          
        else:
            ratio_2 = num_match / test_frame.num_slots

        score = int(100 * (ratio_1 + ratio_2))

        if score > self.best_score:
            self.possible_roles = [{} for x in range(self.frame.num_slots)] 
            self.best_frames = []
        if score >= self.best_score:
            for slot, role in enumerate(distrib):
                if role != None:
                    index = "{}_{}".format(test_frame.vnclass, self.num_new_match)
                    self.possible_roles[slot][index] = role
            
            self.best_frames.append(test_frame)
            self.best_score = score
    
    def possible_distribs(self):
        """Compute the lists of possible roles for each slots
        
        :returns: str set list -- The lists of possible roles for each slot
        """
        return [set(x.values()) for x in self.possible_roles]
        
class frameMatcherTest(unittest.TestCase):
    def test_1(self):
        frame1 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], [None, None, None])
        frame2 = VerbnetFrame(["NP", "V", "NP", "for", "NP"], ["Agent", "Patient", "Role1"], "a")
        frame3 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], ["Agent", "Patient", "Role2"], "b")
        frame4 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], ["Agent", "Patient", "Role3"], "c")

        matcher = FrameMatcher(frame1, "sync_predicates")
        matcher.new_match(frame2)
        self.assertEqual(matcher.best_score, int(100 * 4 / 3))
        matcher.new_match(frame3)
        matcher.new_match(frame4)
        self.assertEqual(matcher.best_score, 200)
        self.assertEqual(matcher.possible_distribs(), [{"Agent"}, {"Patient"}, {"Role2", "Role3"}])
        
    def test_2(self):
        frame1 = VerbnetFrame(["to", "be"], [])
        frame2 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], ["Agent", "Patient", "Role3"])

        with self.assertRaises(EmptyFrameError):
            matcher = FrameMatcher(frame1, "sync_predicates")
            matcher.new_match(frame2)
            
    def test_3(self):
        frame1 = VerbnetFrame(["NP", "V", "with", "NP"], [None, None])
        frame2 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], ["Agent", "Patient", "Role3"])

        matcher = FrameMatcher(frame1, "sync_predicates")
        matcher.new_match(frame2)
        self.assertEqual(matcher.best_score, int(100 / 2 + 100 / 3))
        
    def test_4(self):
        frame = VerbnetFrame(['NP', 'V', 'NP'], [None, None])
        matcher = FrameMatcher(frame, "sync_predicates")
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
            
        self.assertEqual(matcher.possible_distribs(), [{"Agent", "Instrument"}, {"Theme"}])
     
                 
    def test_baseline_alg(self):
        matching_algorithm = "baseline"
        frame = VerbnetFrame(['NP', 'V', 'NP', 'NP', 'for', 'NP'], [None, None, None, None])
        
        test_frames = [
            VerbnetFrame(['NP', 'V', 'NP', 'by', 'NP'], ['R1', 'R2', 'R3']),
            VerbnetFrame(['NP', 'V', 'NP', ['for', 'as'], 'NP'], ['R1', 'R4', 'R5'])
        ]
        matcher = FrameMatcher(frame, "baseline")
        for test_frame in test_frames:
            matcher.new_match(test_frame)
        self.assertEqual(matcher.possible_distribs(), [{"R1"}, {"R2", "R4"}, set(), {"R5"}])
       
if __name__ == "__main__":
    unittest.main()
        
