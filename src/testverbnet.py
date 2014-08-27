#!/usr/bin/env python3

import unittest
import verbnet

# TODO complete when unifying VerbNet parsing across projects
class VerbnetSyntax(unittest.TestCase):
    def test_equality(self):
        v1 = verbnet.Syntax([{'type': 'V'}])
        v2 = verbnet.Syntax([{'type': 'V'}])
        self.assertEqual(v1, v2)

