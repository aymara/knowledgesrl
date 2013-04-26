#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mst_tree_builder

test_input = \
"the	sec	will	probably	vote	on	the	proposal	early	next	year	,	he	said	.\n\
DEP	NP-SBJ	S	ADVP	VP	PP	DEP	NP	DEP	DEP	NP	DEP	NP-SBJ	ROOT	DEP\n\
2	3	14	3	3	5	8	6	11	11	5	14	14	0	14"

test_expected_result = "(S will (NP-SBJ sec (DEP the ));(ADVP probably );(VP vote (PP on (NP proposal (DEP the )));(NP year (DEP early );(DEP next ))))"

treeBuilder = mst_tree_builder.SyntacticTreeBuilder(test_input)
tree = treeBuilder.build_syntactic_tree()

if test_expected_result == str(tree.children[0]):
	print("Success")
else:
	print("Test failed")
