#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Extract frames, predicates and arguments from a corpus, using only syntactic annotations """

import verbnetreader
from framenetparsedreader import FNParsedReader
from framestructure import *
from conllreader import SyntacticTreeBuilder
import framenetreader
import unittest
import paths
import pickle
import os
import sys

class ArgGuesser(FNParsedReader):
    """
    :var verbnet_index: VerbnetFrame Dict -- Used to know which predicates are in VerbNet.
    :var base_forms: str Dict -- The infinitives of the verbal forms we found in the corpus.
    """
    
    predicate_pos = ["VV", "VVN"]
    
    subject_deprels = ["SBJ"]
    args_deprels = subject_deprels + ["OBJ", "VC"]
    
    def __init__(self, path, verbnet_index):
        FNParsedReader.__init__(self, path)
        self.verbnet_index = verbnet_index
        self.base_forms = {}

    def handle_corpus(self):
        """ Extracts frames from the corpus and iterate over them """
        
        # First, compute the infinitive for of every verb in the corpus
        self._compute_base_forms()
        
        # Read the corpus a second time to build frames
        for filename in sorted(os.listdir(self.annotations_path)):
            if not filename[-6:] == ".conll": continue

            print(".", file=sys.stderr, end="")
            sys.stderr.flush()
       
            for frame in self._handle_file(filename):
                yield frame

    def _extract_verbs(self):
        """ Computes the set of every verbs in the corpus 
        
        :returns: str Set -- The set of every verbal form encountered in the corpus
        
        """
        
        result = set()
        
        for filename in sorted(os.listdir(self.annotations_path)):
            if not filename[-6:] == ".conll": continue

            print(".", file=sys.stderr, end="")
            sys.stderr.flush()
       
            with open(self.annotations_path + filename) as content:
                for line in content.readlines():
                    data = line.split("\t")
                    if len(data) < 2: continue
                    word, pos = data[1], data[4]
                    if pos in self.predicate_pos:
                        result.add(word.lower())
        
        print("")                
        return result          

    def _compute_base_forms(self):
        """ Use the python2 script that can talk to nltk to compute the infinitive forms """
    
        with open("temp_wordlist", "wb") as picklefile:
            pickle.dump(self._extract_verbs(), picklefile, 2)

        os.system("python2.7 wordclassesloader.py --morph")
        
        with open("temp_morph", "rb") as picklefile:
            self.base_forms.update(pickle.load(picklefile))
            
        os.system("rm temp_wordlist temp_morph")

    def _handle_file(self, filename):
        """ Extracts frames from one file and iterate over them """
        self.load_file(filename)
        sentence_id = 1
        while self.select_sentence(sentence_id):
            for frame in self._handle_sentence():
                yield frame
            sentence_id += 1
    
    def _handle_sentence(self):
        """ Extracts frames from one sentence and iterate over them """
        for node in self.tree:
            # For every verb, looks for its infinitive form in verbnet, and
            # builds a new frame if it is found
            if node.pos in self.predicate_pos:
                node.lemma = node.word
                if node.word in self.base_forms:
                    node.lemma = self.base_forms[node.word]
                if node.lemma in self.verbnet_index:
                    predicate = Predicate(node.begin, node.end, node.word, node.lemma)
                    args = self._find_args(node)
                    
                    yield Frame(
                        sentence=self.tree.flat(),
                        predicate=predicate,
                        args=args,
                        words=[Word(x.begin, x.end, x.pos) for x in self.tree],
                        frame_name=None,
                        sentence_id=self.sentence_id,
                        filename=self.filename
                    )
    
    def _find_args(self, node):
        """Returns every arguments of a given node.
        
        :param node: The node which descendant are susceptible to be returned.
        :type node: SyntacticTreeNode.
        :returns: Arg List -- The resulting list of arguments.
        
        """
        result = self._find_args_rec(node, node)
        
        """
        if node.father != None:
            for brother in node.father.children:
                if self._is_subject(brother, node):
                    result.append(self._nodeToArg(brother))"""

        return result
    
    def _find_args_rec(self, predicate_node, node):
        """Returns every arguments of a given node that is a descendant of another node.
        It is possible that one of the returned arguments corresponds
        to the second node itself.
        
        :param predicate_node: The node of which we want to obtain arguments.
        :type predicate_node: SyntacticTreeNode.
        :param node: The node which descendant are susceptible to be returned.
        :type node: SyntacticTreeNode.
        :returns: Arg List -- The resulting list of arguments.
        
        """
        result = []
        for child in node.children:
            if not child.pos in self.predicate_pos:
                result += self._find_args_rec(predicate_node, child)
            if self._is_arg(child, predicate_node):
                result.append(self._nodeToArg(child))
        return result
    
    def _nodeToArg(self, node):
        """ Builds an Arg using the data of a node. """
        return Arg(
            begin=node.begin,
            end=node.end,
            text=node.flat(),
            role=None,
            instanciated=True,
            phrase_type=node.pos)
    
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
    def test_global(self):
        verbnet = verbnetreader.VerbnetReader(paths.VERBNET_PATH).verbs
        arg_finder = ArgGuesser(paths.FRAMENET_PARSED, verbnet)

        frames = [x for x in arg_finder.handle_corpus()]
        num_args = 0
        for frame in frames:
            for arg in frame.args:
                self.assertTrue(arg.text != "")
                self.assertEqual(frame.sentence[arg.begin:arg.end + 1], arg.text)
            num_args += len(frame.args)
            
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
        tree = treeBuilder.build_syntactic_tree()
        args = [
            Arg(0, 20, "The others here today", None, True, "NNS")
        ]
        
        verbnet = verbnetreader.VerbnetReader(paths.VERBNET_PATH).verbs
        arg_finder = ArgGuesser(paths.FRAMENET_PARSED, verbnet) 
        
        self.assertEqual(arg_finder._find_args(tree), args)
if __name__ == "__main__":
    unittest.main()