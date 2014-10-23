#!/usr/bin/env python3

import unittest

from verbnetframe import VerbnetOfficialFrame

class VerbnetOfficialFrameTest(unittest.TestCase):
    '''Tests operations on frames from the VerbNet resource.

    'XX', [] denote the vnclass and role restrictions, we don't want them to be
    optional in __init__ to catch constructor call errors.
    '''
    def test_transitive(self):
        vn_frame_transitive = VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('NP', 'Theme')], 'XX', [])
        self.assertEqual(vn_frame_transitive.passivize(), [
            VerbnetOfficialFrame([('NP', 'Theme'), ('V', None)], 'XX', []),
            VerbnetOfficialFrame([('NP', 'Theme'), ('V', None), ('by', None), ('NP', 'Agent')], 'XX', [])])

    def test_ditransitive(self):
        vn_frame_ditransitive = VerbnetOfficialFrame(
            [('NP', 'Agent'), ('V', None), ('NP', 'Theme'), ('at', None), ('NP', 'Value')], 'XX', [])
        self.assertEqual(vn_frame_ditransitive.passivize(), [
            VerbnetOfficialFrame(
                [('NP', 'Theme'), ('V', None), ('at', None), ('NP', 'Value')], 'XX', []),
            VerbnetOfficialFrame(
                [('NP', 'Theme'), ('V', None), ('by', None), ('NP', 'Agent'), ('at', None), ('NP', 'Value')], 'XX', []),
            VerbnetOfficialFrame(
                [('NP', 'Theme'), ('V', None), ('at', None), ('NP', 'Value'), ('by', None), ('NP', 'Agent')], 'XX', [])])

    def test_strange(self):
        vn_frame_strange = VerbnetOfficialFrame(
            [('NP', 'Agent'), ('NP', 'Theme'), ('V', None), ('S', 'Value')], 'XX', [])
        self.assertEqual(vn_frame_strange.passivize(), [
            VerbnetOfficialFrame(
                [('S', 'Value'), ('NP', 'Theme'), ('V', None)], 'XX', []),
            VerbnetOfficialFrame(
                [('S', 'Value'), ('NP', 'Theme'), ('V', None), ('by', None), ('NP', 'Agent')],'XX', [])])
