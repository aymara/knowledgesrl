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
use_training_set = False
corpus_lu = False

debug = False
dump = False
dump_file = ""

test_set = [
    'ANC__110CYL067',
    'ANC__110CYL068',
    'ANC__112C-L013',
    'ANC__IntroHongKong',
    'ANC__StephanopoulosCrimes',
    'ANC__WhereToHongKong',
    'KBEval__Brandeis',
    'KBEval__Stanford',
    'KBEval__atm',
    'KBEval__cycorp',
    'KBEval__parc',
    'KBEval__utd-icsi',
    'LUCorpus-v0.3__20000410_nyt-NEW',
    'LUCorpus-v0.3__AFGP-2002-602187-Trans',
    'LUCorpus-v0.3__IZ-060316-01-Trans-1',
    'LUCorpus-v0.3__SNO-525',
    'LUCorpus-v0.3__enron-thread-159550',
    'LUCorpus-v0.3__sw2025-ms98-a-trans.ascii-1-NEW',
    'Miscellaneous__Hound-Ch14',
    'Miscellaneous__SadatAssassination',
    'NTI__NorthKorea_Introduction',
    'NTI__Syria_NuclearOverview',
    'PropBank__AetnaLifeAndCasualty',
]

fulltext_corpus = paths.FRAMENET_FULLTEXT
framenet_parsed = paths.FRAMENET_PARSED

fulltext_annotations = sorted([f for f in fulltext_corpus.glob('*.xml') if f.stem in test_set])
fulltext_parses = sorted([f for f in framenet_parsed.glob('*.conll') if f.stem in test_set])

options = getopt.getopt(sys.argv[1:], "d:", [
    # "manual use"
    "best-gold", "best-auto",
    # tuning algorithms
    "fmatching-algo=", "add-non-core-args", "model=", "bootstrap",
    "argument-identification", "heuristic-rules", "passivize", "semantic-restrictions",
    # what do we annotate?
    "conll_input=", "conll_output=", "training-set", "lu",
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
        semrestr = True
        bootstrap = True
    elif opt == "--best-auto":
        argument_identification = True
        passivize = True
        semrestr = True
        bootstrap = True
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
    elif opt == "--training-set":
        use_training_set = True
        fulltext_annotations = sorted([f for f in fulltext_corpus.glob('*.xml') if f.stem not in test_set])
        fulltext_parses = sorted([f for f in framenet_parsed.glob('*.conll') if f.stem not in test_set])
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
