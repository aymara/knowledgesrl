#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from abc import ABCMeta

from framestructure import FrameInstance, Predicate, Arg, Word
import verbnetprepclasses

class ComputeSlotTypeMixin(metaclass=ABCMeta):
    slot_types = {
        "subject": "SBJ", "object": "OBJ",
        "indirect_object": "OBJI", "prep_object": "PPOBJ"
    }

    def compute_slot_types(self, structure):
        """Build the list of slot types for this frame"""

        slot_types, slot_preps = [], []

        # The next slot we are expecting :
        # always subject before the verb, object immediatly after the verb
        # and indirect_object after we encoutered a slot for object
        next_expected = ComputeSlotTypeMixin.slot_types["subject"]
        # If last structure element was a preposition, this will be filled
        # with the preposition and will "overwrite" :next_expected
        preposition = ""

        for element in structure:
            if element == "V":
                next_expected = ComputeSlotTypeMixin.slot_types["object"]
            elif self._is_a_slot(element):
                if preposition != "":
                    slot_types.append(ComputeSlotTypeMixin.slot_types["prep_object"])
                    slot_preps.append(preposition)
                    preposition = ""
                else:
                    slot_types.append(next_expected)
                    slot_preps.append(None)
                    if next_expected == ComputeSlotTypeMixin.slot_types["object"]:
                        next_expected = ComputeSlotTypeMixin.slot_types["indirect_object"]
            elif isinstance(element, set) or element in verbnetprepclasses.all_preps:
                preposition = element

        return slot_types, slot_preps

    @staticmethod
    def _is_a_slot(elem):
        """Tell wether an element represent a slot

        :param elem: The element.
        :type elem: str.
        :returns: bool -- True if elem represents a slot, False otherwise
        """

        return isinstance(elem, str) and elem[0].isupper() and elem != "V"

class VerbnetFrameOccurrence(ComputeSlotTypeMixin): 
    """A representation of a FrameNet frame occurrence converted to VerbNet
    representation for easy comparison.

    :var structure: (str | str set) list -- representation of the structure
    :var roles: set list -- possible VerbNet roles for each structure's slot
    :var num_slots: int -- number of argument slots in :structure
    :var predicate: str -- the predicate
    :var headwords: str -- the head word of each argument
    """

    phrase_replacements = {
        "N": "NP", "Poss": "NP", "QUO": "S",
        "Sinterrog": "S", "Sfin": "S",
        "VPbrst": "S", "VPing": "S_ING", "VPto": "to S"
    }

    def __init__(self, structure, roles, predicate):
        self.structure = structure
        self.predicate = predicate

        # Transform "a" in {"a"} and keep everything else unchanged
        self.roles = [{x} if isinstance(x, str) else x for x in roles]
        self.num_slots = len(self.roles)

        self.slot_types, self.slot_preps = self.compute_slot_types(structure)
        self.headwords = []

        self.best_classes = None

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.structure == other.structure and
                self.roles == other.roles and
                self.num_slots == other.num_slots and
                self.predicate == other.predicate)

    def __repr__(self):
        return "VerbnetFrameOccurrence({}, {}, {})".format(
            self.predicate, self.structure, self.roles)

    @staticmethod
    def build_from_frame(gold_framenet_instance, conll_frame_instance):
        """Build a VerbNet frame from a FrameInstance object

        :param gold_framenet_instance: The gold FrameNet frame instance
        :type frame: FrameInstance.
        :param conll_frame_instance: The frame instance from CoNLL
        :type frame: FrameInstance.
        :returns: VerbnetFrameOccurrence -- the frame without the gold roles
        converted to VerbNet-style representation
        """

        num_slots = 0

        # The goal here is to translate a FrameInstance into a VerbnetFrameOccurrence.
        # We do this in a number of steps

        # TODO split the method for two usages
        if conll_frame_instance is not None:
            sentence = conll_frame_instance.sentence
        elif gold_framenet_instance is not None:
            sentence = gold_framenet_instance.sentence
        else:
            raise Exception('Either conll_frame_instance or gold_framenet_instance should exist.')

        # First, only keep the text segments with arguments and predicates
        begin = gold_framenet_instance.predicate.begin
        end = gold_framenet_instance.predicate.end

        for argument in gold_framenet_instance.args:
            if not argument.instanciated:
                continue
            num_slots += 1
            if argument.begin < begin:
                begin = argument.begin
            if argument.end > end:
                end = argument.end

        structure = sentence[begin:end + 1]

        # Then, replace the predicate/arguments by their phrase type
        structure = VerbnetFrameOccurrence._reduce_args(gold_framenet_instance, structure, begin)
        # And delete everything else, except some keywords
        structure = VerbnetFrameOccurrence._keep_only_keywords(structure)
        # Transform the structure into a list
        structure = structure.split(" ")

        result = VerbnetFrameOccurrence(structure, [], predicate=gold_framenet_instance.predicate.lemma)
        result.num_slots = num_slots

        # Finally, fill the role list with None value
        result.roles = [None] * num_slots

        # If the FrameInstance only comes from a CoNLL file and is not part of
        # the corpus, we don't want to loose predicate/args position in the
        # file so that we can add classes and roles later
        # TODO remove this condition and reorganize caller code instead
        if conll_frame_instance is not None:
            result.predicate_position = conll_frame_instance.predicate.position
            result.args = conll_frame_instance.args
            result.sentence_id = conll_frame_instance.sentence_id

        return result

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

            if not argument.instanciated:
                continue

            phrase_type = argument.phrase_type
            if phrase_type in VerbnetFrameOccurrence.phrase_replacements:
                phrase_type = VerbnetFrameOccurrence.phrase_replacements[phrase_type]

            before = structure[0:argument.begin - new_begin]
            after = structure[1 + argument.end - new_begin:]
            arg_first_word = argument.text.lower().split(" ")[0]

            # Fix some S incorrectly marked as PP
            if (phrase_type == "PP"
                    and arg_first_word in verbnetprepclasses.sub_pronouns):
                added_length = 8 + len(arg_first_word)
                structure = "{} || {} S| {}".format(before, arg_first_word, after)

            # Replace every "PP" by "prep NP"
            elif phrase_type == "PP":
                prep = ""
                for word in argument.text.lower().split(" "):
                    if word in verbnetprepclasses.keywords:
                        prep = word
                        break
                if prep == "":
                    prep = arg_first_word

                added_length = 9 + len(prep)
                structure = "{} || {} NP| {}".format(before, prep, after)
            # Replace every "PPing" by "prep S_ING",
            elif phrase_type == "PPing":
                prep = ""
                for word in argument.text.lower().split(" "):
                    if word in verbnetprepclasses.keywords:
                        prep = word
                        break
                if prep == "":
                    prep = arg_first_word

                added_length = 12 + len(prep)
                structure = "{} || {} S_ING| {}".format(before, prep, after)
            # Replace every "Swhether" and "S" by "that S", "if S", ...
            elif phrase_type in ["Swhether", "Sub"]:
                added_length = 8 + len(arg_first_word)
                structure = "{} || {} S| {}".format(before, arg_first_word, after)
            else:
                added_length = 6 + len(phrase_type)
                structure = "{} || {}| {}".format(before, phrase_type, after)

            # Compute the new position of the predicate if we reduced an
            # argument before it
            if argument.begin - new_begin < predicate_begin:
                offset = (argument.end - argument.begin + 1) - added_length
                predicate_begin -= offset
                predicate_end -= offset

        structure = "{} || V| {}".format(
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
        inside_tag = 0
        closing_tag = False
        result = ""

        while pos < last_pos:
            if inside_tag == 2 and sentence[pos] == "|":
                inside_tag = 0
                closing_tag = True

            if inside_tag == 2:
                result += sentence[pos]
                pos += 1
                continue

            if not closing_tag and sentence[pos] == "|":
                inside_tag += 1
            else:
                inside_tag = 0
            closing_tag = False

            for search in verbnetprepclasses.external_lexemes:
                if (search == sentence[pos:pos + len(search)].lower() and
                    (pos == 0 or sentence[pos - 1] == " ") and
                    (pos + len(search) == len(sentence) or
                        sentence[pos + len(search)] == " ")):

                    pos += len(search) - 1
                    result += " "+search

            pos += 1

        if result[0] == " ":
            result = result[1:]

        if result[-1] == " ":
            result = result[:-1]

        return result


class VerbnetOfficialFrame(ComputeSlotTypeMixin):
    """A representation of a frame syntactic structure

    :var structure: (str | str set) List -- representation of the structure
    :var roles: str list -- VerbNet roles for each structure's slot
    :var num_slots: int -- number of argument slots in :structure
    :var vnclass: str -- the class number, eg. 9.10
    :var example: str -- An example sentence that illustrates the frame
    """

    def __init__(self, structure, roles, vnclass, role_restrictions):
        self.structure = structure

        # Transform "a" in {"a"} and keep everything else unchanged
        self.roles = [{x} if isinstance(x, str) else x for x in roles]
        self.num_slots = len(self.roles)
        self.role_restrictions = role_restrictions

        self.slot_types, self.slot_preps = self.compute_slot_types(structure)
        self.vnclass = vnclass

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.structure == other.structure and
                self.roles == other.roles and
                self.num_slots == other.num_slots and
                self.vnclass == other.vnclass)

    def __repr__(self):
        return "VerbnetOfficialFrame({}, {}, {})".format(
            self.vnclass, self.structure, self.roles)

    def passivize(self):
        """
        Based on current frame, return a list of possible passivizations
        """
        passivizedframes = []

        # Find the position of the first slot following the verb and
        # the last element of the first slot of the frame
        slot_position = 0
        old_sbj_end = 0
        first_slot = True
        for i, element in enumerate(self.structure):
            if first_slot:
                old_sbj_end = i
            if VerbnetOfficialFrame._is_a_slot(element):
                first_slot = False
                slot_position += 1
            if element == "V":
                break

        # Find the first and last element of the first slot following the verb
        index_v = self.structure.index("V")
        new_sbj_begin, new_sbj_end = index_v + 1, index_v + 1
        while True:
            if new_sbj_end >= len(self.structure):
                return []
            if VerbnetOfficialFrame._is_a_slot(self.structure[new_sbj_end]):
                break
            new_sbj_end += 1

        # Build the passive frame without "by"
        frame_without_agent = VerbnetOfficialFrame(
            (self.structure[new_sbj_begin:new_sbj_end+1] +
                self.structure[old_sbj_end+1:index_v] + ["V"] +
                self.structure[new_sbj_end+1:]),
            ([self.roles[slot_position]] + self.roles[1:slot_position] +
                self.roles[slot_position+1:]),
            vnclass=self.vnclass,
            role_restrictions=self.role_restrictions
        )

        passivizedframes.append(frame_without_agent)

        # Add the frames obtained by inserting "by + the old subject"
        # after the verb and every slot that follows it
        new_index_v = frame_without_agent.structure.index("V")
        i = new_index_v
        slot = slot_position - 1
        while i < len(frame_without_agent.structure):
            elem = frame_without_agent.structure[i]
            if self._is_a_slot(elem) or elem == "V":
                passivizedframes.append(VerbnetOfficialFrame(
                    (frame_without_agent.structure[0:i+1] +
                        ["by"] + self.structure[0:old_sbj_end+1] +
                        frame_without_agent.structure[i+1:]),
                    (frame_without_agent.roles[0:slot+1] +
                        [self.roles[0]] +
                        frame_without_agent.roles[slot+1:]),
                    vnclass=self.vnclass,
                    role_restrictions=self.role_restrictions
                ))
                slot += 1
            i += 1

        return passivizedframes

    def generate_relatives(self):
        relatives = []
        i_slot = 0
        for i, element in enumerate(self.structure):
            if VerbnetOfficialFrame._is_a_slot(element):
                j = i - 1
                while j >= 0 and self.structure[j][0].islower():
                    j -= 1

                structure = (self.structure[j+1:i+1] +
                             self.structure[0:j+1] +
                             self.structure[i+1:])
                roles = ([self.roles[i_slot]] +
                         self.roles[0:i_slot] +
                         self.roles[i_slot+1:])

                relatives.append(
                    VerbnetOfficialFrame(structure, roles, vnclass=self.vnclass,
                                 role_restrictions=self.role_restrictions))
                i_slot += 1

        return relatives
