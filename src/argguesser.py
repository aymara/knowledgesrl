#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Extract frames, predicates and arguments from a corpus, using only syntactic annotations """

import unittest
import paths
import os

from framestructure import FrameInstance, Predicate, Word, Arg
import verbnetreader
from framenetparsedreader import FNParsedReader
from framenetallreader import FNAllReader
import options
from conllreader import SyntacticTreeBuilder
from verbnetprepclasses import all_preps
from argheuristic import find_args
from nltk.corpus import wordnet as wn


class ArgGuesser(FNParsedReader):
    """
    :var frames_for_verb: lemma -> VerbnetOfficialFrame list - Used to know which predicates are in VerbNet.
    :var filename: str -- The name of the current CoNLL file.
    """
    
    predicate_pos = ["MD", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]

    subject_deprels = [
    "LGS", #Logical subject -> should we keep this (36 args) ?
    "SBJ", "SUB"
    ]
    
    non_core_deprels = [
    "DIR", "EXT", "LOC",
    "MNR", "PRP", "PUT", "TMP"
    ]
        
    args_deprels = subject_deprels + [
    "DIR",
    "BNF", #the 'for' phrase for verbs that undergo dative shift
    "DTV", #the 'to' phrase for verbs that undergo dative shift
    "OBJ", #direct or indirect object or clause complement
    "OPRD",#object complement
    "PRD", #predicative complement
    "VMOD"
    ]
    
    # Source : http://www.comp.leeds.ac.uk/ccalas/tagsets/upenn.html
    pos_conversions = {
    "$":"NP",
    "CD":"NP", #Cardinal number ("The three of us")
    "DT":"NP", #Determiner ("this" or "that")
    "JJ":"ADJ",
    "JJR":"NP", #Comparative
    "JJS":"NP", #Superlative
    "MD":"S", #Modal verb
    "NN":"NP", "NNP":"NP", "NNPS": "NP", "NNS":"NP",
    "NP":"NP", "NPS":"NP",
    "PP":"PP",
    "PRP":"NP",
    "RB":"ADV",
    "TO":"to S",
    "VB":"S", #Base form of a verb
    "VBD":"S", "VBG":"S_ING",
    "VBN":"ADJ", #Participe, as "fed" in "He got so fed up that..."
    "VBP":"S", "VBZ":"S",
    "WDT":"NP" #Relative determiners ("that what whatever which whichever")
    }
    
    acceptable_pt = ["NP", "PP", "S_ING", "S"]
    
    complex_pos = ["IN", "WP"]

    def __init__(self, frames_for_verb):
        FNParsedReader.__init__(self)
        self.frames_for_verb = frames_for_verb
        
    def frame_instances_from_file(self, filename):
        """ Extracts frames from one file and iterate over them """
        self.load_file(filename)
        for sentence_id, sentence, tree in self.sentence_trees():
            for frame in self._handle_sentence(sentence_id, sentence, tree, filename):
                yield frame
    
    def _handle_sentence(self, sentence_id, sentence, tree, filename):
        """ Extracts frames from one sentence and iterate over them """
        for node in tree:
            # For every verb, looks for its infinitive form in VerbNet, and
            # builds a frame occurrence if it is found

            if wn.morphy(node.word.lower(), 'v') is not None:
                node.lemma = wn.morphy(node.word.lower(), 'v')
            else:
                node.lemma = node.word.lower()

            if not node.lemma in self.frames_for_verb:
                continue

            if self._is_predicate(node):
                #Si deprel = VC, prendre le noeud du haut pour les args
                #Si un child est VC -> ne rien faire avec ce node
                predicate = Predicate(
                    node.begin_word, node.begin_word + len(node.word) - 1,
                    node.word, node.lemma,
                    node.word_id)
                
                if options.heuristic_rules:
                    args = [self._nodeToArg(x, node) for x in find_args(node)]
                else:
                    args = self._find_args(node)

                args = [x for x in args if self._is_good_pt(x.phrase_type)]
                
                yield FrameInstance(
                    sentence=sentence,
                    predicate=predicate,
                    args=args,
                    words=[Word(x.begin, x.end, x.pos) for x in tree],
                    frame_name="",
                    sentence_id=sentence_id,
                    filename=filename
                )
    
    def _is_good_pt(self, phrase_type):
        """ Tells whether a phrase type is acceptable for an argument """
        # If it contains a space, it has been assigned by _get_phrase_type
        if " " in phrase_type: return True
        
        return phrase_type in self.acceptable_pt
    
    def _find_args(self, node):
        """Returns every arguments of a given node.
        
        :param node: The node for which descendants are susceptible to be returned.
        :type node: SyntacticTreeNode.
        :returns: Arg List -- The resulting list of arguments.
        
        """
        
        base_node = node
        while base_node.deprel in ["VC", "CONJ", "COORD"]:
            base_node = base_node.father
        
        result = self._find_args_rec(node, node)
        if not base_node is node and base_node.pos in self.predicate_pos:
            result += self._find_args_rec(base_node, base_node)

        result = [x for x in result if x.text != "to"]

        return result
    
    def _find_args_rec(self, predicate_node, node):
        """Returns every arguments of a given node that is a descendant of another node.
        It is possible that one of the returned arguments corresponds
        to the second node itself.
        
        :param predicate_node: The node of which we want to obtain arguments.
        :type predicate_node: SyntacticTreeNode.
        :param node: The node for which descendants are susceptible to be returned.
        :type node: SyntacticTreeNode.
        :returns: Arg List -- The resulting list of arguments.
        
        """
        result = []
        for child in node.children:
            if self._is_arg(child, predicate_node):
                result.append(self._nodeToArg(child, predicate_node))
            elif not child.pos in self.predicate_pos:
                result += self._find_args_rec(predicate_node, child)
        return result
    
    def _overlap(self, node1, node2):
        return (node1.begin <= node2.begin_word + len(node2.word) - 1 and
            node1.end >= node2.begin_word)
    
    def _same_side(self, node, child, predicate):
        if node.begin_word < predicate.begin_word:
            return child.end < predicate.begin_word
        return child.begin > predicate.begin_word
    
    def _nodeToArg(self, node, predicate):
        """ Builds an Arg using the data of a node. """
        
        # Prevent arguments from overlapping over the predicate
        begin, end = node.begin, node.end
        text = node.flat()

        if self._overlap(node, predicate):
            begin, end = node.begin_word, node.begin_word + len(node.word) - 1
            for child in node.children:
                if self._same_side(node, child, predicate):
                    begin, end = min(begin, child.begin), max(end, child.end)
            root = node
            while root.father != None: root = root.father
            text = root.flat()[begin:end+1]
            
        return Arg(
            position=node.word_id,
            begin=begin,
            end=end,
            text=text,
            # If the argument isn't continuous, text will not be
            # a substring of frame.sentence
            role="",
            instanciated=True,
            phrase_type=self._get_phrase_type(node),
            annotated=False)
    
    def _get_phrase_type(self, node):
        #IN = Preposition or subordinating conjunction
        if node.pos == "IN":
            if node.word.lower() in all_preps: return "PP"
            return "S"
        # WP = Wh-pronoun
        if node.pos == "WP":
            return node.word.lower()+" S"
        
        if node.pos in self.pos_conversions:
            return self.pos_conversions[node.pos]
        return node.pos
    
    def _is_predicate(self, node):
        """Tells whether a node can be used as a predicate for a frame"""
        # Check part-of-speech compatibility
        if not node.pos in self.predicate_pos:
            return False
        
        # Check that this node is not an auxiliary
        if node.lemma in ["be", "do", "have", "will", "would"]:
            for child in node.children:
                if child.pos in self.predicate_pos and child.deprel == "VC":
                    return False    
        return True
    
    def _is_subject(self, node, predicate_node):
        """Tells whether node is the subject of predicate_node. This is only called
        when node is a brother of predicate_node.
        """
        return ((not node is predicate_node) and
                node.deprel in self.subject_deprels)
        
    def _is_arg(self, node, predicate_node):
        """Tells whether node is an argument of predicate_node. This is only called
        when node is a descendant of predicate_node.
        """
        return ((not node is predicate_node) and
                node.deprel in self.args_deprels)

class ArgGuesserTest(unittest.TestCase):
    def setUp(self):
        verbnet = verbnetreader.VerbnetReader(paths.VERBNET_PATH).frames_for_verb
        self.arg_guesser = ArgGuesser(verbnet)

    def test_global(self):
        frames = []
        for filename in FNAllReader.fulltext_parses():
            frames.extend([x for x in self.arg_guesser.frame_instances_from_file(filename)])

        num_args = 0
        
        for frame in frames:
            for arg in frame.args:
                self.assertTrue(arg.text != "")
                #self.assertEqual(frame.sentence[arg.begin:arg.end + 1], arg.text)
            num_args += len(frame.args)
        print(len(frames))
        print(num_args)
            
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
        
        self.assertEqual(self.arg_guesser._find_args(treeBuilder.tree_list[0]), args)
        print(self.arg_guesser._find_args(treeBuilder.tree_list[0]))

    def test_multiroot_sentence(self):
        conll_tree = \
"""1	because	because	IN	IN	-	15	VMOD	-	-
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
