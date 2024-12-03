#!/usr/bin/env python3

import argparse
import logging
import sys
import unittest

import probabilitymodel
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
        parser.add_argument("--matching-algorithm", type=str,
                            choices=["baseline", "sync_predicates",
                                    "stop_on_fail"],
                            default="sync_predicates",
                            help="Select a frame matching algorithm.")
        parser.add_argument("--add-non-core-args", action="store_true",
                            help="Consider non-core-arg with gold arguments (why?)")
        parser.add_argument("--model", type=str,
                            choices=probabilitymodel.models,
                            help="Probability models.")
        parser.add_argument("--bootstrap", action="store_true",
                            help="")
        parser.add_argument("--no-argument-identification", action="store_true",
                            help="Identify arguments automatically")
        parser.add_argument("--heuristic-rules", action="store_true",
                            help="Use Lang and Lapata heuristics to find args.")
        parser.add_argument("--passivize", action="store_true",
                            help="Handle passive sentences")
        parser.add_argument("--semantic-restrictions", action="store_true",
                            help="Restrict to phrases that obey VerbNet restrictions")
        parser.add_argument("--wordnet-restrictions", action="store_true",
                            help="Restrict to phrases that obey WordNet restrictions")
        # what do we annotate?
        parser.add_argument("--conll-input", "-i", type=str, default="",
                            help="File to annotate.")
        parser.add_argument("--conll-output", "-o", type=str, default=None,
                            help="File to write result on. Default to stdout.")
        parser.add_argument("--corpus", type=str,
                            choices=["FrameNet", "dicoinfo_fr"],
                            default=None,
                            help="")
        parser.add_argument("--training-set", action="store_true", default=True,
                            help="To annotate FrameNet training set.")
        parser.add_argument("--lu", action="store_true",
                            help="To annotate FrameNet example corpus.")
        # what kind of output do we want
        parser.add_argument("--frame-lexicon", type=str,
                            choices=["VerbNet", "FrameNet"],
                            default="VerbNet",
                            help="Chose frame lexicon to use for output.")
        # meta
        parser.add_argument("--loglevel", type=str,
                            choices=['debug', 'info', 'warning', 'error',
                                    'critical'],
                            default='warning',
                            help="Log level.")

        # parse command line arguments
        # args = parser.parse_args()
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
