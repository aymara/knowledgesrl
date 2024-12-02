#!/usr/bin/env python3

import sys
import unittest
import xml.etree.ElementTree as ET

from verbnetreader import VerbnetReader
import paths
from verbnetframe import VerbnetOfficialFrame
from verbnetrestrictions import VNRestriction
import verbnetprepclasses

class VerbnetReaderTest(unittest.TestCase):
    '''Unit test class'''

    def test_global(self):
        reader = VerbnetReader(paths.Paths.verbnet_path("eng"))
        self.assertEqual(len(reader.frames_for_verb), 4402)
        empty_restr = VNRestriction.build_empty()

        test_frames = {
            'sparkle': VerbnetOfficialFrame('light_emission-43.1', [
                {'elem': 'there'},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Theme', 'restr': VNRestriction.build_not(VNRestriction.build('animate'))},
                {'elem': verbnetprepclasses.prep['loc']}, {'elem': 'NP', 'role': 'Location', 'restr': empty_restr}]),
            'employ': VerbnetOfficialFrame('use-105', [
                {'elem': 'NP', 'role': 'Agent', 'restr': VNRestriction.build_or(VNRestriction.build('animate'), VNRestriction.build('organization'))},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Theme', 'restr': empty_restr}]),
            'break': VerbnetOfficialFrame('break-45.1', [
                {'elem': 'NP', 'role': 'Patient', 'restr': VNRestriction.build('solid')},
                {'elem': 'V'}]),
            'suggest': VerbnetOfficialFrame('say-37.7', [
                {'elem': 'NP', 'role': 'Agent', 'restr': VNRestriction.build_or(VNRestriction.build('animate'), VNRestriction.build('organization'))},
                {'elem': 'V'},
                {'elem': 'how'}, {'elem': 'to'}, {'elem': 'S', 'role': 'Topic', 'restr': VNRestriction.build('communication')}]),
            'snooze': VerbnetOfficialFrame('snooze-40.4', [
                {'elem': 'NP', 'role': 'Agent', 'restr': VNRestriction.build('animate')},
                {'elem': 'V'}])
        }

        for verb, frame in test_frames.items():
            self.assertIn(verb, reader.frames_for_verb)
            self.assertIn(frame, reader.frames_for_verb[verb])

        reader.frames_for_verb = {}
        root = ET.ElementTree(file=str(paths.Paths.verbnet_path("eng")
                                       / 'separate-23.1.xml'))
        reader._handle_class(root.getroot(), [], [], [])

        animate = VNRestriction.build('animate')

        list1 = [
            VerbnetOfficialFrame('separate-23.1', [
                {'elem': 'NP', 'role': 'Agent', 'restr': VNRestriction.build('animate')},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Patient', 'restr': empty_restr},
                {'elem': {'from'}}, {'elem': 'NP', 'role': 'Co-Patient', 'restr': empty_restr}]),
            VerbnetOfficialFrame('separate-23.1', [
                {'elem': 'NP', 'role': 'Agent', 'restr': VNRestriction.build('animate')},
                {'elem': 'V'},
                {'elem': 'NP', 'role': 'Patient', 'restr': empty_restr}]),
            VerbnetOfficialFrame('separate-23.1', [
                {'elem': 'NP', 'role': 'Patient', 'restr': empty_restr},
                {'elem': 'V'}]),
            VerbnetOfficialFrame('separate-23.1', [
                {'elem': 'NP', 'role': 'Patient', 'restr': empty_restr},
                {'elem': 'V'},
                {'elem': {'from'}}, {'elem': 'NP', 'role': 'Co-Patient', 'restr': empty_restr}]),
            VerbnetOfficialFrame('separate-23.1', [
                {'elem': 'NP', 'role': 'Patient', 'restr': empty_restr},
                {'elem': 'V'}])
        ]

        list2 = [VerbnetOfficialFrame('separate-23.1-1', [
            {'elem': 'NP', 'role': 'Patient', 'restr': empty_restr},
            {'elem': 'V'},
            {'elem': {'from'}}, {'elem': 'NP', 'role': 'Co-Patient', 'restr': empty_restr}])]

        list3 = [VerbnetOfficialFrame('separate-23.1-2', [
            {'elem': 'NP', 'role': 'Patient', 'restr': empty_restr},
            {'elem': 'V'},
            {'elem': {'with'}}, {'elem': 'NP', 'role': 'Co-Patient', 'restr': empty_restr}])]

        expected_result = {
            'dissociate': list1+list3,
            'disconnect': list1+list3,
            'divide': list1+list2,
            'disassociate': list1,
            'disentangle': list1+list2,
            'divorce': list1+list2,
            'separate': list1+list3,
            'segregate': list1+list2,
            'part': list1+list3,
            'differentiate': list1+list2,
            'uncoil': list1,
            'decouple': list1+list2,
            'sever': list1,
            'dissimilate': list1+list2
        }

        for verb in expected_result:
            if expected_result[verb] != reader.frames_for_verb[verb]:
                print('Error with {}'.format(verb))
                for expected, got in zip(expected_result[verb], reader.frames_for_verb[verb]):
                    if expected != got:
                        print('{} != {}'.format(expected, got))

        self.assertEqual(reader.frames_for_verb, expected_result)

if __name__ == '__main__':
    unittest.main()
