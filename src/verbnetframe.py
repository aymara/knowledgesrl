#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABCMeta
from operator import attrgetter

from framenetframe import Predicate, Arg
import verbnetprepclasses


class ComputeSlotTypeMixin(metaclass=ABCMeta):
    slot_types = {
        "subject": "SBJ", "object": "OBJ",
        "indirect_object": "OBJI", "prep_object": "PPOBJ"
    }

    def compute_slot_types(self, syntax):
        """Build the list of slot types for this frame"""

        slot_types, slot_preps = [], []

        # The next slot we are expecting :
        # always subject before the verb, object immediatly after the verb
        # and indirect_object after we encoutered a slot for object
        next_expected = ComputeSlotTypeMixin.slot_types["subject"]
        # If last syntax element was a preposition, this will be filled
        # with the preposition and will "overwrite" :next_expected
        preposition = ""

        for element in syntax:
            # TODO type(...) == tuple is a hack!
            if type(element) == tuple:
                element, role = element

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
        self.headwords = [None] * self.num_slots

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

        # The goal here is to translate a FrameInstance into a VerbnetFrameOccurrence.

        # TODO split the method for two usages
        if conll_frame_instance is not None:
            sentence = conll_frame_instance.sentence
        elif gold_framenet_instance is not None:
            sentence = gold_framenet_instance.sentence
        else:
            raise Exception('Either conll_frame_instance or gold_framenet_instance should exist.')

        chunk_list = VerbnetFrameOccurrence.annotated_chunks(gold_framenet_instance, sentence)
        structure = list(VerbnetFrameOccurrence.chunks_to_verbnet(chunk_list))


        result = VerbnetFrameOccurrence(structure, [], predicate=gold_framenet_instance.predicate.lemma)
        result.num_slots = len([arg for arg in gold_framenet_instance.args if arg.instanciated])

        # Finally, fill the role list with None value
        result.roles = [None] * result.num_slots

        # If the FrameInstance only comes from a CoNLL file and is not part of
        # the corpus, we don't want to loose predicate/args position in the
        # file so that we can add classes and roles later
        # TODO remove this condition and reorganize caller code instead
        if conll_frame_instance is not None:
            result.predicate_position = conll_frame_instance.predicate.position
            result.sentence_id = conll_frame_instance.sentence_id

            result.args = conll_frame_instance.args
            result.tree = conll_frame_instance.tree
            result.headwords = conll_frame_instance.headwords
        else:
            result.args = gold_framenet_instance.args
            result.tree = gold_framenet_instance.tree
            result.headwords = gold_framenet_instance.headwords

        return result

    @staticmethod
    def annotated_chunks(frame, sentence):
        """Transforms a frame sentence into a list of "chunks".

        The chunks we're talking about are really "parts of a sentence", not
        actual parsed chunks."""

        frame_part_list = sorted(
            frame.args + [frame.predicate],
            key=attrgetter('begin'))

        i = 0
        for frame_part in frame_part_list:
            # Place the preceding chunk
            if frame_part.begin > i:
                yield {
                    'type': 'text',
                    'text': sentence[i:frame_part.begin].strip()}
                i = frame_part.begin

            # Place predicate or argument
            if isinstance(frame_part, Predicate):
                yield {'type': 'verb', 'text': frame.predicate.text}
                i = frame_part.end + 1
            elif isinstance(frame_part, Arg):
                argument = frame_part
                if not argument.instanciated:
                    continue

                assert i == argument.begin
                phrase_type = VerbnetFrameOccurrence.phrase_replacements.get(
                    argument.phrase_type, argument.phrase_type)
                yield {
                    'type': 'arg',
                    'phrase_type': phrase_type,
                    'text': argument.text}
                i = argument.end + 1

    @staticmethod
    def chunks_to_verbnet(chunk_list):
        for chunk in chunk_list:
            if chunk['text'] == '':
                pass
            elif chunk['type'] == 'arg':
                arg_first_word = chunk['text'].split()[0]
                if chunk['phrase_type'] == 'PP' and arg_first_word in verbnetprepclasses.sub_pronouns:
                    yield arg_first_word
                    yield 'S'
                elif chunk['phrase_type'] == 'PP':
                    yield arg_first_word
                    yield 'NP'
                elif chunk['phrase_type'] == 'PPing':
                    yield arg_first_word
                    yield 'S_ING'
                elif chunk['phrase_type'] == 'to S':
                    yield 'to'
                    yield 'S'
                elif chunk['phrase_type'] in ["Swhether", "Sub"]:
                    yield arg_first_word
                    yield 'S'
                else:
                    yield chunk['phrase_type']
            elif chunk['type'] == 'verb':
                yield 'V'
            elif chunk['type'] == 'text':
                # we do not keep any keyword here, but it's a possibility.
                pass
            else:
                raise Exception('Unknown chunk type {}.'.format(chunk['type']))


class VerbnetOfficialFrame(ComputeSlotTypeMixin):
    """A representation of a frame syntactic syntax

    :var syntax : (str + role tuple | str + None tuple | str set + None tuple) list -- structure + roles
    :var num_slots: int -- number of argument slots in :structure
    :var vnclass: str -- the class number, eg. 9.10
    :var example: str -- An example sentence that illustrates the frame
    """

    def __init__(self, syntax, vnclass, role_restrictions):
        self.syntax = syntax
        self.num_slots = len([role for elem, role in syntax if role is not None])
        self.role_restrictions = role_restrictions

        self.slot_types, self.slot_preps = self.compute_slot_types(syntax)
        self.vnclass = vnclass

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.syntax == other.syntax and
                self.vnclass == other.vnclass)

    def __key__(self):
        def syntax_no_set(syntax):
            for elem, role in syntax:
                yield '-'.join(elem) if type(elem) == set else '{}.{}'.format(elem, role)

        return (self.vnclass, len(self.syntax), tuple(syntax_no_set(self.syntax)))

    def __lt__(self, other):
        return self.__key__() < other.__key__()

    def __repr__(self):
        return "VerbnetOfficialFrame({}, {})".format(
            self.vnclass, self.syntax)

    def has(self, word):
        return any([True for elem, role in self.syntax if 'that' in elem])

    def remove(self, word):
        self.syntax = [(elem, role) for elem, role in self.syntax if elem != word]

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
        for i, element in enumerate(self.syntax):
            element, role = element
            if first_slot:
                old_sbj_end = i
            if VerbnetOfficialFrame._is_a_slot(element):
                first_slot = False
                slot_position += 1
            if element == "V":
                break

        # Find the first and last element of the first slot following the verb
        index_v = self.syntax.index(("V", None))
        new_sbj_begin, new_sbj_end = index_v + 1, index_v + 1
        while True:
            if new_sbj_end >= len(self.syntax):
                return []

            # TODO type(...) -= tuple is a hack!
            if type(self.syntax[new_sbj_end]) == tuple and VerbnetOfficialFrame._is_a_slot(self.syntax[new_sbj_end][1]):
                break
            new_sbj_end += 1

        # Build the passive frame without "by"
        frame_without_agent = VerbnetOfficialFrame(
            (self.syntax[new_sbj_begin:new_sbj_end+1] +
                self.syntax[old_sbj_end+1:index_v] + [("V", None)] +
                self.syntax[new_sbj_end+1:]),
            vnclass=self.vnclass,
            role_restrictions=self.role_restrictions
        )

        passivizedframes.append(frame_without_agent)

        # Add the frames obtained by inserting "by + the old subject"
        # after the verb and every slot that follows it
        new_index_v = frame_without_agent.syntax.index(("V", None))
        i = new_index_v
        slot = slot_position - 1
        while i < len(frame_without_agent.syntax):
            elem, role = frame_without_agent.syntax[i]
            if self._is_a_slot(elem) or elem == "V":
                passivizedframes.append(VerbnetOfficialFrame(
                    (frame_without_agent.syntax[0:i+1] +
                        [("by", None)] + self.syntax[0:old_sbj_end+1] +
                        frame_without_agent.syntax[i+1:]),
                    vnclass=self.vnclass,
                    role_restrictions=self.role_restrictions
                ))
                slot += 1
            i += 1

        return passivizedframes
