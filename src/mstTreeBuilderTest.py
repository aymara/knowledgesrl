testInput = \
"the	sec	will	probably	vote	on	the	proposal	early	next	year	,	he	said	.\n\
DEP	NP-SBJ	S	ADVP	VP	PP	DEP	NP	DEP	DEP	NP	DEP	NP-SBJ	ROOT	DEP\n\
2	3	14	3	3	5	8	6	11	11	5	14	14	0	14"

testExpectedResult = "(S will (NP-SBJ sec (DEP the ));(ADVP probably );(VP vote (PP on (NP proposal (DEP the )));(NP year (DEP early );(DEP next ))))"

import mstTreeBuilder
tree = mstTreeBuilder.buildSyntacticTree(testInput)

if testExpectedResult == tree.children[0].toString():
	print("Success")
else:
	print("Test failed")
