#!/usr/bin/env python3

import sys
sys.path.append('/home/cjaffre/knowledgesrl/src')


import unittest

from parsequality import get_quality_scores

class ParseQualityTest(unittest.TestCase):
    def test_score(self):
        correct, partial, total = get_quality_scores()
        # Must have elements to compute a fraction
        self.assertTrue(total > 0)
        # More than 75% of frame arguments should be exact subtrees from the
        # dependency parse
        self.assertTrue(correct/total > 0.75)
        # Subtrees from the dependency parse should match more than 90% of the
        # frame arguments
        self.assertTrue(partial/total > 0.90)
        
if __name__ == '__main__':
    unittest.main()
