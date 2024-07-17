#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""  Module defining classes related to VerbNet frames

    Define classes:
    * ComputeSlotTypeMixin
    * VerbnetFrameOccurrence
    * VerbnetOfficialFrame
"""

import options
import logging
logger = logging.getLogger(__name__)
# logger.setLevel(options.Options.loglevel)

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

        for part in syntax:
            element = part['elem']
            if element == "V":
                next_expected = ComputeSlotTypeMixin.slot_types["object"]
            elif self._is_a_slot(part):
                if preposition != "":
                    slot_types.append(ComputeSlotTypeMixin.slot_types["prep_object"])  # noqa
                    slot_preps.append(preposition)
                    preposition = ""
                else:
                    slot_types.append(next_expected)
                    slot_preps.append(None)
                    if next_expected == ComputeSlotTypeMixin.slot_types["object"]:  # noqa
                        next_expected = ComputeSlotTypeMixin.slot_types["indirect_object"]  # noqa
            elif (isinstance(element, set)
                  or element in verbnetprepclasses.all_preps):
                preposition = element

        return slot_types, slot_preps

    @staticmethod
    def _is_a_slot(part):
        """Tell wether an element represent a slot

        :param dict: The element.
        :type elem: str.
        :returns: bool -- True if elem represents a slot, False otherwise
        """
        if 'role' in part:
            return True
        elif type(part['elem']) == set:
            return False
        else:
            return part['elem'].isupper() and part['elem'] != "V"


class VerbnetFrameOccurrence(ComputeSlotTypeMixin):
    """A representation of a FrameNet frame occurrence converted to VerbNet
    representation for easy comparison.

    :var structure: (str | str set) list -- representation of the structure.
    :var predicate: str -- the predicate, a lemma.
    :var num_slots: int -- number of argument slots in the structure.
    :var slot_types: string list -- syntactic relation for each role.
    :var slot_preps: string list -- preposition introducing each role.
    :var headwords: hash list -- the head word of each argument.
    :var best_matches: {'vnframe': VerbnetOfficialFrame, 'slot_assocs': int
        list } list -- The frames that achieved the best score + the mapping
        (in each tuple, the first int is the occurrence id, and the second one
        is the official id) between our identified slots and these verbnet
        frames
    :var roles: string set list -- for each role the list of possible role
        names
        Should ALWAYS reflect current match situation, except in
        probability models ?
    :var tokenid: int -- id of the predicate token in the sentence of the
        CoNLL file
    :var sentence_id: int -- id of the sentence in the CoNLL file
    :var args: Arg list -- the syntactic chunks corresponding to the role
    :var tree: -- the syntactic tree of under this frame occurrence

    An example:
        {
        'structure':    [{'elem': 'NP'}, {'elem': 'V'}, {'elem': 'NP'}],
        'predicate':    'establish',
        'num_slots':    2,
        'slot_types':   ['SBJ', 'OBJ'],
        'slot_preps':   [None, None],
        'headwords':    [{'content_headword': ('NNP', 'Convention'),
                        'top_headword': ('NNP', 'Convention')},
                         {'content_headword': ('NNS', 'Groups'),
                          'top_headword': ('NNS', 'Groups')}],
        'best_matches': [
            {'slot_assocs': [0, 1],
             'vnframe': VerbnetOfficialFrame(establish-55.5,
                NP.Agent [(animate) OR (organization)] V NP.Theme [None])},
            {'slot_assocs': [0, 1],
             'vnframe': VerbnetOfficialFrame(indicate-78,
                NP.Cause [None] V NP.Topic [None])},
            {'slot_assocs': [0, 1],
             'vnframe': VerbnetOfficialFrame(indicate-78-1-1,
                NP.Cause [None] V NP.Topic [None] to be NP)}
            ],
        'roles':        [{'Cause', 'Agent'}, {'Theme', 'Topic'}],
        'tokenid':      4,
        'sentence_id':  0,
        'args':         [Arg(The Convention, NP, ), Arg(Working Groups, NP, )],
        'tree':         (VBD/ROOT/2/0/52 established
            (NNP/SUB/1/0/13 Convention (DT/NMOD/0/0/2 The))
            (RB/VMOD/0/15/18 also)
            (NNS/OBJ/1/39/52 Groups (JJ/NMOD/0/39/45 Working))),
        }
    """

    phrase_replacements = {
        "N": "NP", "Poss": "NP", "QUO": "S",
        "Sinterrog": "S", "Sfin": "S",
        "VPbrst": "S", "VPing": "S_ING", "VPto": "to S"
    }

    def __init__(self, structure, num_slots, predicate, headwords=None,
                 best_matches=None, tokenid=-1, sentence_id=-1, args=None,
                 tree=None):
        logger = logging.getLogger(__name__)
        logger.setLevel(options.Options.loglevel)
        logger.debug('VerbnetFrameOccurrence {}, {}, {}'.format(structure, num_slots, predicate))
        self.structure = structure
        self.num_slots = num_slots
        self.predicate = predicate

        self.slot_types, self.slot_preps = self.compute_slot_types(structure)
        if headwords:
            self.headwords = headwords
        else:
            self.headwords = [None for i in range(self.num_slots)]

        if best_matches:
            self.best_matches = best_matches
        else:
            self.best_matches = []

        self.roles = self.possible_roles()

        self.tokenid = tokenid
        self.sentence_id = sentence_id

        if args:
            self.args = args
        else:
            self.args = []

        if tree:
            self.tree = tree
        else:
            self.tree = None

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.structure == other.structure and
                self.roles == other.roles and
                self.num_slots == other.num_slots and
                self.predicate == other.predicate)

    def __repr__(self):
        return ("VerbnetFrameOccurrence(structure={}, num_slots={}, "
                "predicate={}, headwords={}, best_matches={}, roles={}, "
                "tokenid={}, sentence_id={}, args={}, tree={})".format(
                    repr(self.structure), repr(self.num_slots),
                    repr(self.predicate), repr(self.headwords),
                    repr(self.best_matches), repr(self.roles),
                    self.tokenid, self.sentence_id,
                    repr(self.args), repr(self.tree)))

    def possible_roles(self):
        """Compute the lists of possible roles for each slot

        :returns: str set list -- The lists of possible roles for each slot
        """

        # Note: Do not use [set()] * self.num_slots as the set() would be the
        # same for each role.
        result = [set() for i in range(self.num_slots)]

        for match in self.best_matches:
            for slot1, slot2 in enumerate(match['slot_assocs']):
                if slot2 is None:
                    continue

                # We want this to fail when roles get stored in a dictionary
                # or a class
                assert all([type(s) == dict for s in match['vnframe'].syntax])

                role = [part['role'] for part in match['vnframe'].syntax if 'role' in part][slot2]  # noqa
                result[slot1].add(role)

        return result

    def add_match(self, match, score):
        logger.debug('add_match {} {}'.format(match, score))
        self.best_matches.append(match)
        self.roles = self.possible_roles()

    def remove_all_matches(self):
        logger.debug('remove_all_matches')
        self.best_matches = []
        self.roles = self.possible_roles()

    def remove_match(self, toremove_match):
        self.best_matches = [match for match in self.best_matches if match is not toremove_match]  # noqa
        self.roles = self.possible_roles()

    def restrict_slot_to_role(self, i, new_role):
        """ Restrict the ith slot to the given role

        This functions only affects self.roles without touching
        best_matches. The callers need to call select_likeliest_matches once
        they've restricted all roles.
        """
        self.roles[i] = set([new_role])

    def select_likeliest_matches(self):
        """Finds the matches that are the closest to the restricted roles.

        Only makes sense when roles got restricted by restrict_slot_to_role
        """
        scores = []

        for match in self.best_matches:
            roles_that_match = 0
            for i, role_set in enumerate(self.roles):
                if match['slot_assocs'][i] is None:
                    # not mapped?
                    continue

                role_in_match = match['vnframe'].roles()[match['slot_assocs'][i]]  # noqa
                if role_in_match in role_set:
                    roles_that_match += 1

            mean_num_slots = (self.num_slots + match['vnframe'].num_slots) / 2
            scores.append(roles_that_match / max(mean_num_slots, 1))

        if scores:
            best_score = max(scores)

            self.best_matches = [match for score, match
                                 in zip(scores, self.best_matches)
                                 if score == best_score]

            # Commenting out for now as it's the old behavior
            # self.roles = self.possible_roles()

    def best_classes(self):
        return {match['vnframe'].vnclass for match in self.best_matches}

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

        # The goal here is to translate a FrameInstance into a
        # VerbnetFrameOccurrence.

        # TODO split the method for two usages
        if conll_frame_instance is not None:
            sentence = conll_frame_instance.sentence
        elif gold_framenet_instance is not None:
            sentence = gold_framenet_instance.sentence
        else:
            raise Exception('Either conll_frame_instance or '
                            'gold_framenet_instance should exist.')

        chunk_list = VerbnetFrameOccurrence.annotated_chunks(gold_framenet_instance, sentence)  # noqa
        structure = [{'elem': elem} for elem in VerbnetFrameOccurrence.chunks_to_verbnet(chunk_list)]  # noqa

        num_slots = len([arg for arg in gold_framenet_instance.args
                         if arg.instanciated])
        result = VerbnetFrameOccurrence(structure, num_slots,
                                        predicate=gold_framenet_instance.predicate.lemma)  # noqa

        # If the FrameInstance only comes from a CoNLL file and is not part of
        # the corpus, we don't want to loose predicate/args position in the
        # file so that we can add classes and roles later
        # TODO remove this condition and reorganize caller code instead
        if conll_frame_instance is not None:
            result.tokenid = conll_frame_instance.predicate.tokenid
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
        """ Transform a frame sentence into a list of "chunks".

        The chunks we're talking about are really "parts of a sentence", not
        actual parsed chunks.
        """

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

                # assert i == argument.begin
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
                if (chunk['phrase_type'] == 'PP'
                        and arg_first_word in verbnetprepclasses.sub_pronouns):
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

    :var syntax : (str + role tuple | str + None tuple
                    | str set + None tuple) list -- structure + roles
    :var num_slots: int -- number of argument slots in :structure
    :var slot_types:
    :var slot_preps:
    :var vnclass: str -- the class number, eg. 9.10
    #:var example: str -- An example sentence that illustrates the frame
    """

    def __init__(self, vnclass, syntax):
        self.syntax = syntax
        self.num_slots = len([part for part in syntax if 'role' in part])

        self.slot_types, self.slot_preps = self.compute_slot_types(syntax)
        self.vnclass = vnclass

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.syntax == other.syntax and
                self.vnclass == other.vnclass)

    def syntax_no_set(self):
        for part in self.syntax:
            elem = part['elem']
            if 'role' in part:
                yield (f"{part['elem']}.{part['role']} "
                       f"[{part['restr'] if 'restr' in part else ''}]")
            elif type(elem) == set:
                yield '-'.join(elem)
            else:
                yield elem

    def __key__(self):
        return (self.vnclass, len(self.syntax), tuple(self.syntax_no_set()))

    def __lt__(self, other):
        return self.__key__() < other.__key__()

    def __repr__(self):
        return "VerbnetOfficialFrame({}, {})".format(
            self.vnclass, ' '.join(self.syntax_no_set()))

    def has(self, word):
        return any([True for part in self.syntax if word in part['elem']])

    def roles(self):
        return [part['role'] for part in self.syntax if 'role' in part]

    def selrestrs(self):
        return [part['restr'] for part in self.syntax if 'role' in part]

    def remove(self, word):
        self.syntax = [part for part in self.syntax if part['elem'] != word]

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
        for i, part in enumerate(self.syntax):
            if part['elem'] == "V":
                break

            if first_slot:
                old_sbj_end = i

            if VerbnetOfficialFrame._is_a_slot(part):
                first_slot = False
                slot_position += 1

        # Find the first and last element of the first slot following the verb
        index_v = self.syntax.index({'elem': 'V'})
        new_sbj_begin, new_sbj_end = index_v + 1, index_v + 1
        while True:
            if new_sbj_end >= len(self.syntax):
                return []

            if VerbnetOfficialFrame._is_a_slot(self.syntax[new_sbj_end]):
                break
            new_sbj_end += 1

        # Build the passive frame without "by"
        frame_without_agent = VerbnetOfficialFrame(
            self.vnclass,
            (self.syntax[new_sbj_begin:new_sbj_end+1] +
             self.syntax[old_sbj_end+1:index_v] + [{'elem': "V"}] +
             self.syntax[new_sbj_end+1:]))

        passivizedframes.append(frame_without_agent)

        # Add the frames obtained by inserting "by + the old subject"
        # after the verb and every slot that follows it
        new_index_v = frame_without_agent.syntax.index({'elem': 'V'})
        i = new_index_v
        slot = slot_position - 1
        while i < len(frame_without_agent.syntax):
            part = frame_without_agent.syntax[i]
            if self._is_a_slot(part) or part['elem'] == "V":
                passivizedframes.append(VerbnetOfficialFrame(
                    self.vnclass,
                    (frame_without_agent.syntax[0:i+1] +
                     [{'elem': 'by'}] + self.syntax[0:old_sbj_end+1] +
                     frame_without_agent.syntax[i+1:])))
                slot += 1
            i += 1

        return passivizedframes
