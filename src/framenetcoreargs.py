#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import xml.etree.ElementTree as ET
import os
import paths


class NoSuchFrameError(Exception):
    """ Trying to determine if a role is a core role of a frame that does not exist.
    
    :var frame: str, the frame that does not exist.
    """
    
    def __init__(self, frame):
        self.frame = frame
        
    def __str__(self):
        return ("is_core_role : no data for frame '{}'.".format(self.frame))

class CoreArgsFinder:
    """This class reads data from FrameNet and sued them to distinguishe core args from other args.
    
    :var core_args: str List Dictionnary -- The list of core args for each frame.
    """
    def __init__(self):
        self._xmlns = "{http://framenet.icsi.berkeley.edu}"
        self.core_args = {}
    
    def load_data_from_xml(self, dirname):
        """Retrieve the data from the XML FrameNet files.
        
        :param dirname: The path to the XML files.
        :type dirname: str.
        
        """
        for filename in dirname.glob('*.xml'):
            root = ET.ElementTree(file=str(filename.resolve())).getroot()

            self.core_args[root.attrib["name"]] = []
            for arg_data in root.findall(self._xmlns+"FE[@coreType]"):
                if arg_data.attrib["coreType"] in ["Core", "Core-Unexpressed"]:
                    self.core_args[root.attrib["name"]].append(
                        arg_data.attrib["name"])
        
    def is_core_role(self, role, frame):
        """Tells whether a role is a core role of a frame
        
        :param arg: The role to test.
        :type arg: str.
        :param frame: The frame in which the argument occurs.
        :type frame: str.
        :returns bool: True if the role was a core role, False otherwise.
        
        """
        if not frame in self.core_args:
            raise NoSuchFrameError(frame)
            
        return role in self.core_args[frame]

class CoreArgsFinderTest(unittest.TestCase):
    def test_specific(self):
        core_args_finder = CoreArgsFinder()
        core_args_finder.load_data_from_xml(paths.FRAMENET_FRAMES)
        
        self.assertEqual(len(core_args_finder.core_args), 1019)
        
        frame = "Activity_abandoned_state"
        self.assertTrue(core_args_finder.is_core_role("Agent", frame))
        self.assertTrue(core_args_finder.is_core_role("Activity", frame))
        self.assertFalse(core_args_finder.is_core_role("Non_existing_role", frame))
        self.assertFalse(core_args_finder.is_core_role("Time", frame))
        self.assertFalse(core_args_finder.is_core_role("Duration", frame))
        
        with self.assertRaises(NoSuchFrameError):
            core_args_finder.is_core_role("Agent", "Non_existing_frame")
