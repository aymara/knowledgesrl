#!/usr/bin/env python3

import sys
import unittest

from verbnetframe import VerbnetFrameOccurrence, VerbnetOfficialFrame
from framematcher import FrameMatcher

class FrameMatcherTest(unittest.TestCase):
    def test_1(self):
        frame_occurrence = VerbnetFrameOccurrence([{'elem': 'NP'}, {'elem': 'V'}, {'elem': 'NP'}, {'elem': 'with'}, {'elem': 'NP'}], 3, 'a predicate')
        frame2 = VerbnetOfficialFrame('Class 1', [
            {'elem': 'NP', 'role': 'Agent'},
            {'elem': 'V'},
            {'elem': 'NP', 'role': 'Patient'},
            {'elem': 'for'}, {'elem': 'NP', 'role': 'Role1'}])
        frame3 = VerbnetOfficialFrame('Class 1', [
            {'elem': 'NP', 'role': 'Agent'},
            {'elem': 'V'},
            {'elem': 'NP', 'role': 'Patient'},
            {'elem': 'with'}, {'elem': 'NP', 'role': 'Role2'}])
        frame4 = VerbnetOfficialFrame('Class 2', [
            {'elem': 'NP', 'role': 'Agent'},
            {'elem': 'V'},
            {'elem': 'NP', 'role': 'Patient'},
            {'elem': 'with'}, {'elem': 'NP', 'role': 'Role3'}])

        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')
        best_score = matcher.perform_frame_matching([frame2])
        self.assertEqual(best_score, int(100 * 4 / 3))
        best_score = matcher.perform_frame_matching([frame3, frame4])
        self.assertEqual(best_score, 200)
        self.assertEqual(frame_occurrence.possible_roles(), [{'Agent'}, {'Patient'}, {'Role2', 'Role3'}])
        self.assertEqual(frame_occurrence.roles, [{'Agent'}, {'Patient'}, {'Role2', 'Role3'}])

    def test_2(self):
        frame_occurrence = VerbnetFrameOccurrence([{'elem': 'to'}, {'elem': 'be'}], 0, 'a predicate')
        frame = VerbnetOfficialFrame('c', [
            {'elem': 'NP', 'role': 'Agent'},
            {'elem': 'V'},
            {'elem': 'NP', 'role': 'Patient'},
            {'elem': 'with'}, {'elem': 'NP', 'role': 'Role3'}])

        self.assertEqual(frame_occurrence.num_slots, 0)

    def test_3(self):
        frame_occurrence = VerbnetFrameOccurrence([{'elem': 'NP'}, {'elem': 'V'}, {'elem': 'with'}, {'elem': 'NP'}], 2, 'a predicate')
        frame = VerbnetOfficialFrame('c', [
            {'elem': 'NP', 'role': 'Agent'},
            {'elem': 'V'},
            {'elem': 'NP', 'role': 'Patient'},
            {'elem': 'with'}, {'elem': 'NP', 'role': 'Role3'}])

        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')
        best_score = matcher.perform_frame_matching([frame])
        self.assertEqual(best_score, int(100 / 2 + 100 / 3))

    def test_4(self):
        frame_occurrence = VerbnetFrameOccurrence([{'elem': 'NP'}, {'elem': 'V'}, {'elem': 'NP'}], 2, 'a predicate')
        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')
        verbnet_frames = [
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Agent'},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Theme'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Agent'},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Theme'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Theme'},
                {'elem': 'V'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Agent'},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Theme'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Theme'},
                {'elem': 'V'},
                {'elem': 'with'}, {'elem': 'NP', 'role': 'Instrument'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Agent'},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Theme'},
                {'elem': 'with'}, {'elem': 'NP', 'role': 'Instrument'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Instrument'},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Theme'}])
        ]
        matcher.perform_frame_matching(verbnet_frames)

        self.assertEqual(frame_occurrence.roles, [{'Agent', 'Instrument'}, {'Theme'}])


    def test_baseline_alg(self):
        frame_occurrence = VerbnetFrameOccurrence([{'elem': 'NP'}, {'elem': 'V'}, {'elem': 'NP'}, {'elem': 'NP'}, {'elem': 'for'}, {'elem': 'NP'}], 4, 'a predicate')

        verbnet_frames = [
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'R1'},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'R2'},
                {'elem': 'by'}, {'elem': 'NP', 'role': 'R3'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'R1'},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'R4'},
                {'elem': {'for', 'as'}}, {'elem': 'NP', 'role': 'R5'}])
        ]
        matcher = FrameMatcher(frame_occurrence, 'baseline')
        matcher.perform_frame_matching(verbnet_frames)
        self.assertEqual(frame_occurrence.roles, [{'R1'}, {'R4'}, set(), {'R5'}])

    def test_removed_that(self):
        # They considered he was the professor
        frame_occurrence = VerbnetFrameOccurrence([{'elem': 'NP'}, {'elem': 'V'}, {'elem': 'S'}], 2, 'consider')
        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')

        best_score = matcher.perform_frame_matching([VerbnetOfficialFrame('consider-29.9-1', [
            {'elem': 'NP', 'role': 'Agent'},
            {'elem': 'V'},
            {'elem': 'that'}, {'elem': 'S', 'role': 'Patient'}])])

        self.assertEqual(best_score, 200)
        self.assertEqual(frame_occurrence.roles, [{'Agent'}, {'Patient'}])

    def test_present_that(self):
        frame_occurrence = VerbnetFrameOccurrence([{'elem': 'NP'}, {'elem': 'V'}, {'elem': 'that'}, {'elem': 'S'}], 2, 'consider')
        matcher = FrameMatcher(frame_occurrence, 'sync_predicates')

        best_score = matcher.perform_frame_matching([VerbnetOfficialFrame('consider-29.9-1', [
            {'elem': 'NP', 'role': 'Agent'},
            {'elem': 'V'},
            {'elem': 'that'}, {'elem': 'S', 'role': 'Patient'}])])

        self.assertEqual(best_score, 200)
        self.assertEqual(frame_occurrence.roles, [{'Agent'}, {'Patient'}])

if __name__ == '__main__':
    unittest.main()
