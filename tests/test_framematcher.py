#!/usr/bin/env python3

import unittest

from verbnetframe import VerbnetFrameOccurrence, VerbnetOfficialFrame
from framematcher import FrameMatcher

class FrameMatcherTest(unittest.TestCase):
    def test_1(self):
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'NP', 'with', 'NP'], 3, 'a predicate')
        frame2 = VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('NP', 'Patient'), ('for', None), ('NP', 'Role1')], 'a', [])
        frame3 = VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('NP', 'Patient'), ('with', None), ('NP', 'Role2')], 'b', [])
        frame4 = VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('NP', 'Patient'), ('with', None), ('NP', 'Role3')], 'c', [])

        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')
        matcher.new_match(frame2)
        self.assertEqual(frame_occurrence.best_score, int(100 * 4 / 3))
        matcher.new_match(frame3)
        matcher.new_match(frame4)
        self.assertEqual(frame_occurrence.best_score, 200)
        self.assertEqual(frame_occurrence.roles(), [{'Agent'}, {'Patient'}, {'Role2', 'Role3'}])
        
    def test_2(self):
        frame_occurrence = VerbnetFrameOccurrence(['to', 'be'], 0, 'a predicate')
        frame = VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('NP', 'Patient'), ('with', None), ('NP', 'Role3')], 'c', [])

        self.assertEqual(frame_occurrence.num_slots, 0)
            
    def test_3(self):
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'with', 'NP'], 2, 'a predicate')
        frame = VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('NP', 'Patient'), ('with', None), ('NP', 'Role3')], 'c', [])

        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')
        matcher.new_match(frame)
        self.assertEqual(frame_occurrence.best_score, int(100 / 2 + 100 / 3))
        
    def test_4(self):
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'NP'], 2, 'a predicate')
        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')
        verbnet_frames = [
            VerbnetOfficialFrame([('NP', 'Agent'), ('V', None), ('NP', 'Theme')], 'XX', []),
            VerbnetOfficialFrame([('NP', 'Agent'), ('V', None), ('NP', 'Theme')], 'XX', []),
            VerbnetOfficialFrame([('NP', 'Theme'), ('V', None)], 'XX', []),
            VerbnetOfficialFrame([('NP', 'Agent'), ('V', None), ('NP', 'Theme')], 'XX', []),
            VerbnetOfficialFrame([('NP', 'Theme'), ('V', None), ({'with'}, None), ('NP', 'Instrument')],
                                 'XX', []),
            VerbnetOfficialFrame([('NP', 'Agent'), ('V', None), ('NP', 'Theme'), ({'with'}, None), ('NP', 'Instrument')],
                                 'XX', []),
            VerbnetOfficialFrame([('NP', 'Instrument'), ('V', None), ('NP', 'Theme')], 'XX', [])
        ]
        for verbnet_frame in verbnet_frames:
            matcher.new_match(verbnet_frame)
            
        self.assertEqual(frame_occurrence.roles(), [{'Agent', 'Instrument'}, {'Theme'}])
     
                 
    def test_baseline_alg(self):
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'NP', 'NP', 'for', 'NP'], 4, 'a predicate')
        
        verbnet_frames = [
            VerbnetOfficialFrame(
                [('NP', 'R1'), ('V', None), ('NP', 'R2'), ('by', None), ('NP', 'R3')],
                'XX', []),
            VerbnetOfficialFrame(
                [('NP', 'R1'), ('V', None), ('NP', 'R4'), ({'for', 'as'}, None), ('NP', 'R5')],
                'XX', [])
        ]
        matcher = FrameMatcher(frame_occurrence, 'baseline')
        for verbnet_frame in verbnet_frames:
            matcher.new_match(verbnet_frame)
        self.assertEqual(frame_occurrence.roles(), [{'R1'}, {'R4'}, set(), {'R5'}])

    def test_removed_that(self):
        # They considered he was the professor
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'S'], 2, 'consider')
        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')

        matcher.new_match(VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('that', None), ('S', 'Patient')],
            'consider-29.9-1', []))
        self.assertEqual(frame_occurrence.best_score, 200)
        self.assertEqual(frame_occurrence.roles(), [{'Agent'}, {'Patient'}])

    def test_present_that(self):
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'that', 'S'], 2, 'consider')
        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')

        matcher.new_match(VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('that', None), ('S', 'Patient')],
            'consider-29.9-1', []))
        self.assertEqual(frame_occurrence.best_score, 200)
        self.assertEqual(frame_occurrence.roles(), [{'Agent'}, {'Patient'}])
