#!/usr/bin/env python3

import unittest
import xml.etree.ElementTree as ET

from verbnetreader import VerbnetReader
import paths
from verbnetframe import VerbnetOfficialFrame
import verbnetprepclasses
        
class VerbnetReaderTest(unittest.TestCase):
    """Unit test class"""
    
    def test_global(self):
        reader = VerbnetReader(paths.VERBNET_PATH)
        self.assertEqual(len(reader.frames_for_verb), 4402)

        test_verbs = ["sparkle", "employ", "break", "suggest", "snooze"]
        test_frames = [
            VerbnetOfficialFrame(
                ['there', 'V', 'NP.Theme', verbnetprepclasses.prep["loc"], 'NP.Location'],
                "light_emission-43.1", []),
            VerbnetOfficialFrame(
                ["NP.Agent", "V", "NP.Theme"],
                "use-105", []),
            VerbnetOfficialFrame(
                ["NP.Patient", "V"],
                "break-45.1", []),
            VerbnetOfficialFrame(
                ["NP.Agent", "V", "how", "to", "S.Topic"],
                "say-37.7", []),
            VerbnetOfficialFrame(
                ["NP.Agent", "V"],
                "snooze-40.4", [])
        ]
        restrictions_str = {
            "sparkle":["(NOT animate)", "NORESTR"],
            "employ":["(animate) OR (organization)", "NORESTR"],
            "break":["solid"],
            "suggest":["(animate) OR (organization)", "communication"],
            "snooze":["animate"]
        }
        
        for verb, frame in zip(test_verbs, test_frames):
            self.assertIn(verb, reader.frames_for_verb)
            self.assertIn(frame, reader.frames_for_verb[verb])
            vnframe = reader.frames_for_verb[verb][reader.frames_for_verb[verb].index(frame)]
            self.assertEqual(
                [str(x) for x in vnframe.role_restrictions], restrictions_str[verb])
        
        reader.frames_for_verb = {}
        root = ET.ElementTree(file=str(paths.VERBNET_PATH / "separate-23.1.xml"))
        reader._handle_class(root.getroot(), [], [], [])
        
        list1 = [
            VerbnetOfficialFrame(
                ['NP.Agent', 'V', 'NP.Patient', {'from'}, 'NP.Co-Patient'],
                "separate-23.1", []),
            VerbnetOfficialFrame(['NP.Agent', 'V', 'NP.Patient'], "separate-23.1", []),
            VerbnetOfficialFrame(['NP.Patient', 'V'], "separate-23.1", []),
            VerbnetOfficialFrame(
                ['NP.Patient', 'V', {'from'}, 'NP.Co-Patient'],
                "separate-23.1", []),
            VerbnetOfficialFrame(['NP.Patient', 'V'], "separate-23.1", [])]
        list2 = [VerbnetOfficialFrame(
            ['NP.Patient', 'V', {'from'}, 'NP.Co-Patient'], "separate-23.1-1", [])]
        list3 = [VerbnetOfficialFrame(
            ['NP.Patient', 'V', {'with'}, 'NP.Co-Patient'], "separate-23.1-2", [])]
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
                print("Error with {}".format(verb))
                print('Expected')
                for data in expected_result[verb]:
                    print(data)
                print('Got')
                for data in reader.frames_for_verb[verb]:
                    print(data)
                print()
            
        self.assertEqual(reader.frames_for_verb, expected_result)
