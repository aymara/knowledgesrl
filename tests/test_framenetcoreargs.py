#!/usr/bin/env python3

import unittest

from framenetcoreargs import CoreArgsFinder, NoSuchFrameError
import paths

class CoreArgsFinderTest(unittest.TestCase):
    def test_specific(self):
        core_args_finder = CoreArgsFinder()
        core_args_finder.load_data_from_xml(paths.Paths.framenet_frames("eng"))
        
        self.assertEqual(len(core_args_finder.core_args), 1019)
        
        frame = "Activity_abandoned_state"
        self.assertTrue(core_args_finder.is_core_role("Agent", frame))
        self.assertTrue(core_args_finder.is_core_role("Activity", frame))
        self.assertFalse(core_args_finder.is_core_role("Non_existing_role", frame))
        self.assertFalse(core_args_finder.is_core_role("Time", frame))
        self.assertFalse(core_args_finder.is_core_role("Duration", frame))
        
        with self.assertRaises(NoSuchFrameError):
            core_args_finder.is_core_role("Agent", "Non_existing_frame")
