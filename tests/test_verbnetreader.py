#!/usr/bin/env python3

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
        reader = VerbnetReader(paths.VERBNET_PATH)
        self.assertEqual(len(reader.frames_for_verb), 4402)

        test_verbs = ['sparkle', 'employ', 'break', 'suggest', 'snooze']
        test_frames = [
            VerbnetOfficialFrame(
                [{'elem': 'there'}, {'elem': 'V'}, {'elem': 'NP', 'role': 'Theme'}, {'elem': verbnetprepclasses.prep['loc']}, {'elem': 'NP', 'role': 'Location'}],
                'light_emission-43.1', []),
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Agent'}, {'elem': 'V'}, {'elem': 'NP', 'role': 'Theme'}],
                'use-105', []),
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Patient'}, {'elem': 'V'}],
                'break-45.1', []),
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Agent'}, {'elem': 'V'}, {'elem': 'how'}, {'elem': 'to'}, {'elem': 'S', 'role': 'Topic'}],
                'say-37.7', []),
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Agent'}, {'elem': 'V'}],
                'snooze-40.4', [])
        ]
        restrictions_str = {
            'sparkle':['(NOT animate)', 'NORESTR'],
            'employ':['(animate) OR (organization)', 'NORESTR'],
            'break':['solid'],
            'suggest':['(animate) OR (organization)', 'communication'],
            'snooze':['animate']
        }

        for verb, frame in zip(test_verbs, test_frames):
            self.assertIn(verb, reader.frames_for_verb)
            self.assertIn(frame, reader.frames_for_verb[verb])
            vnframe = reader.frames_for_verb[verb][reader.frames_for_verb[verb].index(frame)]
            self.assertEqual(
                [str(x) for x in vnframe.role_restrictions], restrictions_str[verb])

        reader.frames_for_verb = {}
        root = ET.ElementTree(file=str(paths.VERBNET_PATH / 'separate-23.1.xml'))
        reader._handle_class(root.getroot(), [], [], [])

        animate = VNRestriction.build('animate')
        norestr = VNRestriction.build_empty()

        list1 = [
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Agent'}, {'elem': 'V'}, {'elem': 'NP', 'role': 'Patient'}, {'elem': {'from'}}, {'elem': 'NP', 'role': 'Co-Patient'}],
                'separate-23.1', [animate, norestr, norestr]),
            VerbnetOfficialFrame([{'elem': 'NP', 'role': 'Agent'}, {'elem': 'V'}, {'elem': 'NP', 'role': 'Patient'}], 'separate-23.1', [animate, norestr]),
            VerbnetOfficialFrame([{'elem': 'NP', 'role': 'Patient'}, {'elem': 'V'}], 'separate-23.1', [norestr]),
            VerbnetOfficialFrame(
                [{'elem': 'NP', 'role': 'Patient'}, {'elem': 'V'}, {'elem': {'from'}}, {'elem': 'NP', 'role': 'Co-Patient'}],
                'separate-23.1', [norestr, norestr]),
            VerbnetOfficialFrame([{'elem': 'NP', 'role': 'Patient'}, {'elem': 'V'}], 'separate-23.1', [norestr])]
        list2 = [VerbnetOfficialFrame(
            [{'elem': 'NP', 'role': 'Patient'}, {'elem': 'V'}, {'elem': {'from'}}, {'elem': 'NP', 'role': 'Co-Patient'}], 'separate-23.1-1', [norestr, norestr])]
        list3 = [VerbnetOfficialFrame(
            [{'elem': 'NP', 'role': 'Patient'}, {'elem': 'V'}, {'elem': {'with'}}, {'elem': 'NP', 'role': 'Co-Patient'}], 'separate-23.1-2', [])]
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
                print('Expected')
                for expected, got in zip(expected_result[verb], reader.frames_for_verb[verb]):
                    if expected != got:
                        print('{} != {}'.format(expected, got))

        self.assertEqual(reader.frames_for_verb, expected_result)
