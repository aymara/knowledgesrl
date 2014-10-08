#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import probabilitymodel
import paths

import getopt
import sys


matching_algorithm = "sync_predicates"

argument_identification = False
heuristic_rules = False
bootstrap = False
probability_model = None
passivize = False
semrestr = False
# usually, a negative option is a bad idea, but 'non-core' is a thing in
# FrameNet
add_non_core_args = False

conll_input = None
conll_output = sys.stdout
use_test_set = False
corpus_lu = False

debug = False
dump = False
dump_file = ""

fulltext_corpus = paths.FRAMENET_FULLTEXT
framenet_parsed = paths.FRAMENET_PARSED

fulltext_annotations = sorted(fulltext_corpus.glob('*.xml'))
fulltext_parses = sorted(framenet_parsed.glob('*.conll'))

options = getopt.getopt(sys.argv[1:], "d:", [
    # "manual use"
    "best-gold", "best-auto",
    # tuning algorithms
    "fmatching-algo=", "add-non-core-args", "model=", "bootstrap",
    "argument-identification", "heuristic-rules", "passivize", "semantic-restrictions",
    # what do we annotate?
    "conll_input=", "conll_output=", "test-set", "lu",
    # meta
    "dump", "help"])

display_usage = False

usage_str = """Usage:
    main.py options # annotates FrameNet
    main.py --conll_input=parsed_file.txt --conll_output=annotated_file.txt"""

for opt, value in options[0]:
    if opt == "--best-gold":
        argument_identification = False
        passivize = True
        probability_model = "predicate_slot"
    elif opt == "--best-auto":
        argument_identification = True
        passivize = True
        probability_model = "predicate_slot"

    elif opt == "--fmatching-algo":
        matching_algorithm = value
    elif opt == "--add-non-core-args":
        add_non_core_args = True
    elif opt == "--model":
        if not value in probabilitymodel.models:
            raise Exception("Unknown model {}".format(value))
        probability_model = value
    elif opt == "--bootstrap":
        bootstrap = True
    elif opt == "--argument-identification":
        argument_identification = True
    elif opt == "--heuristic-rules":
        heuristic_rules = True
    elif opt == "--semantic-restrictions":
        semrestr = True
    elif opt == "--passivize":
        passivize = True

    elif opt == "--conll_input":
        conll_input = value
        argument_identification = True
    elif opt == "--conll_output":
        conll_output = value
    elif opt == "--dump":
        if len(options[1]) > 0:
            dump = True
            dump_file = options[1][0]
        else:
            display_usage = True
    elif opt == "--test-set":
        use_test_set = True
        fulltext_corpus = paths.FRAMENET_FULLTEXT_EVALUATION
        framenet_parsed = paths.FRAMENET_PARSED_EVALUATION
    elif opt == "--lu":
        corpus_lu = True
        fulltext_corpus = paths.FRAMENET_LU
        framenet_parsed = paths.FRAMENET_LU_PARSED

    elif opt == "-d":
        debug = True
        value = 0 if value == "" else int(value)
        if value > 0:
            n_debug = value
    elif opt == "--help":
        display_usage = True

if conll_output != sys.stdout and conll_input is not None:
    print("--conll_output should be used with --conll_input. Aborting")
    display_usage = True

if display_usage:
    print(usage_str)
    sys.exit(-1)
