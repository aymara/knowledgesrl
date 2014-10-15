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
            ["NP.Agent", "V", "NP.Theme"],
            "XX", [])
        self.assertEqual(vn_frame_transitive.passivize(), [
            VerbnetOfficialFrame(["NP.Theme", "V"], "XX", []),
            VerbnetOfficialFrame(["NP.Theme", "V", "by", "NP.Agent"], "XX", [])])

        vn_frame_ditransitive = VerbnetOfficialFrame(
            ["NP.Agent", "V", "NP.Theme", "at", "NP.Value"], "XX", [])
        self.assertEqual(vn_frame_ditransitive.passivize(), [
            VerbnetOfficialFrame(
                ["NP.Theme", "V", "at", "NP.Value"], "XX", []),
            VerbnetOfficialFrame(
                ["NP.Theme", "V", "by", "NP.Agent", "at", "NP.Value"], "XX", []),
            VerbnetOfficialFrame(
                ["NP.Theme", "V", "at", "NP.Value", "by", "NP.Agent"], "XX", [])])

        vn_frame_strange = VerbnetOfficialFrame(
            ["NP.Agent", "NP.Theme", "V", "S.Value"], "XX", [])
        self.assertEqual(vn_frame_strange.passivize(), [
            VerbnetOfficialFrame(
                ["S.Value", "NP.Theme", "V"], "XX", []),
            VerbnetOfficialFrame(
                ["S.Value", "NP.Theme", "V", "by", "NP.Agent"],"XX", [])])
