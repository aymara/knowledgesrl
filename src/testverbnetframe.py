#!/usr/bin/env python3

import unittest

from verbnetframe import VerbnetOfficialFrame

class VerbnetOfficialFrameTest(unittest.TestCase):
    """Tests operations on frames from the VerbNet resource.

    "XX", [] denote the vnclass and role restrictions, we don't want them to be
    optional in __init__ to catch constructor call errors.
    """
    def test_passivize(self):
        vn_frame_transitive = VerbnetOfficialFrame(
            ["NP", "V", "NP"],
            ["Agent", "Theme"],
            "XX", [])
        self.assertEqual(vn_frame_transitive.passivize(), [
            VerbnetOfficialFrame(["NP", "V"], ["Theme"], "XX", []),
            VerbnetOfficialFrame(["NP", "V", "by", "NP"], ["Theme", "Agent"], "XX", [])])

        vn_frame_ditransitive = VerbnetOfficialFrame(
            ["NP", "V", "NP", "at", "NP"],
            ["Agent", "Theme", "Value"], "XX", [])
        self.assertEqual(vn_frame_ditransitive.passivize(), [
            VerbnetOfficialFrame(
                ["NP", "V", "at", "NP"],
                ["Theme", "Value"], "XX", []),
            VerbnetOfficialFrame(
                ["NP", "V", "by", "NP", "at", "NP"],
                ["Theme", "Agent", "Value"], "XX", []),
            VerbnetOfficialFrame(
                ["NP", "V", "at", "NP", "by", "NP"],
                ["Theme", "Value", "Agent"], "XX", [])])

        vn_frame_strange = VerbnetOfficialFrame(
            ["NP", "NP", "V", "S"],
            ["Agent", "Theme", "Value"],
            "XX", [])
        self.assertEqual(vn_frame_strange.passivize(), [
            VerbnetOfficialFrame(
                ["S", "NP", "V"],
                ["Value", "Theme"],
                "XX", []),
            VerbnetOfficialFrame(
                ["S", "NP", "V", "by", "NP"],
                ["Value", "Theme", "Agent"],
                "XX", [])])

    def test_relatives(self):
        test_frame = VerbnetOfficialFrame(
            ["NP", "V", "NP", "for", "NP"],
            ["Agent", "Theme", "Beneficiary"],
            "XX", [])

        self.assertEqual(test_frame.generate_relatives(), [
            VerbnetOfficialFrame(
                ["NP", "V", "NP", "for", "NP"],
                ["Agent", "Theme", "Beneficiary"],
                "XX", []),
            VerbnetOfficialFrame(
                ["NP", "NP", "V", "for", "NP"],
                ["Theme", "Agent", "Beneficiary"],
                "XX", []),
            VerbnetOfficialFrame(
                ["for", "NP", "NP", "V", "NP"],
                ["Beneficiary", "Agent", "Theme"],
                "XX", [])
        ])
