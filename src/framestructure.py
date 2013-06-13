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
    
    def __init__(self, sentence, predicate, args, words, frame_name,
        sentence_id = 0, filename = "", slot_type = "", annotated = False):
        self.frame_name = frame_name
        self.sentence = sentence
        self.predicate = predicate
        self.args = sorted(args)
        self.words = words
        self.sentence_id = sentence_id
        self.filename = filename
        self.slot_type = slot_type
        self.annotated = annotated

    def get_word(self, word):
        return self.sentence[word.begin:word.end + 1]
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.sentence == other.sentence and
            self.predicate == other.predicate and
            self.args == other.args and
            self.words == other.words)

    def __repr__(self):
        return "Frame({}, {}, {})".format(
                self.predicate, self.args, self.frame_name)

class VerbnetFrame:
    """A representation of a frame syntaxic structure
    
    :var structure: String list containing a VerbNet-style representation of the structure
    :var roles: List of the possible VerbNet roles for each structure's slot
    :var num_slots: Number of argument slots in :structure
    :var verbnet_class: For VerbNet-extracted frames, the class number, eg. 9.10
    :var predicate: For FrameNet-extracted frames, the predicate
    
    """
    
    slot_types = {
        "subject":"SBJ", "object":"OBJ",
        "indirect_object":"OBJI", "prep_object":"PPOBJ"
    }
    
    phrase_replacements = {
        "N":"NP", "Poss":"NP", "QUO":"S",
        "Sinterrog":"S", "Sfin":"S",
        "VPbrst":"S", "VPing":"S_ING", "VPto":"to S"
    }
    
    def __init__(self, structure, roles, vnclass = None, predicate = None):
        self.structure = structure
        self.predicate = predicate
        
        # Transform "a" in {"a"} and keep everything else unchanged
        self.roles = [{x} if isinstance(x, str) else x for x in roles]
        self.slot_preps = []
        self.slot_types = []
        self.headwords = []
        
        self.num_slots = len(self.roles)
        
        # Used to retrieve vnclass and map roles to framenet roles
        self.vnclass = vnclass

        self.compute_slot_types()
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.structure == other.structure and
            self.roles == other.roles and
            self.num_slots == other.num_slots and
            self.predicate == other.predicate)
            
    def __repr__(self):
        return "VerbnetFrame({}, {}, {}, {})".format(
                self.predicate, self.structure, self.roles, self.vnclass)
    
    def compute_slot_types(self):
        """Build the list of slot types for this frame"""
        
        # Re-initialize in case we are called several times
        self.slot_types, self.slot_preps = [], []
        
        # The next slot we are expecting :
        # always subject before the verb, object immediatly after the verb
        # and indirect_object after we encoutered a slot for object
        next_expected = VerbnetFrame.slot_types["subject"]
        # If last structure element was a preposition, this will be filled
        # with the preposition and will "overwrite" :next_expected
        preposition = ""
        
        for element in self.structure:
            if element == "V":
                next_expected = VerbnetFrame.slot_types["object"]
            elif element[0].isupper(): # If this is a slot
                if preposition != "":
                    self.slot_types.append(VerbnetFrame.slot_types["prep_object"])
                    self.slot_preps.append(preposition)
                    preposition = ""
                else:
                    self.slot_types.append(next_expected)
                    self.slot_preps.append(None)
                    if next_expected == VerbnetFrame.slot_types["object"]:
                        next_expected = VerbnetFrame.slot_types["indirect_object"]
            elif isinstance(element, list) or element in verbnetprepclasses.all_preps:
                preposition = element
            
    
    @staticmethod    
    def build_from_frame(frame):
        """Build a VerbNet frame from a Frame object
        
        :param frame: The original Frame.
        :type frame: Frame.
        :returns: VerbnetFrame -- the built frame, without the roles
        """
        
        # The main job is to build the VerbNet structure representation
        # from the Frame object data
        
        num_slots = 0
        
        # First, delete everything that is before or after the frame
        begin = frame.predicate.begin
        end = frame.predicate.end
        
        for argument in frame.args:
            if not argument.instanciated: continue
            num_slots += 1
            if argument.begin < begin: begin = argument.begin
            if argument.end > end: end = argument.end
 
        structure = frame.sentence[begin:end + 1]
        # Then, replace the predicate/arguments by their phrase type
        structure = VerbnetFrame._reduce_args(frame, structure, begin)
        # And delete everything else, except some keywords
        structure = VerbnetFrame._keep_only_keywords(structure)
        # Transform the structure into a list
        structure = structure.split(" ")
        #structure = VerbnetFrame._strip_leftpart_keywords(structure)
                
        result = VerbnetFrame(structure, [], predicate=frame.predicate.lemma)
        result.num_slots = num_slots
        
        # Fill the role list with None value
        result.roles = [None] * num_slots
        
        return result

    def passivize(self):
        """
        Based on current frame, return a list of possible passivizations
        Currently extremely simple on purpose, the goal is to add variations later on.
        """
        passivizedframes = []
        index_v = self.structure.index("V")

        intransitive = VerbnetFrame([self.structure[index_v+1], "V"], [self.roles[1]], vnclass = self.vnclass)
        passivizedframes.append(intransitive)

        transitive = VerbnetFrame(
            [self.structure[index_v+1], "V", "by", self.structure[0]],
            [self.roles[1], self.roles[0]],
            vnclass = self.vnclass)
        passivizedframes.append(transitive)

        return passivizedframes
        
        
    
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

            before = structure[0:argument.begin - new_begin]
            after = structure[1 + argument.end - new_begin:]
            # Replace every "PP" by "prep NP"
            if argument.phrase_type == "PP":
                prep = ""
                for word in argument.text.lower().split(" "):
                    if word in verbnetprepclasses.keywords:
                        prep = word
                        break             
                if prep == "":
                    prep = argument.text.lower().split(" ")[0]
                         
                added_length = 6 + len(prep)
                structure = "{}| {} NP|{}".format(before, prep, after)
            # Replace every "PPing" by "prep S_ING", 
            elif argument.phrase_type == "PPing":
                prep = ""
                for word in argument.text.lower().split(" "):
                    if word in verbnetprepclasses.keywords:
                        prep = word
                        break             
                if prep == "":
                    prep = argument.text.lower().split(" ")[0]
                         
                added_length = 9 + len(prep)
                structure = "{}| {} S_ING|{}".format(before, prep, after)
            # Replace every "Swhether" and "S" by "that S", "if S", ...
            elif argument.phrase_type in ["Swhether", "Sub"]:
                sub = argument.text.split(" ")[0].lower()
                added_length = 5 + len(sub)
                structure = "{}| {} S|{}".format(before, sub, after)
            # Handle simple phrase replacements
            elif argument.phrase_type in VerbnetFrame.phrase_replacements:
                phrase = VerbnetFrame.phrase_replacements[argument.phrase_type]
                added_length = 4 + len(phrase)
                structure = "{} | {}|{}".format(before, phrase, after)
            else:
                added_length = 3 + len(argument.phrase_type)
                structure = "{}| {}|{}".format(before, argument.phrase_type, after)
            
            # Compute the new position of the predicate if we reduced an argument before it    
            if argument.begin - new_begin < predicate_begin:
                offset = (argument.end - argument.begin + 1) - added_length
                predicate_begin -= offset
                predicate_end -= offset

        structure = "{}| V|{}".format(
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
        closing_tag = False
        result = ""
        
        while pos < last_pos:
            if inside_tag and sentence[pos] == "|":
                inside_tag = False
                closing_tag = True
            if inside_tag: 
                result += sentence[pos]
                pos += 1
                continue
            if not closing_tag and sentence[pos] == "|": inside_tag = True
            closing_tag = False
            
            for search in verbnetprepclasses.external_lexemes:
                if (search == sentence[pos:pos + len(search)].lower() and
                    (pos == 0 or sentence[pos - 1] == " ") and
                    (pos + len(search) == len(sentence) or
                        sentence[pos + len(search)] == " ")
                ):
                    pos += len(search) - 1
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
    
    def __init__(self, begin, end, text, role, instanciated, phrase_type, annotated = True):
        self.begin = begin
        self.end = end
        self.text = text
        self.role = role
        self.instanciated = instanciated
        self.phrase_type = phrase_type
        
        # This can be false for extracted args which could not be matched with
        # annotated args from the fulltext corpus
        self.annotated = annotated

    def __repr__(self):
        return self.role
        
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

    def __str__(self):
        return self.lemma
        
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
                ],
                "Attempt_suasion" ),
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
                 ],
                 "Grant_permission" ) ]
        
        vn_frames = [
            VerbnetFrame(["NP", "V", "NP", "to", "S"], 
                [None, None, None], predicate="urge"),
            VerbnetFrame(["NP", "V", "NP"], [None, None], predicate="allow"),
            VerbnetFrame(
                ["NP", "NP", "in", "NP", "V", "that", "S",
                    "for", "NP", "NP", "after", "NP"],
                [None, None, None, None, None, None, None])
        ]
        slot_preps = [
            [None, None, "to"],
            [None, None],
            [None, None, "in", None, "for", None, "after"]
        ]
        st = VerbnetFrame.slot_types
        slot_types = [
            [st["subject"], st["object"], st["prep_object"]],
            [st["subject"], st["object"]],
            [st["subject"], st["subject"], st["prep_object"], st["object"],
            st["prep_object"], st["indirect_object"], st["prep_object"]]
        ]
        
        verbnet_frame = VerbnetFrame.build_from_frame(tested_frames[0])
        self.assertEqual(vn_frames[0], verbnet_frame)
        self.assertEqual(verbnet_frame.slot_types, slot_types[0])
        self.assertEqual(verbnet_frame.slot_preps, slot_preps[0])
        
        verbnet_frame = VerbnetFrame.build_from_frame(tested_frames[1])
        self.assertEqual(vn_frames[1], verbnet_frame)
        self.assertEqual(verbnet_frame.slot_types, slot_types[1])
        self.assertEqual(verbnet_frame.slot_preps, slot_preps[1])
        
        # compute_slot_types is idempotent
        verbnet_frame = vn_frames[2]
        verbnet_frame.compute_slot_types()
        verbnet_frame.compute_slot_types()
        self.assertEqual(verbnet_frame.slot_types, slot_types[2])
        self.assertEqual(verbnet_frame.slot_preps, slot_preps[2])

    def test_passivize(self):
        vn_frame_transitive = VerbnetFrame(["NP", "V", "NP"], ["Agent", "Theme"])
        passivizations = vn_frame_transitive.passivize()
        self.assertEqual(passivizations, [
            VerbnetFrame(["NP", "V"], ["Theme"]),
            VerbnetFrame(["NP", "V", "by", "NP"], ["Theme", "Agent"])])
        
        
if __name__ == "__main__":
    unittest.main()
