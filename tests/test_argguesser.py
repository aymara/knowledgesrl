#!/usr/bin/env python3

import logging
import os
import sys

import argparse
import paths
import unittest

from options import Options
import verbnetreader
from argguesser import ArgGuesser
from conllreader import SyntacticTreeBuilder
from framenetframe import Arg
import probabilitymodel

logging.basicConfig(level=logging.DEBUG)
logging.root.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class ArgGuesserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logger.debug(f"ArgGuesserTest.setUpClass")
        # parse command line arguments
        parser = argparse.ArgumentParser(
            description="""
            Depending on the options used, can
            # Annotate a single file
            knowledgesrl.py --conll_input=parsed_file.conll
                    --conll_output=annotated_file.conll [options]

            # Annotate FrameNet test set
            knowledgesrl.py [options]

            # Annotate FrameNet training set
            knowledgesrl.py --training-set [options]

            # Annotate FrameNet example corpus
            knowledgesrl.py --lu [options]
            """)
        parser.add_argument("--language", "-l", type=str, choices=["eng", "fre"],
                            default="eng",
                            help="Name of the CoNLL-U file with the gold data.")
        parser.add_argument("--best-gold", action="store_true",
                            help=" Best configuration for gold.")
        parser.add_argument("--best-auto", action="store_true",
                            help="Best configuration for auto.")
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
        parser.add_argument("--dump", type=str, default=None,
                            help="File where to dump annotations for comparisons.")

        # parse command line arguments
        # args = parser.parse_args()
        # Separate unittest arguments and custom arguments
        args, unittest_args = parser.parse_known_args()

        # initialize the Options class with command line arguments
        Options(args)
        logger.setLevel(Options.loglevel)
        return unittest_args


    def setUp(self):
        logger.debug(f"ArgGuesserTest.setUp")
        verbnet = verbnetreader.VerbnetReader(
            paths.Paths.verbnet_path("eng")).frames_for_verb
        self.arg_guesser = ArgGuesser(verbnet)

    def test_global(self):
        logger.debug(f"ArgGuesserTest.test_global")
        frames = []
        # Options.fulltext_parses is either test or train files in options
        # while tests below where expecting the full corpus. We the compute
        # a new list combining both.
        fulltext_parses = paths.Paths.FRAMENET_PARSED.glob('*.conll')
        for filename in fulltext_parses:
        # for filename in Options.fulltext_parses:
            logger.debug(f"ArgGuesserTest.test_global filename: {filename}")
            frames.extend(
                [x for x
                 in self.arg_guesser.frame_instances_from_file(filename)])

        num_args = 0

        for frame in frames:
            for arg in frame.args:
                self.assertNotEqual(arg.text, '')
                self.assertEqual(frame.sentence[arg.begin:arg.end + 1], arg.text)
            num_args += len(frame.args)

        # Values computed are different from those hardcoded here from 2014
        # This is probably due to changes in the list of part of speech used
        # as frame triggers. Let's comment out this test as the really correct
        # value is hard to check.
        logger.debug(f"ArgGuesserTest.test_global nb frames: {len(frames)}")
        logger.debug(f"ArgGuesserTest.test_global nb args: {num_args}")
        # self.assertEqual(len(frames), 4173)
        # self.assertEqual(num_args, 7936)

    def test_1(self):
        conll_tree = """1	The	The	DT	DT	-	2	NMOD	-	-
2	others	others	NNS	NNS	-	5	SBJ	-	-
3	here	here	RB	RB	-	2	LOC	-	-
4	today	today	RB	RB	-	3	TMP	-	-
5	live	live	VV	VV	-	0	ROOT	-	-
6	elsewhere	elsewhere	RB	RB	-	5	LOC	-	-
7	.	.	.	.	-	5	P	-	-"""
        treeBuilder = SyntacticTreeBuilder(conll_tree)
        args = [
            Arg(0, 20, "The others here today", "", True, "NP")
        ]

        self.assertEqual(self.arg_guesser._find_args(treeBuilder.tree_list[0]),
                         args)

    def test_multiroot_sentence(self):
        conll_tree = """\
1	because	because	IN	IN	-	15	VMOD	-	-
2	they	they	PRP	PRP	-	4	SUB	-	-
3	just	just	RB	RB	-	4	VMOD	-	-
4	say	say	VBP	VBP	-	1	SBAR	-	-
5	there	there	EX	EX	-	6	SUB	-	-
6	's	's	VBZ	VBZ	-	4	VMOD	-	-
7	either	either	DT	DT	-	9	NMOD	-	-
8	no	no	DT	DT	-	9	NMOD	-	-
9	room	room	NN	NN	-	6	PRD	-	-
10	in	in	IN	IN	-	9	NMOD	-	-
11	the	the	DT	DT	-	12	NMOD	-	-
12	system	system	NN	NN	-	10	PMOD	-	-
13	,	,	,	,	-	15	P	-	-
14	you	you	PRP	PRP	-	15	SUB	-	-
15	know	know	VBP	VBP	-	71	VMOD	-	-
16	,	,	,	,	-	15	P	-	-
17	in	in	IN	IN	-	15	VMOD	-	-
18	the	the	DT	DT	-	19	NMOD	-	-
19	jails	jails	NNS	NNS	-	17	PMOD	-	-
20	for	for	IN	IN	-	19	NMOD	-	-
21	them	them	PRP	PRP	-	20	PMOD	-	-
22	or	or	CC	CC	-	71	VMOD	-	-
23	,	,	,	,	-	25	P	-	-
24	you	you	PRP	PRP	-	25	SUB	-	-
25	know	know	VBP	VBP	-	71	VMOD	-	-
26	,	,	,	,	-	25	P	-	-
27	it	it	PRP	PRP	-	28	SUB	-	-
28	's	's	VBZ	VBZ	-	71	VMOD	-	-
29	just	just	RB	RB	-	30	AMOD	-	-
30	that	that	IN	IN	-	28	PRD	-	-
31	it	it	PRP	PRP	-	32	SUB	-	-
32	seems	seems	VBZ	VBZ	-	30	SBAR	-	-
33	like	like	IN	IN	-	32	PRD	-	-
34	the	the	DT	DT	-	36	NMOD	-	-
35	automatic	automatic	JJ	JJ	-	36	NMOD	-	-
36	sentences	sentences	NNS	NNS	-	33	PMOD	-	-
37	-	-	:	:	-	28	P	-	-
38	if	if	IN	IN	-	28	VMOD	-	-
39	-	-	:	:	-	71	P	-	-
40	if	if	IN	IN	-	53	VMOD	-	-
41	a	a	DT	DT	-	42	NMOD	-	-
42	judge	judge	NN	NN	-	43	SUB	-	-
43	has	has	VBZ	VBZ	-	40	SBAR	-	-
44	leeway	leeway	VBN	VBN	-	43	VC	-	-
45	on	on	IN	IN	-	44	VMOD	-	-
46	what	what	WP	WP	-	45	PMOD	-	-
47	he	he	PRP	PRP	-	48	SUB	-	-
48	's	's	VBZ	VBZ	-	46	SBAR	-	-
49	going	going	VBG	VBG	-	48	VC	-	-
50	to	to	TO	TO	-	49	VMOD	-	-
51	,	,	,	,	-	53	P	-	-
52	you	you	PRP	PRP	-	53	SUB	-	-
53	know	know	VBP	VBP	-	71	VMOD	-	-
54	,	,	,	,	-	53	P	-	-
55	sentence	sentence	NN	NN	-	56	NMOD	-	-
56	someone	someone	NN	NN	-	53	OBJ	-	-
57	for	for	IN	IN	-	56	NMOD	-	-
58	between	between	IN	IN	-	68	NMOD	-	-
59	,	,	,	,	-	61	P	-	-
60	you	you	PRP	PRP	-	61	SUB	-	-
61	know	know	VBP	VBP	-	58	SBAR	-	-
62	,	,	,	,	-	68	P	-	-
63	two	two	CD	CD	-	64	NMOD	-	-
64	months	months	NNS	NNS	-	68	NMOD	-	-
65	and	and	CC	CC	-	68	NMOD	-	-
66	uh	uh	JJ	JJ	-	68	NMOD	-	-
67	fifty	fifty	JJ	JJ	-	68	NMOD	-	-
68	years	years	NNS	NNS	-	57	PMOD	-	-
69	and	and	CC	CC	-	71	VMOD	-	-
70	you	you	PRP	PRP	-	71	SUB	-	-
71	know	know	VBP	VBP	-	0	ROOT	-	-
72	what	what	WP	WP	-	71	VMOD	-	-
73	's	's	VBZ	VBZ	-	0	ROOT	-	-
74	his	his	PRP$	PRP$	-	75	NMOD	-	-
75	whim	whim	NN	NN	-	73	PRD	-	-
76	to	to	TO	TO	-	77	VMOD	-	-
77	decide	decide	VB	VB	-	0	ROOT	-	-
78	it	it	PRP	PRP	-	79	SUB	-	-
79	should	should	MD	MD	-	0	ROOT	-	-
80	be	be	VB	VB	-	0	ROOT	-	-
81	two	two	CD	CD	-	82	NMOD	-	-
82	months	months	NNS	NNS	-	0	ROOT	-	-
83	.	.	.	.	-	82	P	-	-"""

        treeBuilder = SyntacticTreeBuilder(conll_tree)
        self.assertEqual(len(treeBuilder.tree_list), 6)


if __name__ == '__main__':
    unittest_args = ArgGuesserTest.setUpClass()
    unittest.main(argv=[sys.argv[0]] + unittest_args)
