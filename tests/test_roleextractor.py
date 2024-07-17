#!/usr/bin/env python3

import unittest

import framenet
from framenetframe import FrameInstance, Predicate, Arg
from roleextractor import _correct_num_tags

class RoleExtractorTest(unittest.TestCase):
    def test_num_replacements(self):
        initial_sentence = ("She tells me that the <num> , <num> people we helped find"
                            " jobs in <num> earned approximately $ <num>"
                            " million dollars .")
        final_sentence = ("She tells me that the 3,666 people we helped find"
                          " jobs in 1998 earned approximately $ 49"
                          " million dollars .")
                          
        initial_predicate = Predicate(64, 69, "earned", "earn")
        final_predicate = Predicate(56, 61, "earned", "earn")
        
        initial_args = [
            Arg(18, 62, "the <num> people we helped find jobs in <num>",
                "role1", True, "phrase_type"),
            Arg(71, 107, "approximately $ <num> million dollars",
                "role2", True, "phrase_type")
        ]
        final_args = [
            Arg(18, 54, "the 3,666 people we helped find jobs in 1998",
                "role1", True, "phrase_type"),
            Arg(62, 95, "approximately $ 49 million dollars",
                "role2", True, "phrase_type")
        ]
        words = []
        
        frame = FrameInstance(initial_sentence, initial_predicate, initial_args,
            words, "fn_frame_name")
        
        _correct_num_tags(frame, final_sentence)
        self.assertEqual(frame.sentence, final_sentence)
        self.assertEqual(frame.predicate, final_predicate)
        self.assertEqual(frame.args, final_args)

if __name__ == "__main__":
    import verbnetreader
    from argguesser import ArgGuesser
    from rolematcher import VnFnRoleMatcher
    from stats import stats_data

    role_matcher = VnFnRoleMatcher(paths.Paths.VNFN_MATCHING,
                                   framenet.FrameNet())
    verbnet_classes = verbnetreader.VerbnetReader(paths.Paths.verbnet_path("eng")).classes
    arg_guesser = ArgGuesser(verbnet_classes)

    frames = []
    for filename in FNAllReader.fulltext_parses():
        for frame in arg_guesser.frame_instances_from_file(filename):
            frames.append(frame)

    frames = fill_gold_roles(frames, verbnet_classes, role_matcher)

    print("\nExtracted {} correct and {} incorrect (non-annotated) frames.\n"
          "Did not extract {} annotated frames ({} had a predicate not in VerbNet).\n"
          "Extracted {} correct, {} partial-match and {} incorrect arguments.\n"
          "Did not extract {} annotated arguments ({} had a predicate not in VerbNet).\n".format(
          stats_data["frame_extracted_good"], stats_data["frame_extracted_bad"],
          stats_data["frame_not_extracted"], stats_data["frame_not_extracted_not_verbnet"],
          stats_data["arg_extracted_good"], stats_data["arg_extracted_partial"],
          stats_data["arg_extracted_bad"],
          stats_data["arg_not_extracted"], stats_data["arg_not_extracted_not_verbnet"]
    ))
