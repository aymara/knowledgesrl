#!/usr/bin/env python3
import logging
import sys
import trace
import unittest
import options

from conllreader import SyntacticTreeBuilder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.root.setLevel(logging.DEBUG)

logger.setLevel(options.Options.loglevel)

class TreeBuilderTest(unittest.TestCase):

    def setUp(self):
        logger.debug('setUp')
        conll_tree = """\
1	The	the	DT	DT	-	2	NMOD	-	-
2	others	others	NNS	NNS	-	5	SBJ	-	-
3	here	here	RB	RB	-	2	LOC	-	-
4	today	today	RB	RB	-	3	TMP	-	-
5	live	live	VV	VV	-	0	ROOT	-	-
6	elsewhere	elsewhere	RB	RB	-	5	LOC	-	-
7	.	.	.	.	-	5	P	-	-"""
        treeBuilder = SyntacticTreeBuilder(conll_tree)
        self.tree_list = treeBuilder.tree_list

    def test_none_fathers(self):
        logger.debug('test_none_fathers')
        for tree in self.tree_list:
            self.assertEqual(tree.father, None)

    def test_tree_str(self):
        logger.debug('test_tree_str')
        #The others here today live elsewhere .
        expected_str = "(VV/ROOT/1/0/37 live (NNS/SBJ/1/0/20 others (DT/NMOD/0/0/2 the) (RB/LOC/0/11/20 here (RB/TMP/0/16/20 today))) (RB/LOC/0/27/35 elsewhere) (./P/0/37/37 .))"
        self.assertEqual(str(self.tree_list[0]), expected_str)

    def test_tree_flat(self):
        logger.debug('test_tree_flat')
        self.assertEqual(self.tree_list[0].flat(), "The others here today live elsewhere .")

    def test_tree_contains(self):
        logger.debug('test_tree_contains')
        self.assertTrue(self.tree_list[0].contains("here today"))
        self.assertFalse(self.tree_list[0].contains("others here today"))

    def test_lima_tree(self):
        logger.debug('test_lima_tree')
        conll_tree = \
"""1	Jamaica	Jamaica	NNP	NNP	-	2	SUB	-	-
2	is	be	VBZ	VBZ	-	-	-	-	-
3	not	not	NOT	NOT	-	2	VMOD	-	-
4	just	just	RB	RB	-	6	NMOD	-	-
5	a	a	DT	DT	-	6	NMOD	-	-
6	destination	destination	NN	NN	-	2	OBJ 	-	-
7	it	it	PRP	PRP	-	8	SUB	-	-
8	is	be	VBZ	VBZ	-	6	NMOD	-	-
9	an	a	DT	DT	-	10	NMOD	-	-
10	experience	experience	NN	NN	-	8	OBJ 	-	-"""

        treeBuilder = SyntacticTreeBuilder(conll_tree)
        for tree in treeBuilder.tree_list:
            self.assertEqual(tree.father, None)

    def test_another_flat(self):
        logger.debug('test_another_flat')
        conll_tree = """\
1	a	a	DT	DT	-	3	NMOD	-	-
2	few	few	JJ	JJ	-	3	NMOD	-	-
3	months	months	NNS	NNS	-	4	AMOD	-	-
4	ago	ago	IN	IN	-	6	VMOD	-	-
5	you	you	PRP	PRP	-	6	SUB	-	-
6	received	received	VBD	VBD	-	0	ROOT	-	-
7	a	a	DT	DT	-	8	NMOD	-	-
8	letter	letter	NN	NN	-	6	OBJ	-	-"""
        self.assertEqual(
            SyntacticTreeBuilder(conll_tree).tree_list[0].flat(),
            'a few months ago you received a letter')

    def test_another_other_flat(self):
        logger.debug('test_another_other_flat')
        conll_tree = """\
1	Jamaica	Jamaica	NNP	NNP	-	2	SUB	-	-
2	is	be	VBZ	VBZ	-	-	-	-	-
3	not	not	NOT	NOT	-	2	VMOD	-	-
4	just	just	RB	RB	-	6	NMOD	-	-
5	a	a	DT	DT	-	6	NMOD	-	-
6	destination	destination	NN	NN	-	2	OBJ	-	-
7	it	it	PRP	PRP	-	8	SUB	-	-
8	is	be	VBZ	VBZ	-	6	NMOD	-	-
9	an	a	DT	DT	-	10	NMOD	-	-
10	experience	experience	NN	NN	-	8	OBJ	-	-"""
        logger.debug(f"lala : {SyntacticTreeBuilder(conll_tree).tree_list[0]}")
        self.assertEqual(
            SyntacticTreeBuilder(conll_tree).tree_list[0].flat(),
            'Jamaica is not just a destination it is an experience')


if __name__ == '__main__':
    ### NEW Pour comprendre ce qu'il se passe ###
    #tracer = trace.Trace(trace=True, count = False)
    #tracer.run('unittest.main()')
    ### END NEW

    unittest.main()
