#!/usr/bin/env python3

import unittest

import random
import options
from framenetparsedreader import FNParsedReader
from headwordextractor import HeadWordExtractor
import framenetreader

class HeadWordExtractorTest(unittest.TestCase):
    def test_classes(self):
        filename = "ANC__110CYL067"
        fnparsed_reader = FNParsedReader()
        fnparsed_reader.load_file(options.framenet_parsed / (filename + ".conll"))
        extractor = HeadWordExtractor()

        reader = framenetreader.FulltextReader(options.fulltext_annotations[0], False)

        for frame in reader.frames:
            sentence_id, sentence_text, tree = list(fnparsed_reader.sentence_trees())[frame.sentence_id]
            for arg in frame.args:
                extractor.headword(arg, tree)

        self.assertEqual(extractor.get_class("soda"), "physical_entity.n.01")
        #self.assertEqual(extractor.get_class("i"), "pronoun")
        
        # get_class should return None for words out of WordNet
        self.assertEqual(extractor.get_class("abcde"), None)

    def test_1(self):
        filename = "ANC__110CYL067"
        fnparsed_reader = FNParsedReader()
        fnparsed_reader.load_file(options.framenet_parsed / (filename + ".conll"))
        extractor = HeadWordExtractor()

        reader = framenetreader.FulltextReader(options.fulltext_corpus / (filename + ".xml"), False)

        frame = reader.frames[1]
        sentence_id, sentence_text, tree = list(fnparsed_reader.sentence_trees())[frame.sentence_id]
        self.assertEqual(extractor.headword(frame.args[0], tree), "you")

        frame = reader.frames[25]
        sentence_id, sentence_text, tree = list(fnparsed_reader.sentence_trees())[frame.sentence_id]
        self.assertEqual(extractor.headword(frame.args[0], tree), "people")


def sample_args(self, num_sample = 10):
    """Not a unit test. Returns a random sample of argument/node/headword to help.

    :param num_sample: The requested number of results
    :type num_sample: int
    :returns: (str, str, str) List -- Some examples of (arg, best_node_text, headword)
    """
    fnparsed_reader = FNParsedReader()


    bad_files = [
            "ANC__110CYL070", "C-4__C-4Text",
            "NTI__BWTutorial_chapter1", "NTI__LibyaCountry1",
            "NTI__NorthKorea_Introduction"]
    bad_sentences = [
            ("LUCorpus-v0.3__sw2025-ms98-a-trans.ascii-1-NEW", 9),
            ("NTI__Iran_Chemical", 6),
            ("NTI__Iran_Chemical", 62),
            ("NTI__Iran_Nuclear", 5),
            ("NTI__Iran_Nuclear", 49),
            ("NTI__Iran_Nuclear", 68),
            ("NTI__Iran_Nuclear", 82),
            ("PropBank__ElectionVictory", 5),
            ("PropBank__ElectionVictory", 9),
            ("PropBank__LomaPrieta", 18)]
            

    sample = []
    for annotation_file, parsed_conll_file in zip(options.fulltext_annotations, options.fulltext_parses):
        if annotation_file.stem in bad_files: continue

        fnparsed_reader.load_file(parsed_conll_file)
        reader = framenetreader.FulltextReader(annotation_file)

        previous_sentence = 0

        for frame in reader.frames:
            if (annotation_file.stem, frame.sentence_id) in bad_sentences: continue

            if frame.sentence_id != previous_sentence:
                sentence_id, sentence_text, tree = list(fnparsed_reader.sentence_trees())[frame.sentence_id]

            for arg in frame.args:
                if not arg.instanciated: continue
                node = tree.closest_match_as_node(arg)
                sample.append((arg.text, node.flat(), node.word))

            previous_sentence = frame.sentence_id

    random.shuffle(sample)
    return sample[0:num_sample]


if __name__ == "__main__":
    num_sample = 50

    if num_sample > 0:
        result = sample_args(num_sample)
        for exemple in result:
            print("{}\n{}\n{}\n".format(exemple[0], exemple[1], exemple[2]))
