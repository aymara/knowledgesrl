#!/usr/bin/env python3

import unittest

from conllreader import SyntacticTreeBuilder


class TreeBuilderTest(unittest.TestCase):

    def setUp(self):
        conll_tree = \
"""1	The	The	DT	DT	-	2	NMOD	-	-
2	others	others	NNS	NNS	-	5	SBJ	-	-
3	here	here	RB	RB	-	2	LOC	-	-
4	today	today	RB	RB	-	3	TMP	-	-
5	live	live	VV	VV	-	0	ROOT	-	-
6	elsewhere	elsewhere	RB	RB	-	5	LOC	-	-
7	.	.	.	.	-	5	P	-	-"""
        treeBuilder = SyntacticTreeBuilder(conll_tree)
        self.tree_list = treeBuilder.tree_list

    def test_none_fathers(self):
        for tree in self.tree_list:
            self.assertEqual(tree.father, None)

    def test_tree_str(self):
        #The others here today live elsewhere .
        expected_str = "(VV/ROOT/1/0/37 live (NNS/SBJ/1/0/20 others (DT/NMOD/0/0/2 The) (RB/LOC/0/11/20 here (RB/TMP/0/16/20 today))) (RB/LOC/0/27/35 elsewhere) (./P/0/37/37 .))"
        self.assertEqual(str(self.tree_list[0]), expected_str)

    def test_tree_flat(self):
        self.assertEqual(self.tree_list[0].flat(), "The others here today live elsewhere .")

    def test_tree_contains(self):
        self.assertTrue(self.tree_list[0].contains("here today"))
        self.assertFalse(self.tree_list[0].contains("others here today"))

    def test_lima_tree(self):
        conll_tree = \
"""1	Jamaica	Jamaica	NNP	NNP	-	2	SUB	-	-
2	is	be	VBZ	VBZ	-	-	-	-	-
3	not	not	NOT	NOT	-	2	VMOD	-	-
4	just	just	RB	RB	-	-	-	-	-
5	a	a	DT	DT	-	6	NMOD	-	-
6	destination	destination	NN	NN	-	2	OBJ 	-	-
7	it	it	PRP	PRP	-	8	SUB	-	-
8	is	be	VBZ	VBZ	-	6	NMOD	-	-
9	an	a	DT	DT	-	10	NMOD	-	-
10	experience	experience	NN	NN	-	8	OBJ 	-	-"""

        treeBuilder = SyntacticTreeBuilder(conll_tree)
        for tree in treeBuilder.tree_list:
            self.assertEqual(tree.father, None)
            print(str(tree))

    def test_another_flat(self):
        conll_tree = \
"""1	a	a	DT	DT	-	3	NMOD	-	-
2	few	few	JJ	JJ	-	3	NMOD	-	-
3	months	months	NNS	NNS	-	4	AMOD	-	-
4	ago	ago	IN	IN	-	6	VMOD	-	-
5	you	you	PRP	PRP	-	6	SUB	-	-
6	received	received	VBD	VBD	-	0	ROOT	-	-
7	a	a	DT	DT	-	8	NMOD	-	-
8	letter	letter	NN	NN	-	6	OBJ	-	-"""
        self.assertEqual(SyntacticTreeBuilder(conll_tree).tree_list[0].flat(), 'a few months ago you received a letter')
