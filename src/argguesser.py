#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Extract frames, predicates and arguments from a corpus, using only syntactic annotations """

import verbnetreader
from framenetparsedreader import FNParsedReader
from framestructure import *
from conllreader import SyntacticTreeBuilder
from verbnetprepclasses import all_preps
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

    
    predicate_pos = ["VV", "VVN", "MD", "VB", "VBD", "VBN", "VBP", "VBZ"]
    predicate_pp_pos = ["VBN"]
      
    subject_deprels = [
    "LGS", #Logical subject -> should we keep this (36 args) ?
    "SBJ"
    ]
    
    non_core_deprels = [
    "DIR", "EXT", "LOC", 
    "MNR", "PRP", "PUT", "TMP"
    ]
        
    args_deprels = subject_deprels + [
    "BNF", #the 'for' phrase for verbs that undergo dative shift
    "DTV", #the 'to' phrase for verbs that undergo dative shift
    "OBJ", #direct or indirect object or clause complement
    "OPRD",#object complement
    "PRD", #predicative complement
    ]
    
    # Source : http://www.comp.leeds.ac.uk/ccalas/tagsets/upenn.html
    pos_conversions = {
    "$":"NP",
    "CD":"NP", #Cardinal number ("The tree of us")
    "DT":"NP", #Determiner ("this" or "that")
    "JJ":"ADJ", "JJR":"ADJ",
    "MD":"S", #Modal verb
    "NN":"NP", "NNP":"NP", "NNPS": "NP", "NNS":"NP",
    "NP":"NP", "NPS":"NP",
    "PP":"PP",
    "PRP":"NP",
    "RB":"ADV",
    "TO":"to S",
    "VB":"S", #Base form of a verb
    "VBD":"S", "VBG":"S_ING",
    "VBN":"ADJ", # Participe, as "fed" in "He got so fed up that..."
    "VBP":"S", "VBZ":"S",
    #VB* become VV* in the non-gold parse
    "VV":"S", "VVD":"S", "VVG":"S_ING",
    "VVN":"ADJ",
    "VVP":"S", "VVZ":"S",
    "WDT":"NP" #Relative pronom ("that what whatever which whichever ")
    }
    
    complex_pos = ["IN", "WP"]

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
                    word, pos = data[1], data[3]
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
            if self._is_predicate(node):
                #Si deprel = VC, prendre le noeud du haut pour les args
                #Si un child est VC -> ne rien faire avec ce node
                node.lemma = node.word.lower()
                if node.word in self.base_forms:
                    node.lemma = self.base_forms[node.word]
                if node.lemma in self.verbnet_index:
                    predicate = Predicate(
                        node.begin_head, node.begin_head + len(node.word) - 1,
                        node.word, node.lemma)
                    args = self._find_args(node)

                    if len(args) > 0:
                        yield Frame(
                            sentence=self.tree.flat(),
                            predicate=predicate,
                            args=args,
                            words=[Word(x.begin, x.end, x.pos) for x in self.tree],
                            frame_name="",
                            sentence_id=self.sentence_id,
                            filename=self.filename.replace(".conll", ".xml")
                        )
    
    def _find_args(self, node):
        """Returns every arguments of a given node.
        
        :param node: The node which descendant are susceptible to be returned.
        :type node: SyntacticTreeNode.
        :returns: Arg List -- The resulting list of arguments.
        
        """
        
        base_node = node
        while base_node.deprel in ["VC", "CONJ", "COORD"]:
            base_node = base_node.father
        
        result = self._find_args_rec(node, node)
        if not base_node is node and base_node.pos in self.predicate_pos:
            result += self._find_args_rec(base_node, base_node)
        
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
                """if not child.pos in self.pos_conversions and child.pos not in self.complex_pos:
                    print(predicate_node.flat())
                    print(child.flat())
                    print(child.pos)"""
        return result
    
    def _nodeToArg(self, node):
        """ Builds an Arg using the data of a node. """
        return Arg(
            begin=node.begin,
            end=node.end,
            text=node.flat(), 
            # If the argument isn't continuous, text will not be
            # a substring of frame.sentence
            role="",
            instanciated=True,
            phrase_type=self._get_phrase_type(node))
    
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
        
        # For a past participe, find the auxiliary
        # and return false if it is also a past participe
        if node.pos in self.predicate_pp_pos:
            current_node = node
            while current_node.deprel == "VC":
                current_node = current_node.father
            if (current_node.pos in self.predicate_pp_pos or
                not current_node.pos in self.predicate_pos
            ):
                return False
        
        # Check that this node is not an auxiliary
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
    def test_global(self):
        verbnet = verbnetreader.VerbnetReader(paths.VERBNET_PATH).verbs
        arg_finder = ArgGuesser(paths.FRAMENET_PARSED, verbnet)

        frames = [x for x in arg_finder.handle_corpus()]
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
        tree = treeBuilder.build_syntactic_tree()
        args = [
            Arg(0, 20, "The others here today", "", True, "NP")
        ]
        
        verbnet = verbnetreader.VerbnetReader(paths.VERBNET_PATH).verbs
        arg_finder = ArgGuesser(paths.FRAMENET_PARSED, verbnet) 

        self.assertEqual(arg_finder._find_args(tree), args)
if __name__ == "__main__":
    unittest.main()
