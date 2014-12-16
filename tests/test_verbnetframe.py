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
            [{'elem': 'NP', 'role': 'Agent'}, {'elem': 'V'}, {'elem': 'NP', 'role': 'Theme'}], 'XX', [])
        self.assertEqual(vn_frame_transitive.passivize(), [
            VerbnetOfficialFrame([{'elem': 'NP', 'role': 'Theme'}, {'elem': 'V'}], 'XX', []),
            VerbnetOfficialFrame([{'elem': 'NP', 'role': 'Theme'}, {'elem': 'V'}, {'elem': 'by'}, {'elem': 'NP', 'role': 'Agent'}], 'XX', [])])

    def test_ditransitive(self):
        vn_frame_ditransitive = VerbnetOfficialFrame(
            [{'elem': 'NP', 'role': 'Agent'}, {'elem': 'V'}, {'elem': 'NP', 'role': 'Theme'}, {'elem': 'at'}, {'elem': 'NP', 'role': 'Value'}], 'XX', [])
        self.assertEqual(vn_frame_ditransitive.passivize(), [
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Theme'}, {'elem': 'V'}, {'elem': 'at'}, {'elem': 'NP', 'role': 'Value'}], 'XX', []),
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Theme'}, {'elem': 'V'}, {'elem': 'by'}, {'elem': 'NP', 'role': 'Agent'}, {'elem': 'at'}, {'elem': 'NP', 'role': 'Value'}], 'XX', []),
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Theme'}, {'elem': 'V'}, {'elem': 'at'}, {'elem': 'NP', 'role': 'Value'}, {'elem': 'by'}, {'elem': 'NP', 'role': 'Agent'}], 'XX', [])])

    def test_strange(self):
        vn_frame_strange = VerbnetOfficialFrame(
            [{'elem': 'NP', 'role': 'Agent'}, {'elem': 'NP', 'role': 'Theme'}, {'elem': 'V'}, {'elem': 'S', 'role': 'Value'}], 'XX', [])
        self.assertEqual(vn_frame_strange.passivize(), [
            VerbnetOfficialFrame(
                [{'elem': 'S', 'role': 'Value'}, {'elem': 'NP', 'role': 'Theme'}, {'elem': 'V'}], 'XX', []),
            VerbnetOfficialFrame(
                [{'elem': 'S', 'role': 'Value'}, {'elem': 'NP', 'role': 'Theme'}, {'elem': 'V'}, {'elem': 'by'}, {'elem': 'NP', 'role': 'Agent'}],'XX', [])])
