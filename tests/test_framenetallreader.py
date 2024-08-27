#!/usr/bin/env python3

import sys
sys.path.append('/home/cjaffre/knowledgesrl/src')

import unittest

from framenetallreader import FNAllReader
import options


class FNAllReaderTest(unittest.TestCase):
    def comp(self, original, parsed):
        return all(
            [x == y or y == "<num>" for x,y in zip(original.split(), parsed.split())]
        )

    def test_sentences_match(self, num_sample = 0):
        extractor = FNAllReader()

        frames = []
        for annotation_file, parse_file in zip(options.Options.fulltext_annotations, options.Options.fulltext_parses):
            frames.extend(extractor.iter_frames(annotation_file, parse_file))
        frame = frames[28]
        self.assertTrue(frame.sentence == ("a few months ago "
            "you received a letter from me telling the success stories of "
            "people who got jobs with goodwill 's help ."))
        self.assertTrue(frame.predicate.lemma == "receive")
        self.assertTrue(frame.passive == False)
        self.assertTrue(frame.tree.flat() == frame.sentence)
        
        frame = frames[42]
        self.assertTrue(frame.predicate.lemma == "use")
        self.assertTrue(frame.passive == True)
        
if __name__ == '__main__':
    unittest.main()
