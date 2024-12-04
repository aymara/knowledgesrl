#!/usr/bin/env python3

import argparse
import sys
import unittest
import probabilitymodel


from framenetallreader import FNAllReader
from options import Options


class FNAllReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("--loglevel", type=str,
                            choices=['debug', 'info', 'warning', 'error',
                                        'critical'],
                            default='warning',
                            help="Log level.")
        # Separate unittest arguments and custom arguments
        args, unittest_args = parser.parse_known_args()

        # initialize the Options class with command line arguments
        Options(args)
        return unittest_args

    def comp(self, original, parsed):
        return all(
            [x == y or y == "<num>" for x,y in zip(original.split(), parsed.split())]
        )

    def test_sentences_match(self, num_sample=0):
        extractor = FNAllReader()

        frames = []

        # annotation_files = ["/home/gael/Projets/knowledgesrl/data/fndata-1.5/fulltext/ANC__110CYL067.xml"]
        # parse_files = ["/home/gael/Projets/knowledgesrl/data/framenet_parsed/ANC__110CYL067.conll"]

        annotation_files = Options.fulltext_annotations
        parse_files = Options.fulltext_parses
        for annotation_file, parse_file in zip(annotation_files, parse_files):
            new_frames = [f for f in extractor.iter_frames(annotation_file, parse_file)]
            # print(len(new_frames), annotation_file, parse_file)
            frames.extend(new_frames)
        frames.sort()
        # print(", ".join([f"{attr}: {getattr(Options, attr)}" for attr in dir(Options)]))
        # for k in range(len(frames)):
        #     print(f"This is frame {k} sentence: {frames[k].sentence}")
        # used to be 28 and 6. stabilized with the sort above
        # TODO in fact the order (and the number of frames) changes if other
        # tests are run or not. So, there is a side effect somewhere that
        # remains unexplained
        frame = frames[344]
        self.assertTrue(frame.sentence == (
            "a few months ago "
            "you received a letter from me telling the success stories of "
            "people who got jobs with goodwill 's help ."))
        self.assertTrue(frame.predicate.lemma == "receive")
        self.assertFalse(frame.passive)
        self.assertTrue(frame.tree.flat() == frame.sentence)

        frame = frames[327]  # used to be 42 and 24. same as above
        self.assertTrue(frame.predicate.lemma == "use")
        # self.assertTrue(frame.passive)


if __name__ == '__main__':
    unittest_args = FNAllReaderTest.setUpClass()
    unittest.main(argv=[sys.argv[0]] + unittest_args)
