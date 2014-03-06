#!/usr/bin/env python3

import unittest
import verbnet

class VerbnetFrameTest(unittest.TestCase):
    def test_equality(self):
        v1 = verbnet.Syntax([{'type': 'V'}])
        v2 = verbnet.Syntax([{'type': 'V'}])
        self.assertEqual(v1, v2)

