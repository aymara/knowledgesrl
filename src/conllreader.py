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

# http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Longest_common_substring#Python
def LongestCommonSubstring(S1, S2):
    M = [[0]*(1+len(S2)) for i in range(1+len(S1))]
    longest, x_longest = 0, 0
    for x in range(1,1+len(S1)):
        for y in range(1,1+len(S2)):
            if S1[x-1] == S2[y-1]:
                M[x][y] = M[x-1][y-1] + 1
                if M[x][y]>longest:
                    longest = M[x][y]
                    x_longest  = x
            else:
                M[x][y] = 0
    return S1[x_longest-longest: x_longest]

class SyntacticTreeNode:
    """A node (internal or terminal) of a syntactic tree
    
    :var word: string, the word contained by the node
    :var position: position of the root among the children (0 is before)
    :var pos: part-of-speech of the node
    :var deprel: string, function attributed by the parser to this word
    :var children: -- SyntacticTreeNode list, the children of this node
    
    """
    
    def __init__(self, word, position, pos, deprel, begin, end, word_id, begin_head, children):
        self.word = word
        self.position = position
        self.pos = pos
        self.deprel = deprel
        self.children = children
        self.word_id = word_id
        self.begin = begin
        self.end = end
        self.begin_head = begin_head
        self.father = None
                
    def __iter__(self):
        for position, child in enumerate(self.children):
            if position == self.position: yield(self)
            for node in child:
                yield node
        if self.position == len(self.children): yield self
    
    def flat(self):
        """Return the tokenized sentence from the parse tree."""
        return " ".join([x.word for x in self])

    def contains(self, arg):
        """Search an exact argument in all subtrees"""
        return (self.flat() == arg or
            any((c.contains(arg) for c in self.children)))

    def closest_match(self, arg):
        """Search the closest match to arg"""
        return self.closest_match_as_node(arg).flat().split()

    def closest_match_as_node(self, arg):
        return self._closest_match_as_node_lcs(arg)[1]
        
    def _closest_match_as_node_lcs(self, arg):
        root_match = self.flat().split()
        root_match_len = (len(LongestCommonSubstring(root_match, arg.split())) /
                (len(root_match) + len(arg.split())))
        children_results = [c._closest_match_as_node_lcs(arg) for c in self.children]
        return max([(root_match_len, self)] + children_results, key = lambda x: x[0])
        
    def __str__(self):
        if self.children:
            children = " " + " ".join([str(t) for t in self.children])
        else:
            children = ""
        return "({}/{}/{}/{}/{} {}{})".format(self.pos, self.deprel, self.position, self.begin, self.end, self.word, children)

class SyntacticTreeBuilder():
    """Wrapper class for the building of a syntactic tree

    :var words: second column of the CoNLL output, list of words
    :var deprels: second column of the CoNLL output, list of deprels
    :var parents: third column of the CoNLL output, position of each word's parent
    
    """
    
    def __init__(self, conll_tree):
        """Extract the data provided
        
        :param conll_tree: The output of the CoNLL parser
        :type conll_tree: str
        
        """
        self.words, self.deprels, self.pos, self.parents = [], [], [], []
        self.word_begins = []
        self.word_ids = []
        
        begin = 0
        for l in conll_tree.splitlines():
            word_id, form, lemma, cpos, pos, feat, head, deprel, *junk = l.split("\t")
            
            self.word_ids.append(int(word_id))
            self.words.append(form)
            self.deprels.append(deprel)
            self.pos.append(cpos)
            self.parents.append(int(head))
            self.word_begins.append(begin)
            begin += 1 + len(form)
        
    def build_syntactic_tree(self):
        """ Build and return a the syntactic tree """
        result = self.build_tree_from(0).children[0]
        result.father = None
        return result

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

        root_position = 0
        children = []
        begin = self.word_begins[root - 1]
        end = begin + len(self.words[root - 1]) - 1

        next_child_pos = self.find_child_after(root, 1)
        while next_child_pos != None:
            if next_child_pos < root:
                root_position += 1

            child = self.build_tree_from(next_child_pos)
            children.append(child)
            if child.begin < begin: begin = child.begin
            if child.end > end: end = child.end
            next_child_pos = self.find_child_after(root, next_child_pos + 1)

        result = SyntacticTreeNode(self.words[root - 1], root_position,
                                 self.pos[root - 1], self.deprels[root - 1],
                                 begin, end, self.word_ids[root - 1], self.word_begins[root - 1], children)
        
        for child in result.children:
            child.father = result
                                 
        return result

class TreeBuilderTest(unittest.TestCase):

    def setUp(self):
        conll_tree = """1	The	The	DT	DT	-	2	NMOD	-	-
2	others	others	NNS	NNS	-	5	SBJ	-	-
3	here	here	RB	RB	-	2	LOC	-	-
4	today	today	RB	RB	-	3	TMP	-	-
5	live	live	VV	VV	-	0	ROOT	-	-
6	elsewhere	elsewhere	RB	RB	-	5	LOC	-	-
7	.	.	.	.	-	5	P	-	-"""
        treeBuilder = SyntacticTreeBuilder(conll_tree)
        self.tree = treeBuilder.build_syntactic_tree()
        self.assertEqual(self.tree.father, None)
    
    def test_tree_str(self):
        #The others here today live elsewhere .
        expected_str = "(VV/ROOT/1/0/37 live (NNS/SBJ/1/0/20 others (DT/NMOD/0/0/2 The) (RB/LOC/0/11/20 here (RB/TMP/0/16/20 today))) (RB/LOC/0/27/35 elsewhere) (./P/0/37/37 .))"
        
        self.assertEqual(str(self.tree), expected_str)
        self.assertEqual(self.tree.flat(), "The others here today live elsewhere .")

    def test_tree_contains(self):
        self.assertTrue(self.tree.contains("here today"))
        self.assertFalse(self.tree.contains("others here today"))

    def test_tree_match(self):
        self.assertEqual(self.tree.closest_match("others here today"),
                ['The', 'others', 'here', 'today'])
        
import sys

if __name__ == '__main__':
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
                
