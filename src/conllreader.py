#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Build syntactic trees from CoNLL parser output"""

import unittest

class ConllInvalidPositionError(Exception):
    """Trying to build a subtree from a node that does not exist
    
    :var bad_root: integer, the position from which we attempted to build a subtree
    :var max_root: integer, the last valid position
    
    """
    
    def __init__(self, bad_root, max_root):
        self.bad_root = bad_root
        self.max_root = max_root
        
    def __str__(self):
        return "Error : tried to build a subtree from position {} while"\
               " parsing CoNLL output (last valid position was {})".format(
                self.bad_root, self.max_root)
 
class SyntacticTreeNode:
    """A node (internal or terminal) of a syntactic tree
    
    :var word: string, the word contained by the node
    :var deprel: string, function attributed by the parser to this word
    :var children: -- SyntacticTreeNode list, the children of this node
    
    """
    
    def __init__(self, word, pos, deprel):
        self.word = word
        self.pos = pos
        self.deprel = deprel
        self.children = [] 

    def __str__(self):
        if self.children:
            children = " " + " ".join([str(t) for t in self.children])
        else:
            children = ""
        return "({}/{} {}{})".format(self.pos, self.deprel, self.word, children)


class SyntacticTreeBuilder():
    """Wrapper class for the building of a syntactic tree

    :var words: second column of the CoNLL output, list of words
    :var deprels: second line of the CoNLL output, list of deprels
    :var parents: third line of the CoNLL output, position of each word's parent
    
    """
    
    def __init__(self, conll_tree):
        """Extract the data provided 
        
        :param conll_tree: The output of the CoNLL parser
        :type conll_tree: str
        
        """
        self.words, self.deprels, self.pos, self.parents = [], [], [], []

        for l in conll_tree.splitlines():
            line_id, form, lemma, cpos, pos, feat, head, deprel, *junk = l.split("\t")
            self.words.append(form)
            self.deprels.append(deprel)
            self.pos.append(pos)
            self.parents.append(int(head))
    
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
            raise ConllInvalidPositionError(root, len(self.words) - 1)

        result = SyntacticTreeNode(self.words[root - 1], self.pos[root - 1],
                                   self.deprels[root - 1])

        next_child_pos = self.find_child_after(root, 1)
        while next_child_pos != None:
            result.children.append(self.build_tree_from(next_child_pos))
            next_child_pos = self.find_child_after(root, next_child_pos + 1)

        return result

class TreeBuilderTest(unittest.TestCase):
    def test_tree_builiding(self):
        conll_tree = """1	The	The	DT	DT	-	2	NMOD	-	-
2	others	others	NNS	NNS	-	5	SBJ	-	-
3	here	here	RB	RB	-	2	LOC	-	-
4	today	today	RB	RB	-	3	TMP	-	-
5	live	live	VV	VV	-	0	ROOT	-	-
6	elsewhere	elsewhere	RB	RB	-	5	LOC	-	-
7	.	.	.	.	-	5	P	-	-"""

        expected_result = "(VV/ROOT live (NNS/SBJ others (DT/NMOD The) (RB/LOC here (RB/TMP today))) (RB/LOC elsewhere) (./P .))"

        treeBuilder = SyntacticTreeBuilder(conll_tree)
        tree = treeBuilder.build_syntactic_tree()
        
        self.assertEqual(str(tree), expected_result)
        
import sys

if __name__ == '__main__':
    if len(sys.argv) == 1:
        unittest.main()
    else:
        with open(sys.argv[1]) as conll_file:
            conll_tree = ""
            for l in conll_file.readlines():
                if l != "\n":
                    conll_tree += l
                else:
                    print("\n\n")
                    print(conll_tree)
                    print(SyntacticTreeBuilder(conll_tree).build_syntactic_tree())
                    conll_tree = ""
                
