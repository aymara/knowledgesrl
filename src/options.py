#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import probabilitymodel
import paths

import getopt
import sys


matching_algorithm = "sync_predicates"
core_args_only = True
gold_args = True
heuristic_rules = False
debug = False
bootstrap = False
probability_model = "predicate_slot"
dump = False
dump_file = ""

conll_input = None
conll_output = sys.stdout

passive = True
use_test_set = False
corpus_lu = False
semrestr = False
fulltext_corpus = paths.FRAMENET_FULLTEXT
framenet_parsed = paths.FRAMENET_PARSED

fulltext_annotations = sorted(fulltext_corpus.glob('*.xml'))
fulltext_parses = sorted(framenet_parsed.glob('*.conll'))

options = getopt.getopt(sys.argv[1:], "d:", [
    "baseline", "fmatching-algo=", "add-non-core-args", "help", "model=",
    "bootstrap", "no-gold-args", "heuristic-rules", "dump", "conll_input=",
    "conll_output=", "no-passive", "baseline", "test-set", "lu",
    "semantic-restrictions"])

display_usage = False

usage_str = """Usage: main.py [--baseline] [-d num_sample]
[--fmatching-algo=algo] [--model=probability_model] [--add-non-core-args]
[--bootstrap] [--no-gold-args] [--heuristic-rules] [--dump filename]
[--conll_input filename] [--conll_output filename] [--no-passive] [--test-set]
[--lu] [--semantic-restrictions] [--help]"""

for opt, value in options[0]:
    # Removes our enhancements
    if opt == "--baseline":
        passive = False
    elif opt == "-d":
        debug = True
        value = 0 if value == "" else int(value)
        if value > 0:
            n_debug = value
    elif opt == "--fmatching-algo":
        matching_algorithm = value
    elif opt == "--add-non-core-args":
        core_args_only = False
    elif opt == "--model":
        if not value in probabilitymodel.models:
            raise Exception("Unknown model {}".format(value))
        probability_model = value
    elif opt == "--bootstrap":
        bootstrap = True
    elif opt == "--no-gold-args":
        gold_args = False
    elif opt == "--heuristic-rules":
        heuristic_rules = True

    elif opt == "--conll_input":
        conll_input = value
        gold_args = False
    elif opt == "--conll_output":
        conll_output = value

    elif opt == "--dump":
        if len(options[1]) > 0:
            dump = True
            dump_file = options[1][0]
        else:
            display_usage = True
    elif opt == "--no-passive":
        passive = False 
    elif opt == "--test-set":
        use_test_set = True
        fulltext_corpus = paths.FRAMENET_FULLTEXT_EVALUATION
        framenet_parsed = paths.FRAMENET_PARSED_EVALUATION
    elif opt == "--lu":
        corpus_lu = True
        fulltext_corpus = paths.FRAMENET_LU
        framenet_parsed = paths.FRAMENET_LU_PARSED
    elif opt == "--semantic-restrictions":
        semrestr = True
    elif opt == "--help":
        display_usage = True

if conll_input is not None and conll_output == sys.stdout:
    print("--conll_input should be used with --conll_output. Aborting")
    display_usage = True
            
if display_usage:
    print(usage_str)
    sys.exit(-1)
