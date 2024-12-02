#!/usr/bin/env python3

import sys
import argparse
import options
import probabilitymodel
###OLD ###

import unittest
import framenet
import paths
from framenetframe import FrameInstance, Predicate, Arg
from roleextractor import _correct_num_tags, fill_gold_roles
from framenetallreader import FNAllReader

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

    # parse command line arguments
    parser = argparse.ArgumentParser(
        description="""
        Depending on the options used, can
        # Annotate a single file
        knowledgesrl.py --conll_input=parsed_file.conll
                --conll_output=annotated_file.conll [options]

        # Annotate FrameNet test set
        knowledgesrl.py [options]

        # Annotate FrameNet training set
        knowledgesrl.py --training-set [options]

        # Annotate FrameNet example corpus
        knowledgesrl.py --lu [options]
        """)
    parser.add_argument("--language", "-l", type=str, choices=["eng", "fre"],
                        default="eng",
                        help="Name of the CoNLL-U file with the gold data.")
    parser.add_argument("--best-gold", action="store_true",
                        help=" Best configuration for gold.")
    parser.add_argument("--best-auto", action="store_true",
                        help="Best configuration for auto.")
    parser.add_argument("--matching-algorithm", type=str,
                        choices=["baseline", "sync_predicates",
                                    "stop_on_fail"],
                        default="sync_predicates",
                        help="Select a frame matching algorithm.")
    parser.add_argument("--add-non-core-args", action="store_true",
                        help="Consider non-core-arg with gold arguments (why?)")
    parser.add_argument("--model", type=str,
                        choices=probabilitymodel.models,
                        help="Probability models.")
    parser.add_argument("--bootstrap", action="store_true",
                        help="")
    parser.add_argument("--no-argument-identification", action="store_true",
                        help="Identify arguments automatically")
    parser.add_argument("--heuristic-rules", action="store_true",
                        help="Use Lang and Lapata heuristics to find args.")
    parser.add_argument("--passivize", action="store_true",
                        help="Handle passive sentences")
    parser.add_argument("--semantic-restrictions", action="store_true",
                        help="Restrict to phrases that obey VerbNet restrictions")
    parser.add_argument("--wordnet-restrictions", action="store_true",
                        help="Restrict to phrases that obey WordNet restrictions")
    # what do we annotate?
    parser.add_argument("--conll-input", "-i", type=str, default="",
                        help="File to annotate.")
    parser.add_argument("--conll-output", "-o", type=str, default=None,
                        help="File to write result on. Default to stdout.")
    parser.add_argument("--corpus", type=str,
                        choices=["FrameNet", "dicoinfo_fr"],
                        default=None,
                        help="")
    parser.add_argument("--training-set", action="store_true",
                        help="To annotate FrameNet training set.")
    parser.add_argument("--lu", action="store_true",
                        help="To annotate FrameNet example corpus.")
    # what kind of output do we want
    parser.add_argument("--frame-lexicon", type=str,
                        choices=["VerbNet", "FrameNet"],
                        default="VerbNet",
                        help="Chose frame lexicon to use for output.")
    # meta
    parser.add_argument("--loglevel", type=str,
                        choices=['debug', 'info', 'warning', 'error',
                                    'critical'],
                        default='warning',
                        help="Log level.")
    parser.add_argument("--dump", type=str, default=None,
                        help="File where to dump annotations for "
                                "comparisons.")

    # parse command line arguments
    args = parser.parse_args()
    #We initialize the frames with framenetallreader
    frames = []
    extractor = FNAllReader()
    opt = options.Options(args)
    for annotation_file, parse_file in zip(opt.fulltext_annotations, opt.fulltext_parses):
        frames.extend(extractor.iter_frames(annotation_file, parse_file))
    # We create the annotations and parsed_files list
    List_L = [frame.args for frame in frames]
    annotations = [List_L[i][0] if len(List_L[i]) > 1 else None for i in range(len(List_L))]
    parsed_files = [List_L[i][1] if len(List_L[i]) > 1 else None for i in range(len(List_L))]
    frames = fill_gold_roles(frame_instances=frames, annotation_file=opt.fulltext_annotations,
                    parsed_conll_file=opt.fulltext_parses, verbnet_classes=verbnet_classes, role_matcher=role_matcher)

    print("\nExtracted {} correct and {} incorrect (non-annotated) frames.\n"
          "Did not extract {} annotated frames ({} had a predicate not in VerbNet).\n"
          "Extracted {} correct and {} incorrect arguments.\n" # , {} partial-match
          "Did not extract {} annotated arguments ({} had a predicate not in VerbNet).\n".format(
          stats_data["frame_extracted_good"], stats_data["frame_extracted_bad"],
          stats_data["frame_not_extracted"], stats_data["frame_not_extracted_not_verbnet"],
          stats_data["arg_extracted_good"], #stats_data["arg_extracted_partial"], TODO check wether if arg_extracted_partial does exist
          stats_data["arg_extracted_bad"],
          stats_data["arg_not_extracted"], stats_data["arg_not_extracted_not_verbnet"]
    ))
    unittest.main()
