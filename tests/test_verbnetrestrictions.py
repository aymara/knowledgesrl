#!/usr/bin/env python3

import unittest
from collections import Counter

from verbnetrestrictions import VNRestriction, NoHashDefaultDict


class VNRestrictionTest(unittest.TestCase):

    """Unit test class"""

    def test_restrictions(self):
        restr1 = VNRestriction.build("human")
        restr2 = VNRestriction.build("animal")
        restr3 = VNRestriction.build("solid")
        
        restr4 = VNRestriction.build_and(restr1, restr2)
        restr5 = VNRestriction.build_and(restr2, restr3)
        restr6 = VNRestriction.build_and(restr4, restr3)
        restr7 = VNRestriction.build_and(restr5, restr1)
        restr8 = VNRestriction.build_empty()
        restr8 = VNRestriction.build_or(restr8, restr7)
        
        self.assertEqual(restr6, restr7)
        self.assertNotEqual(restr4, restr5)
        subrestr = restr6.get_atomic_restrictions()
        self.assertEqual(subrestr, set(["human", "animal", "solid"]))
        self.assertTrue(str(restr8) == str(restr7))
        self.assertTrue(str(restr4) == "(human) AND (animal)")
        self.assertTrue(str(restr7) == "(animal) AND (solid) AND (human)")
        
    def test_scores(self):
        restr1 = VNRestriction.build("human")
        restr2 = VNRestriction.build("animal")
        
        restr3 = VNRestriction.build_or(restr1, restr2)
        restr4 = VNRestriction.build_and(restr1, restr2)
        restr5 = VNRestriction.build_not(restr3)
        restr6 = VNRestriction.build_empty()
        
        data = NoHashDefaultDict(lambda : Counter())
        data[restr1].update({"people":4, "president":10, "them":1})
        data[restr2].update({"dog":5, "cat":8, "them":2})
        data[restr3].update({"people":2})
        
        # Tests on basic restrictions
        self.assertEqual(restr1.match_score("people", data), 4)
        self.assertEqual(restr1.match_score("cat", data), 0)
        self.assertEqual(restr2.match_score("dog", data), 5)
        
        # OR relations must take the max score of the children
        self.assertEqual(restr3.match_score("president", data), 10)
        self.assertEqual(restr3.match_score("them", data), 2)
        # and use data explictly associated with them
        self.assertEqual(restr3.match_score("people", data), 6)
        
        # AND relations must take the min score of the children
        self.assertEqual(restr4.match_score("people", data), 0)
        
        # NOT relations must take the opposite score of their child
        self.assertEqual(restr5.match_score("people", data), -6)
        self.assertEqual(restr5.match_score("building", data), 1)
        
        self.assertEqual(restr6.match_score("building", data), 1 / 100)
