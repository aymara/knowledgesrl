#!/usr/bin/env python3

import unittest

from verbnetframe import VerbnetFrameOccurrence, VerbnetOfficialFrame, ComputeSlotTypeMixin
from framenetframe import FrameInstance, Predicate, Arg, Word


tony_hall_frame_instances = [
    FrameInstance(
        "Rep . Tony Hall , D- Ohio , urges the United Nations to allow"
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
        "Attempt_suasion"),
    FrameInstance(
        "Rep . Tony Hall , D- Ohio , urges the United Nations to allow"
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
        "Grant_permission")]


class VerbnetFrameOccurrenceTest(unittest.TestCase):
    def test_conversion(self):
        vn_frames = [
            VerbnetFrameOccurrence(
                ["NP", "V", "NP", "to", "S"],
                [None, None, None], predicate="urge"),
            VerbnetFrameOccurrence(["NP", "V", "NP"], [None, None], predicate="allow"),
        ]
        slot_preps = [
            [None, None, "to"],
            [None, None],
            [None, None, "in", None, "for", None, "after"]
        ]
        st = ComputeSlotTypeMixin.slot_types
        slot_types = [
            [st["subject"], st["object"], st["prep_object"]],
            [st["subject"], st["object"]],
            [st["subject"], st["subject"], st["prep_object"], st["object"],
             st["prep_object"], st["indirect_object"], st["prep_object"]]
        ]

        verbnet_frame = VerbnetFrameOccurrence.build_from_frame(tony_hall_frame_instances[0], None)
        self.assertEqual(vn_frames[0], verbnet_frame)
        self.assertEqual(verbnet_frame.slot_types, slot_types[0])
        self.assertEqual(verbnet_frame.slot_preps, slot_preps[0])

        verbnet_frame = VerbnetFrameOccurrence.build_from_frame(tony_hall_frame_instances[1], conll_frame_instance=None)
        self.assertEqual(vn_frames[1], verbnet_frame)
        self.assertEqual(verbnet_frame.slot_types, slot_types[1])
        self.assertEqual(verbnet_frame.slot_preps, slot_preps[1])

    def test_annotated_chunks(self):
        tony_hall_gold_frame = tony_hall_frame_instances[0]
        tony_hall_gold_frame_chunks = [
            {'phrase_type': 'NP', 'type': 'arg', 'text': 'Rep . Tony Hall , D- Ohio'},
            {'text': '', 'type': 'text'},
            {'type': 'verb', 'text': 'urges'},
            {'text': '', 'type': 'text'},
            {'phrase_type': 'NP', 'type': 'arg', 'text': 'the United Nations'},
            {'text': '', 'type': 'text'},
            {'phrase_type': 'to S', 'type': 'arg', 'text': 'to allow a freer flow of food and medicine into Iraq'}]

        self.assertEqual(list(VerbnetFrameOccurrence.annotated_chunks(tony_hall_gold_frame, tony_hall_gold_frame.sentence)), tony_hall_gold_frame_chunks)

        without_subject = FrameInstance(
            "Rep . Tony Hall , D- Ohio , urges the United Nations to allow"
            " a freer flow of food and medicine into Iraq .",
            Predicate(28, 32, "urges", "urge"),
            [
                Arg(34, 51, "the United Nations", "Addressee", True, "NP"),
                Arg(53, 104,
                    "to allow a freer flow of food and medicine into Iraq",
                    "Content", True, "VPto"),
            ], [], "XXX")
        without_subject_chunks = [
            {'type': 'text', 'text': 'Rep . Tony Hall , D- Ohio ,'},
            {'type': 'verb', 'text': 'urges'},
            {'text': '', 'type': 'text'},
            {'phrase_type': 'NP', 'type': 'arg', 'text': 'the United Nations'},
            {'text': '', 'type': 'text'},
            {'phrase_type': 'to S', 'type': 'arg', 'text': 'to allow a freer flow of food and medicine into Iraq'}]

        self.assertEqual(list(VerbnetFrameOccurrence.annotated_chunks(without_subject, without_subject.sentence)), without_subject_chunks)
