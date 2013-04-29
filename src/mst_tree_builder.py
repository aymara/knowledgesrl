#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
..module:: mst_tree_builder
    synopsis: Build syntactic trees from MST parser output
    
"""

import unittest

class MstInvalidPositionError(Exception):
    """Exception raised when trying to build a subtree
    from a node that does not exist
    
    Members:
    bad_root -- integer, the position from which we attempted to build a subtree
    max_root -- integer, the last valid position
    
    """
    
    def __init__(self, bad_root, max_root):
        self.bad_root = bad_root
        self.max_root = max_root
        
    def __str__(self):
        return "Error : tried to build a subtree from position "+format(self.bad_root)+\
                " while parsing MST output (last valid position was "+format(self.max_root)+")"
 
class SyntacticTreeNode:
    """A node (internal or terminal) of a syntactic tree
    
    Members:
    word -- string, the word contained by the node
    label -- string, function attributed by the parser to this word
    children -- SyntacticTreeNode list, the children of this node
    
    """
    
    def __init__(self, word, label):
        self.word = word
        self.label = label
        self.children = [] 

    def __str__(self):
        return "("+self.label+" "+self.word+" "+";".join([str(t) for t in self.children])+")"


class SyntacticTreeBuilder():
    """Wrapper class for the building of a syntactic tree

    Members:
    words -- first line of the MST output, list of words
    labels -- second line of the MST output, list of labels
    parents -- third line of the MST output, position of each word's parent
    """
    
    def __init__(self, mst_output):
        """Extract the data provided 
        
        :param mst_output: The output of the MST parser
        :type mst_output: str
        
        """
        (words_line, labels_line, parents_line) = mst_output.split("\n")
        self.words = words_line.split("\t")
        self.labels = labels_line.split("\t")
        self.parents = [int(n) for n in parents_line.split("\t")]
    
    def build_syntactic_tree(self):
        """ Build and return a the syntactic tree """
        return self.build_tree_from(0).children[0]

    def find_child_after(self, father, min_pos):
        """Search the position (real offset + 1) of a node's child after a given position
        
        :param father: The node of which we are looking for a child
        :type father: int
        :param min_pos: The position at or after which we are looking for a child
        :type min_pos: int
        :returns:  int -- the position of the child or None if no child was found
        """
        for i in range(min_pos - 1, len(self.parents)):
            if father == self.parents[i]:
                return i + 1

        return None

    def build_tree_from(self, root):
        """Builds a subtree rooted at a given node
        
        :param root: The position of the node used as the subtree root
        :type root: int
        :returns: SyntacticTreeNode -- the subtree
        
        """
        if root < 0 or root > len(self.words):
            raise MstInvalidPositionError(root, len(self.words) - 1)

        result = SyntacticTreeNode(self.words[root - 1], self.labels[root - 1])

        next_child_pos = self.find_child_after(root, 1)
        while next_child_pos != None:
            result.children.append(self.build_tree_from(next_child_pos))
            next_child_pos = self.find_child_after(root, next_child_pos + 1)

        return result

class TreeBuilderTest(unittest.TestCase):
    def test_tree_builiding(self):
        mst_input = \
        "the	sec	will	probably	vote	on	the	proposal	early	next"+\
        "	year	,	he	said	.\n\
        DEP	NP-SBJ	S	ADVP	VP	PP	DEP	NP	DEP	DEP	NP	DEP	NP-SBJ	ROOT	"+\
        "DEP\n\
        2	3	14	3	3	5	8	6	11	11	5	14	14	0	14"

        expected_result = "(ROOT said (S will (NP-SBJ sec (        DEP the ));(A"+\
        "DVP probably );(VP vote (PP on (NP proposal (DEP the )));(NP year (DEP "+\
        "early );(DEP next ))));(DEP , );(NP-SBJ he );(DEP . ))"

        treeBuilder = SyntacticTreeBuilder(mst_input)
        tree = treeBuilder.build_syntactic_tree()
        
        self.assertEqual(str(tree), expected_result)
        
if __name__ == '__main__':
    unittest.main()
