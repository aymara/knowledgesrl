#!/usr/bin/env python3

import unittest

from conllreader import SyntacticTreeBuilder
from argheuristic import find_args, build_relation_tree


class ArgHeuristicTest(unittest.TestCase):
    parsed_sentence = (
        "1	Your	Your	PRP$	PRP$	-	2	NMOD	-	-\n"
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
    
    def setUp(self):
        treeBuilder = SyntacticTreeBuilder(ArgHeuristicTest.parsed_sentence)
        self.initial_tree_list = treeBuilder.tree_list
        
    def test_relation_tree(self):
        expected = (
            "mean IDENTITY (more OBJ_DOWN (than AMOD_DOWN (may SUB_DOWN (you SB"
            "J_DOWN (), know VC_DOWN ()))), will VC_UP (contribution SBJ_DOWN ("
            "your NMOD_DOWN (), to NMOD_DOWN (goodwill IM_DOWN ())), . P_DOWN ("
            ")))"
        )
        
        relation_tree = build_relation_tree(self.initial_tree_list[0].children[1])
               
        self.assertEqual(str(relation_tree), expected)

    def test_rules(self):
        expected = set(["contribution", "more"])
        
        found = find_args(self.initial_tree_list[0].children[1])
        
        self.assertEqual(set([x.word for x in found]), expected)
