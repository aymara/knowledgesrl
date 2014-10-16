#!/usr/bin/env python3

import unittest

import options
from headwordextractor import HeadWordExtractor
import framenetreader


class HeadWordExtractorTest(unittest.TestCase):
    bad_files = [
            "ANC__110CYL070.xml", "C-4__C-4Text.xml",
            "NTI__BWTutorial_chapter1.xml", "NTI__LibyaCountry1.xml",
            "NTI__NorthKorea_Introduction.xml"]
    bad_sentences = [
            ("LUCorpus-v0.3__sw2025-ms98-a-trans.ascii-1-NEW.xml", 9),
            ("NTI__Iran_Chemical.xml", 6),
            ("NTI__Iran_Chemical.xml", 62),
            ("NTI__Iran_Nuclear.xml", 5),
            ("NTI__Iran_Nuclear.xml", 49),
            ("NTI__Iran_Nuclear.xml", 68),
            ("NTI__Iran_Nuclear.xml", 82),
            ("PropBank__ElectionVictory.xml", 5),
            ("PropBank__ElectionVictory.xml", 9),
            ("PropBank__LomaPrieta.xml", 18)]
            
    def test_classes(self):
        filename = "ANC__110CYL067"
        extractor = HeadWordExtractor()
        extractor.load_file(options.framenet_parsed / (filename + ".conll"))

        reader = framenetreader.FulltextReader(options.fulltext_annotations[0], False)

        for frame in reader.frames:
            sentence_id, sentence_text, tree = list(extractor.sentence_trees())[frame.sentence_id]
            for arg in frame.args:
                extractor.headword(arg, tree)

        self.assertEqual(extractor.get_class("soda"), "physical_entity.n.01")
        #self.assertEqual(extractor.get_class("i"), "pronoun")
        
        # get_class should return None for words out of WordNet
        self.assertEqual(extractor.get_class("abcde"), None)

    def sample_args(self, num_sample = 10):
        """Not a unit test. Returns a random sample of argument/node/headword to help.
        
        :param num_sample: The requested number of results
        :type num_sample: int
        :returns: (str, str, str) List -- Some examples of (arg, best_node_text, headword)
        """
        extractor = HeadWordExtractor(options.framenet_parsed)

        sample = []
        for filename in options.fulltext_annotations:
            if filename in self.bad_files: continue
            
            extractor.load_file(options.framenet_parsed + filename)
            
            reader = framenetreader.FulltextReader(options.fulltext_corpus+filename, False)
            previous_sentence = 0

            for frame in reader.frames:
                if (filename, frame.sentence_id) in self.bad_sentences: continue
   
                if frame.sentence_id != previous_sentence:
                    sentence_id, sentence_text, tree = list(extractor.sentence_trees())[frame.sentence_id]
                
                for arg in frame.args:
                    if not arg.instanciated: continue
                    node = extractor.best_node(arg.text)
                    sample.append((arg.text, node.flat(), node.word))
                
                previous_sentence = frame.sentence_id
                
        random.shuffle(sample)
        return sample[0:num_sample]
    
    def test_1(self):
        filename = "ANC__110CYL067"
        extractor = HeadWordExtractor()
        extractor.load_file(options.framenet_parsed / (filename + ".conll"))

        reader = framenetreader.FulltextReader(options.fulltext_corpus / (filename + ".xml"), False)

        frame = reader.frames[1]
        sentence_id, sentence_text, tree = list(extractor.sentence_trees())[frame.sentence_id]
        self.assertEqual(extractor.headword(frame.args[0], tree), "you")

        frame = reader.frames[25]
        sentence_id, sentence_text, tree = list(extractor.sentence_trees())[frame.sentence_id]
        self.assertEqual(extractor.headword(frame.args[0], tree), "people")

if __name__ == "__main__":
    # The -s option makes the script display some examples of results
    # or write them in a file using pickle
    cli_options = getopt.getopt(sys.argv[1:], "s:", [])
    num_sample = 0
    filename = ""
    
    for opt, value in cli_options[0]:
        if opt == "-s":
            if len(cli_options[1]) >= 1:
                filename = cli_options[1][0]
            num_sample = int(value)
        
    if num_sample > 0:
        tester = HeadWordExtractorTest()
        result = tester.sample_args(num_sample)
        if filename == "":
            for exemple in result:
                print("{}\n{}\n{}\n".format(exemple[0], exemple[1], exemple[2]))
        else:
            with open(filename, "wb") as picklefile:
                pickle.dump(result, picklefile)

