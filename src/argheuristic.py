#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Implementation of the heuristic method that extract potential arguments
of a syntax-annotated sentence described in:
Lang & Lapata, 2011 "Unsupervised Semantic Role Induction via Split-Merge Clustering"
"""

from conllreader import SyntacticTreeBuilder
from functools import reduce
import unittest

class InvalidRelationError(Exception):
    """Exception raised when trying to build a relation with invalid keywords
    
    :var error_type: str -- the nature of the wrong keyword
    :var invalid_data: str -- the wrong keyword
    
    """
    
    def __init__(self, error_type, invalid_data):
        self.error_type = error_type
        self.invalid_data = invalid_data
        
    def __str__(self):
        return "Invalid {} : \"{}\"".format(self.error_type, self.invalid_data)



class Relation:
    """A syntactic relation between one node and its neighbour that is closer
    to the predicate. This can be an upward dependency if the node is the 
    governor of the relation or a downward dependency in the other case.
    
    :var name: str -- The name of the relation
    :var direction: str -- Indicates whether this is an upward or downward dependency
    
    """
    
    possible_names = {
        "ADV", "AMOD", "APPO", "BNF", "CONJ", "COORD", "DEP", "DIR", "DTV",
        "EXT", "EXTR", "GAP-LGS", "GAP-LOC", "IM", "LGS", "LOC", "LOC-PRD",
        "MNR", "NAME", "NMOD", "OBJ", "OPRD", "P", "PMOD", "POSTHON", "PRD",
        "PRN", "PRP", "PRT", "PUT", "ROOT", "SBJ", "SUB", "SUFFIX", "TITLE",
        "TMP", "VC", "VOC",
        # Last two were never encoutered in the corpus :
        "HMOD", "IOBJ"}

    possible_directions = {"UP", "DOWN"}
    
    def __init__(self, name, direction):
        if not direction in Relation.possible_directions:
            raise InvalidRelationError("direction", direction)
        if not name in Relation.possible_names:
            raise InvalidRelationError("name", name)
            
        self.name = name
        self.direction = direction
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.name == other.name and
            self.direction == other.direction)
    
    def __repr__(self):
        return "{}_{}".format(self.name, self.direction)
    
    @staticmethod
    def both(name):
        return [Relation(name, "UP"), Relation(name, "DOWN")]



class RelationTreeNode:
    """A node from a tree representation of a sentence, similar to
    a SyntacticTreeNode, except that the root is a given predicate, and that
    all nodes are annotated nwith their relation to their neighbour that is
    closer to the predicate.
    
    :var node: SyntacticTreeNode -- The matching SyntacticTreeNode
    :var children: RelationTreeNode List -- The children of the node in this
        particular representation
    :var relation: Relation -- The relation between the node and its neighbour
        that is closer to the predicate
    :var status: str -- UNKNOWN, KEPT or DISCARDED depending on whether the
        node is an argument
        
    """
    
    def __init__(self, node, children, relation):
        self.node = node
        self.children = children
        self.relation = relation
        self.status = "UNKNOWN"
    
    def __iter__(self):
        """ Iterate over all the subnodes (node itself is NOT included).
        No particular order is guaranteed.
        
        """
        
        for node in self._iter_all():
            if not node is self:
                yield node
    
    def _iter_all(self):
        for child in self.children:
            for node in child._iter_all():
                yield node
        yield self
    
    def __repr__(self):
        return "{} {} ({})".format(
            self.node.word, self.relation, ", ".join([str(x) for x in self.children]))
            
    def keep(self):
        if self.status == "UNKNOWN": self.status = "KEPT"
        
    def discard(self):
        if self.status == "UNKNOWN": self.status = "DISCARDED"



def build_relation_tree(node):
    """Transforms a SyntacticTreeNode into a RelationTreeNode
    
    :param node: The node which will be the root of the resulting tree
    :type node: SyntacticTreeNode
    :returns: RelationTreeNode -- The tree of relation corresponding to the node
    
    """
    
    # The root node gets the special relation "IDENTITY", but its relation
    # attribute is never actually read, except for debug purposes.
    return build_relation_tree_rec(node, node, "IDENTITY")

def build_relation_tree_rec(node, new_father, relation):
    """Recursivly build the subtree which starts at node
    
    :param node: The node from which we start to build the subtree
    :type node: SyntacticTreeNode
    :param new_father: The node that will be the father of this node in the new tree
    :type new_father: SyntacticTreeNode
    :param relation: The relation from ``new_father`` to ``node``
    :type relation: Relation
    
    """
    
    # Starts by the syntactic children (except new_father if it is one)
    new_children = [build_relation_tree_rec(x, node, Relation(x.deprel, "DOWN"))
            for x in node.children if not x is new_father]
    
    # The add the father if it is not new_father
    if not (new_father is node.father or node.father == None):
        new_children.append(build_relation_tree_rec(
            node.father, node, Relation(node.deprel, "UP")))
    
    return RelationTreeNode(node, new_children, relation)


# Determiner, coordinating conjunction and punctuation POS
# TO is missing because this is also the POS attributed to "to" when it is
# a preposition.
# The list of poncutation POS was obtained by extracting punctuation from
# the fulltext corpus and might therefore be incomplete
rule1_pos = ["CC", "DT", "``", "$", ")", "(", ",", ".", "''", ":"]

# Next two variables were set according to the appendix of the article
rule2_relations = (
    Relation.both("IM") + Relation.both("COORD") + Relation.both("P") +
    Relation.both("SUB") + [Relation("PRT", "DOWN"), Relation("OBJ", "UP"),
    Relation("PMOD", "UP"), Relation("ADV", "UP"), Relation("ROOT", "UP"),
    Relation("TMP", "UP"), Relation("SBJ", "UP"), Relation("OPRD", "UP")])
    
rule4_relations = reduce(lambda x,y: x + Relation.both(y), [
    "ADV", "AMOD", "APPO", "BNF", "CONJ", "COORD", "DIR", "DTV", "EXT", "EXTR",
    "HMOD", "IOBJ", "LGS", "LOC", "MNR", "NMOD", "OBJ", "OPRD", "POSTHON",
    "PRD", "PRN", "PRP", "PRT", "PUT", "SBJ", "SUB", "SUFFIX"
    ], [])

def find_args(predicate_node):
    """ Apply the heuristic to its argument
    
    :param predicate_node: The node from which we want potential arguments
    :type predicate_node: SyntacticTreeNode
    
    """
    
    # Build the relation tree
    tree = build_relation_tree(predicate_node)
    
    # Apply the 8 rules
    rule1(tree)
    rule2(tree)
    rule3(tree)
    rule4(tree)
    rule5(tree)
    rule6(tree)
    rule7(tree)
    rule8(tree)
    
    # At this point, all nodes are marked as "KEPT" or "DISCARDED"
    # Returns every node marked as "KEPT"
    
    # But first, discard nodes which have children which are also candidate arguments
    arg_list = [x for x in tree if x.status == "KEPT"]
    for arg_node in arg_list:
        for subnode in arg_node:
            if subnode in arg_list:
                arg_node.status = "DISCARDED"
                break
    
    return [x.node for x in tree if x.status == "KEPT"]

def rule1(tree):
    for elem in tree:
        if elem.node.pos in rule1_pos:
            elem.discard()

def rule2(tree):
    for elem in tree:
        if elem.relation in rule2_relations:
            elem.discard()

def rule3(tree):
    candidate = None
    best_position = -1
    
    for elem in tree:
        if (elem.node.deprel == "SBJ" and
            elem.node.begin_head < tree.node.begin_head and
            elem.node.begin_head > best_position
        ):
            candidate, best_position = elem, elem.node.begin
    
    if candidate == None: return
            
    found = False
    node = tree.node
    while node != None:
        if node.begin_head == candidate.node.father.begin_head:
            found = True
            break
        node = node.father
        
    if found: candidate.keep()

def rule4(tree):
    for elem1 in tree.children:
        if elem1.relation in rule4_relations:
            for elem2 in elem1: elem2.discard()
        else:
            rule4(elem1)
    
def rule5(tree):
    for elem in tree:
        if any([x.deprel == "VC" for x in elem.node.children]):
            elem.discard()

def rule6(tree):
    for elem in tree.children:
        if not elem is tree.node.father:
            elem.keep()

def rule7(tree, root = True):
    for elem in tree.children:
        if elem.relation.name == "VC":
            rule7(elem, False)
        elif not root:
            elem.keep()

def rule8(tree):
    for elem in tree: elem.discard()



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
        self.initial_tree = treeBuilder.build_syntactic_tree()
        
    def test_relation_tree(self):
        expected = (
            "mean IDENTITY (more OBJ_DOWN (than AMOD_DOWN (may SUB_DOWN (you SB"
            "J_DOWN (), know VC_DOWN ()))), will VC_UP (contribution SBJ_DOWN ("
            "Your NMOD_DOWN (), to NMOD_DOWN (Goodwill IM_DOWN ())), . P_DOWN ("
            ")))"
        )
        
        relation_tree = build_relation_tree(self.initial_tree.children[1]) 
               
        self.assertEqual(str(relation_tree), expected)

    def test_rules(self):
        expected = set(["contribution", "more"])
        
        found = find_args(self.initial_tree.children[1])
        
        self.assertEqual(set([x.word for x in found]), expected)
        

if __name__ == "__main__":
    unittest.main()
