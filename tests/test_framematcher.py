#!/usr/bin/env python3

import unittest

from verbnetframe import VerbnetFrameOccurrence, VerbnetOfficialFrame
from framematcher import FrameMatcher

class FrameMatcherTest(unittest.TestCase):
    def test_1(self):
        frame_occurrence = VerbnetFrameOccurrence(["NP", "V", "NP", "with", "NP"], [None, None, None], "a predicate")
        frame2 = VerbnetOfficialFrame(
            ["NP.Agent", "V", "NP.Patient", "for", "NP.Role1"], "a", [])
        frame3 = VerbnetOfficialFrame(
            ["NP.Agent", "V", "NP.Patient", "with", "NP.Role2"], "b", [])
        frame4 = VerbnetOfficialFrame(
            ["NP.Agent", "V", "NP.Patient", "with", "NP.Role3"], "c", [])

        matcher = FrameMatcher(frame_occurrence, "sync_predicates")
        matcher.new_match(frame2)
        self.assertEqual(matcher.best_score, int(100 * 4 / 3))
        matcher.new_match(frame3)
        matcher.new_match(frame4)
        self.assertEqual(matcher.best_score, 200)
        self.assertEqual(matcher.possible_distribs(), [{"Agent"}, {"Patient"}, {"Role2", "Role3"}])
        
    def test_2(self):
        frame_occurrence = VerbnetFrameOccurrence(["to", "be"], [], "a predicate")
        frame = VerbnetOfficialFrame(
            ["NP.Agent", "V", "NP.Patient", "with", "NP.Role3"], "c", [])

        self.assertEqual(frame_occurrence.num_slots, 0)
            
    def test_3(self):
        frame_occurrence = VerbnetFrameOccurrence(["NP", "V", "with", "NP"], [None, None], "a predicate")
        frame = VerbnetOfficialFrame(
            ["NP.Agent", "V", "NP.Patient", "with", "NP.Role3"], "c", [])

        matcher = FrameMatcher(frame_occurrence, "sync_predicates")
        matcher.new_match(frame)
        self.assertEqual(matcher.best_score, int(100 / 2 + 100 / 3))
        
    def test_4(self):
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'NP'], [None, None], "a predicate")
        matcher = FrameMatcher(frame_occurrence, "sync_predicates")
        verbnet_frames = [
            VerbnetOfficialFrame(['NP.Agent', 'V', 'NP.Theme'], "XX", []),
            VerbnetOfficialFrame(['NP.Agent', 'V', 'NP.Theme'], "XX", []),
            VerbnetOfficialFrame(['NP.Theme', 'V'], "XX", []),
            VerbnetOfficialFrame(['NP.Agent', 'V', 'NP.Theme'], "XX", []),
            VerbnetOfficialFrame(['NP.Theme', 'V', {'with'}, 'NP.Instrument'],
                                 "XX", []),
            VerbnetOfficialFrame(['NP.Agent', 'V', 'NP.Theme', {'with'}, 'NP.Instrument'],
                                 "XX", []),
            VerbnetOfficialFrame(['NP.Instrument', 'V', 'NP.Theme'], "XX", [])
        ]
        for verbnet_frame in verbnet_frames:
            matcher.new_match(verbnet_frame)
            
        self.assertEqual(matcher.possible_distribs(), [{"Agent", "Instrument"}, {"Theme"}])
     
                 
    def test_baseline_alg(self):
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'NP', 'NP', 'for', 'NP'], [None, None, None, None], "a predicate")
        
        verbnet_frames = [
            VerbnetOfficialFrame(
                ['NP.R1', 'V', 'NP.R2', 'by', 'NP.R3'],
                "XX", []),
            VerbnetOfficialFrame(
                ['NP.R1', 'V', 'NP.R4', {'for', 'as'}, 'NP.R5'],
                "XX", [])
        ]
        matcher = FrameMatcher(frame_occurrence, "baseline")
        for verbnet_frame in verbnet_frames:
            matcher.new_match(verbnet_frame)
        self.assertEqual(matcher.possible_distribs(), [{"R1"}, {"R4"}, set(), {"R5"}])

    def test_removed_that(self):
        # They considered he was the professor
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'S'], ['Agent', 'Theme'], "consider")
        matcher = FrameMatcher(frame_occurrence, "sync_predicates")

        matcher.new_match(VerbnetOfficialFrame(
            ['NP.Agent', 'V', 'that', 'S.Patient'],
            'consider-29.9-1', []))
        self.assertEqual(matcher.best_score, 200)
        self.assertEqual(matcher.possible_distribs(), [{'Agent'}, {'Patient'}])

    def test_present_that(self):
        frame_occurrence = VerbnetFrameOccurrence(['NP', 'V', 'that', 'S'], ['Agent', 'Theme'], "consider")
        matcher = FrameMatcher(frame_occurrence, "sync_predicates")

        matcher.new_match(VerbnetOfficialFrame(
            ['NP.Agent', 'V', 'that', 'S.Patient'],
            'consider-29.9-1', []))
        self.assertEqual(matcher.best_score, 200)
        self.assertEqual(matcher.possible_distribs(), [{'Agent'}, {'Patient'}])
