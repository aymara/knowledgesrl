#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Frames, arguments and predicates."""

import unittest
import verbnetprepclasses

class Frame:
    """A frame extracted from the corpus 
    
    :var sentence: Sentence in which the frame appears
    :var predicate: Predicate object representing the frame's predicate
    :var args: Arg list containing the predicate's arguments
    
    """
    
    def __init__(self, sentence, predicate, args, words):
        self.sentence = sentence
        self.predicate = predicate
        self.args = sorted(args)
        self.words = words

    def get_word(self, word):
        return self.sentence[word.begin:word.end + 1]
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.sentence == other.sentence and
            self.predicate == other.predicate and
            self.args == other.args and
            self.words == other.words)

class VerbnetFrame:
    """A representation of a frame syntaxic structure
    
    :var structure: String containing a VerbNet-style representation of the structure
    :var roles: List of the VerbNet of the element of the structure empty for prepositions
    
    """
    
    #keywords = ["to be", "how", "to", "what", "whether"]
    
    def __init__(self, structure, roles):
        self.structure = structure
        self.roles = roles
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.structure == other.structure and
            self.roles == other.roles)
            
    def __repr__(self):
        return "VerbnetFrame({}, {})".format(self.structure, self.roles)
        
    @staticmethod    
    def build_from_frame(frame):
        """Build a VerbNet frame from a Frame object
        
        :param frame: The original Frame.
        :type frame: Frame.
        :returns: VerbnetFrame -- the built frame, without the roles
        """
        
        # The main job is to build the VerbNet structure representation
        # from the Frame object data
        
        # First, delete everything that is before or after the frame
        begin = frame.predicate.begin
        end = frame.predicate.end
        
        for argument in frame.args:
            if not argument.instanciated: continue
            if argument.begin < begin: begin = argument.begin
            if argument.end > end: end = argument.end
 
        structure = frame.sentence[begin:end + 1]
        # Then, replace the predicate/arguments by their phrase type
        structure = VerbnetFrame._reduce_args(frame, structure, begin)
        # And delete everything else, except some keywords
        structure = VerbnetFrame._keep_only_keywords(structure)
        # Transform the structure into a list
        structure = structure.split(" ")
        # Delete every keyword before the verb
        structure = VerbnetFrame._strip_leftpart_keywords(structure)
        return VerbnetFrame(structure, [])
    
    @staticmethod    
    def _reduce_args(frame, structure, new_begin):
        """Replace the predicate and the argument of a frame by phrase type marks
        
        :param frame: The original Frame.
        :type frame: Frame.
        :param structure: The current structure representation.
        :type structure: str.
        :param new_begin: The left offset cause by previous manipulations.
        :type new_begin: int.
        :returns: String -- the reduced string
        """
        predicate_begin = frame.predicate.begin - new_begin
        predicate_end = frame.predicate.end - new_begin

        for argument in reversed(frame.args):
            if not argument.instanciated: continue

            # Replace every "PP" by "prep NP"
            if argument.phrase_type == "PP":
                prep = argument.text.split(" ")[0].lower()
                added_length = 6 + len(prep)
                structure = "{}{} < NP>{}".format(
                    structure[0:argument.begin - new_begin],
                    prep,  
                    structure[1 + argument.end - new_begin:])
            else:
                added_length = 3 + len(argument.phrase_type)
                structure = "{}< {}>{}".format(
                    structure[0:argument.begin - new_begin], 
                    argument.phrase_type, 
                    structure[1 + argument.end - new_begin:])
                
            if argument.begin - new_begin < predicate_begin:
                offset = (argument.end - argument.begin + 1) - added_length
                predicate_begin -= offset
                predicate_end -= offset

        structure = "{}< V>{}".format(
            structure[0:predicate_begin], structure[1+predicate_end:])
            
        return structure
    
    @staticmethod        
    def _keep_only_keywords(sentence):
        """Keep only keywords and phrase type markers in the structure
        
        :param sentence: The structure to reduce.
        :type sentence: str.
        :returns: String -- the reduced string
        """
        pos = 0
        last_pos = len(sentence) - 1
        inside_tag = False
        result = ""
        
        while pos < last_pos:
            if sentence[pos] == ">": inside_tag = False
            if inside_tag: result += sentence[pos]
            if sentence[pos] == "<": inside_tag = True
            
            for search in verbnetprepclasses.keywords:
                if " "+search+" " == sentence[pos:pos + len(search) + 2].lower():
                    pos += len(search) + 1
                    result += " "+search
            
            pos += 1
        
        if result[0] == " ": result = result[1:]
        if result[-1] == " ": result = result[:-1]
            
        return result
    
    @staticmethod    
    def _strip_leftpart_keywords(sentence):
        result = []
        found_verb = False
        for elem in sentence:
            if elem == "V": found_verb = True
            if found_verb or elem[0].isupper():
                result.append(elem)
                
        return result
        
class Arg:

    """An argument of a frame 

    :var begin: integer, position of the argument's first character in the sentence
    :var end: integer, position of the argument's last character in the sentence
    :var text: string containing the argument's text
    :var role: string containing the argument's role
    :var instanciated: boolean that marks wether the argument is instanciated
    
    """
    
    def __init__(self, begin, end, text, role, instanciated, phrase_type):
        self.begin = begin
        self.end = end
        self.text = text
        self.role = role
        self.instanciated = instanciated
        self.phrase_type = phrase_type
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__)  and
            ((self.begin == other.begin and self.end == other.end) or
                (self.instanciated == False and other.instanciated == False)) and
            self.role == other.role and
            self.phrase_type == other.phrase_type)
            
    def __cmp__(self, other):
        if not self.instanciated:
            if other.instanciated: return 1
            if self.role < other.role: return -1
            if self.role > other.role: return 1
            return 0
        if not other.instanciated: return -1
        if self.begin < other.begin: return -1
        if self.begin > other.begin: return 1
        return 0
        
    def __lt__(self, other):
        return self.__cmp__(other) < 0
        
    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0
    
class Predicate:

    """A frame's predicate 
    
    :var begin: integer, position of the predicate's first character in the sentence
    :var end: integer, position of the predicate's last character in the sentence
    :var text: string containing the predicate's text
    :var lemma: string containing the predicate's lemma
    
    """
    
    def __init__(self, begin, end, text, lemma):
        self.begin = begin
        self.end = end
        self.text = text
        self.lemma = lemma
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.begin == other.begin and
            self.end == other.end and
            self.lemma == other.lemma)

class Word:
    """A frame's word
    
    :var begin: integer, position of the predicate's first character in the sentence
    :var end: integer, position of the predicate's last character in the sentence
    :var text: string containing the predicate's text
    :var pos: string containing the predicate's part-of-speech
    
    """
    
    def __init__(self, begin, end, pos):
        self.begin = begin
        self.end = end
        if pos == 'sent': pos = '.'
        self.pos = pos.upper()
        
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.begin == other.begin and
            self.end == other.end and
            self.pos == other.pos)

    def __repr__(self):
        return "Word({}, {}, \"{}\")".format(self.begin, self.end, self.pos)

            
class VerbnetFrameTest(unittest.TestCase):
    def test_conversion(self):
        tested_frames = [
            Frame(
                "Rep . Tony Hall , D- Ohio , urges the United Nations to allow"+\
                " a freer flow of food and medicine into Iraq .", 
                Predicate(28, 32, "urges", "urge"),
                [
                    Arg(34, 51, "the United Nations", "Addressee", True, "NP"),
                    Arg(53, 104,
                        "to allow a freer flow of food and medicine into Iraq", 
                        "Content", True, "VPto"),
                    Arg(0, 26, "Rep . Tony Hall , D- Ohio", "Speaker", True, "NP")
                ],
                [
                    Word(0, 2, "NN"), Word(4, 4, "."), Word(6, 9, "NP"),
                    Word(11, 14, "NP"), Word(16, 16, ","), Word(18, 19, "NN"),
                    Word(21, 24, "NP"), Word(26, 26, ","), Word(28, 32, "VVZ"),
                    Word(34, 36, "DT"), Word(38, 43, "NP"), Word(45, 51, "NPS"),
                    Word(53, 54, "TO"), Word(56, 60, "VV"), Word(62, 62, "DT"),
                    Word(64, 68, "JJR"), Word(70, 73, "NN"), Word(75, 76, "IN"),
                    Word(78, 81, "NN"), Word(83, 85, "CC"), Word(87, 94, "NN"),
                    Word(96, 99, "IN"), Word(101, 104, "NP"), Word(106, 106, ".")
                ] ),
            Frame(
                "Rep . Tony Hall , D- Ohio , urges the United Nations to allow"+\
                " a freer flow of food and medicine into Iraq .", 
                 Predicate(56, 60, "allow", "allow"),
                 [
                    Arg(62, 104, 
                        "a freer flow of food and medicine into Iraq",
                        "Action", True, "NP"),
                    Arg(34, 51, "the United Nations", "Grantee", True, "NP"),
                    Arg(0, -1, "", "Grantor", False, "")
                 ],
                 [
                    Word(0, 2, "NN"), Word(4, 4, "."), Word(6, 9, "NP"),
                    Word(11, 14, "NP"), Word(16, 16, ","), Word(18, 19, "NN"),
                    Word(21, 24, "NP"), Word(26, 26, ","), Word(28, 32, "VVZ"),
                    Word(34, 36, "DT"), Word(38, 43, "NP"), Word(45, 51, "NPS"),
                    Word(53, 54, "TO"), Word(56, 60, "VV"), Word(62, 62, "DT"),
                    Word(64, 68, "JJR"), Word(70, 73, "NN"), Word(75, 76, "IN"),
                    Word(78, 81, "NN"), Word(83, 85, "CC"), Word(87, 94, "NN"),
                    Word(96, 99, "IN"), Word(101, 104, "NP"), Word(106, 106, ".")
                 ] ) ]
        
        expected_results = [
            VerbnetFrame(["NP", "V", "NP", "VPto"], []),
            VerbnetFrame(["NP", "V", "NP"], [])
        ]
            
        verbnet_frame = VerbnetFrame.build_from_frame(tested_frames[0])
        self.assertEqual(expected_results[0], verbnet_frame)
        verbnet_frame = VerbnetFrame.build_from_frame(tested_frames[1])
        self.assertEqual(expected_results[1], verbnet_frame)
        
if __name__ == "__main__":
    unittest.main()
