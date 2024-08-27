#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import options
import probabilitymodel

def parse_arguments():
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
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    print(args)