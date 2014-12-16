#!/usr/bin/env python3

import unittest

from verbnetframe import VerbnetOfficialFrame


class VerbnetOfficialFrameTest(unittest.TestCase):
    '''Tests operations on frames from the VerbNet resource.

    'XX' denotes the vnclass, which is not relevant here'''

    def test_transitive(self):
        vn_frame_transitive = VerbnetOfficialFrame('XX', [
            {'elem': 'NP', 'role': 'Agent', 'restr': 'a'},
            {'elem': 'V'},
            {'elem': 'NP', 'role': 'Theme', 'restr': 'b'}])

        self.assertEqual(vn_frame_transitive.passivize(), [
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
                {'elem': 'V'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
                {'elem': 'V'},
                {'elem': 'by'},
                {'elem': 'NP', 'role': 'Agent', 'restr': 'a'}])])

    def test_ditransitive(self):
        vn_frame_ditransitive = VerbnetOfficialFrame('XX', [
            {'elem': 'NP', 'role': 'Agent', 'restr': 'a'},
            {'elem': 'V'},
            {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
            {'elem': 'at'}, {'elem': 'NP', 'role': 'Value', 'restr': 'c'}])

        self.assertEqual(vn_frame_ditransitive.passivize(), [
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
                {'elem': 'V'},
                {'elem': 'at'}, {'elem': 'NP', 'role': 'Value', 'restr': 'c'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
                {'elem': 'V'},
                {'elem': 'by'}, {'elem': 'NP', 'role': 'Agent', 'restr': 'a'},
                {'elem': 'at'}, {'elem': 'NP', 'role': 'Value', 'restr': 'c'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
                {'elem': 'V'},
                {'elem': 'at'}, {'elem': 'NP', 'role': 'Value', 'restr': 'c'},
                {'elem': 'by'}, {'elem': 'NP', 'role': 'Agent', 'restr': 'a'}])])

    def test_strange(self):
        vn_frame_strange = VerbnetOfficialFrame('XX', [
            {'elem': 'NP', 'role': 'Agent', 'restr': 'a'},
            {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
            {'elem': 'V'},
            {'elem': 'S', 'role': 'Value', 'restr': 'c'}])

        self.assertEqual(vn_frame_strange.passivize(), [
            VerbnetOfficialFrame('XX', [
                {'elem': 'S', 'role': 'Value', 'restr': 'c'},
                {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
                {'elem': 'V'}]),
            VerbnetOfficialFrame('XX', [
                {'elem': 'S', 'role': 'Value', 'restr': 'c'},
                {'elem': 'NP', 'role': 'Theme', 'restr': 'b'},
                {'elem': 'V'}, {'elem': 'by'},
                {'elem': 'NP', 'role': 'Agent', 'restr': 'a'}])])
