#!/usr/bin/env python3

import argparse
import logging
import sys
import unittest

from argheuristic import find_args, build_relation_tree # type: ignore
from conllreader import SyntacticTreeBuilder # type: ignore
from options import Options

logging.basicConfig(level=logging.DEBUG)
logging.root.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class ArgHeuristicTest(unittest.TestCase):
    parsed_sentence = (
        "1	Your	your	PRP$	PRP$	-	2	NMOD	-	-\n"
        "2	contribution	contribution	NN	NN	-	5	SBJ	-	-\n"
        "3	to	to	TO	TO	-	2	NMOD	-	-\n"
        "4	Goodwill	Goodwill	NNP	NNP	-	3	IM	-	-\n"
        "5	will	will	MD	MD	-	0	ROOT	-	-\n"
        "6	mean	mean	VB	VB	-	5	VC	-	-\n"
        "7	more	more	JJR	JJR	-	6	OBJ	-	-\n"
        "8	than	than	IN	IN	-	7	AMOD	-	-\n"
        "9	you	you	PRP	PRP	-	10	SBJ	-	-\n"
        "10	may	may	MD	MD	-	8	SUB	-	-\n"
        "11	know	know	VB	VB	-	10	VC	-	-\n"
        "12	.	.	.	.	-	5	P	-	-")

    @classmethod
    def setUpClass(cls):
        logger.debug(f"ArgHeuristicTest.setUpClass")
        # parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("--loglevel", type=str,
                            choices=['debug', 'info', 'warning', 'error',
                                    'critical'],
                            default='warning',
                            help="Log level.")

        # Separate unittest arguments and custom arguments
        args, unittest_args = parser.parse_known_args()

        # initialize the Options class with command line arguments
        Options(args)
        logger.setLevel(Options.loglevel)
        return unittest_args

    def setUp(self):
        treeBuilder = SyntacticTreeBuilder(ArgHeuristicTest.parsed_sentence)
        self.initial_tree_list = treeBuilder.tree_list

    def test_relation_tree(self):
        expected = (
            "mean IDENTITY (more OBJ_DOWN (than AMOD_DOWN (may SUB_DOWN (you SBJ_DOWN (), know VC_DOWN ()))), will VC_UP (contribution SBJ_DOWN (Your NMOD_DOWN (), to NMOD_DOWN (Goodwill IM_DOWN ())), . P_DOWN ()))"
        )

        relation_tree = build_relation_tree(
            self.initial_tree_list[0].children[1])
        logger.debug(f"ArgHeuristicTest.test_relation_tree relation_tree:\n"
                     f"{str(relation_tree)}")
        self.assertEqual(str(relation_tree), expected)

    def test_rules(self):
        expected = set(["contribution", "more"])

        found = find_args(self.initial_tree_list[0].children[1])

        self.assertEqual(set([x.word for x in found]), expected)

if __name__ == '__main__':
    unittest_args = ArgHeuristicTest.setUpClass()
    unittest.main(argv=[sys.argv[0]] + unittest_args)
