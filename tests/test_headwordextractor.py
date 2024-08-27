#!/usr/bin/env python3

import sys
sys.path.append('/home/cjaffre/knowledgesrl/src')


import unittest
from parser_test import parse_arguments # type: ignore
import random
import options # type: ignore
from conllparsedreader import ConllParsedReader # type: ignore
import headwordextractor # type: ignore
import framenetreader # type: ignore
import paths # type: ignore

import nltk
nltk.download('wordnet')


class HeadWordExtractorTest(unittest.TestCase):
    def test_classes(self):
        filename = "ANC__110CYL067"
        fnparsed_reader = ConllParsedReader()
        parsed_conll_file = paths.Paths.FRAMENET_PARSED / (filename + ".conll")

        reader = framenetreader.FulltextReader(options.Options.fulltext_annotations[0], False)

        for frame in reader.frames:
            sentence_id, sentence_text, tree = list(fnparsed_reader.sentence_trees(parsed_conll_file))[frame.sentence_id]
            for arg in frame.args:
                headwordextractor.headword(arg, tree)

        self.assertEqual(headwordextractor.get_class("soda"), "physical_entity.n.01")
        #self.assertEqual(headwordextractor.get_class("i"), "pronoun")
        
        # get_class should return None for words out of WordNet
        self.assertEqual(headwordextractor.get_class("abcde"), None)

    def test_1(self):
        filename = "ANC__110CYL067"
        fnparsed_reader = ConllParsedReader()
        parsed_conll_file = paths.Paths.FRAMENET_PARSED / (filename + ".conll")

        reader = framenetreader.FulltextReader(
            paths.Paths.framenet_fulltext(options.Options.language)
            / (filename + ".xml"), False)

        frame = reader.frames[1]
        sentence_id, sentence_text, tree = list(fnparsed_reader.sentence_trees(parsed_conll_file))[frame.sentence_id]
        self.assertEqual(headwordextractor.headword(frame.args[0], tree), {'top_headword': ('PRP', 'you'), 'content_headword': ('PRP', 'you')})

        frame = reader.frames[25]
        sentence_id, sentence_text, tree = list(fnparsed_reader.sentence_trees(parsed_conll_file))[frame.sentence_id]
        self.assertEqual(headwordextractor.headword(frame.args[0], tree), {'top_headword': ('NNS', 'people'), 'content_headword': ('NNS', 'people')})


def sample_args(argus, num_sample = 10):
    """Not a unit test. Returns a random sample of argument/node/headword to help.

    :param num_sample: The requested number of results
    :type num_sample: int
    :returns: (str, str, str) List -- Some examples of (arg, best_node_text, headword)
    """
    fnparsed_reader = ConllParsedReader()


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
    print(options.Options.fulltext_annotations)
    print(f"language selected: {argus.language}")
    options.Options.init(argus)
    print(options.Options.fulltext_annotations)
    for annotation_file, parsed_conll_file in zip(options.Options.fulltext_annotations, options.Options.fulltext_parses):
        if annotation_file.stem in bad_files: continue

        reader = framenetreader.FulltextReader(annotation_file)

        previous_sentence = 0

        for frame in reader.frames:
            if (annotation_file.stem, frame.sentence_id) in bad_sentences: continue

            if frame.sentence_id != previous_sentence:
                sentence_id, sentence_text, tree = list(fnparsed_reader.sentence_trees(parsed_conll_file))[frame.sentence_id]

            for arg in frame.args:
                if not arg.instanciated: continue
                node = tree.closest_match_as_node(arg)
                sample.append((arg.text, node.flat(), node.word))

            previous_sentence = frame.sentence_id

    random.shuffle(sample)
    return sample[0:num_sample]


if __name__ == "__main__":
    num_sample = 50
    argus = parse_arguments()
    print(f"language selected: {argus.language}")
    if num_sample > 0:
        result = sample_args(argus, num_sample)
        for exemple in result:
            print("{}\n{}\n{}\n".format(exemple[0], exemple[1], exemple[2]))
    unittest.main()
