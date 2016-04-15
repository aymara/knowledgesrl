#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import probabilitymodel
import paths
import optionsparsing
import getopt
import sys

import logging

matching_algorithm = "sync_predicates"

language = 'eng'

argument_identification = False
heuristic_rules = False
bootstrap = False
probability_model = None
passivize = False
semrestr = False
wordnetrestr = False
corpus = 'FrameNet'
loglevel = logging.WARNING

# usually, a negative option is a bad idea, but 'non-core' is a thing in
# FrameNet
add_non_core_args = False

conll_input = None
conll_output = None
use_training_set = False
corpus_lu = False

debug = False
dump = False
dump_file = ""

loglevels = {
    'debug':logging.DEBUG, 
    'info':logging.INFO, 
    'warning':logging.WARNING, 
    'error':logging.ERROR, 
    'critical':logging.CRITICAL,
}

framenet_test_set = [
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

fulltext_annotations = sorted([f for f in fulltext_corpus.glob('*.xml') if f.stem in framenet_test_set])
fulltext_parses = sorted([f for f in framenet_parsed.glob('*.conll') if f.stem in framenet_test_set])


display_usage = False

# TODO ask argparse to generate this?
usage_str = """Usage:
======

# Annotate a single file
main.py --conll_input=parsed_file.txt --conll_output=annotated_file.txt [options]
# Annotate FrameNet test set
main.py [options]
# Annotate FrameNet training set
main.py --training-set [options]
# Annotate FrameNet example corpus
main.py --lu [options]

Options:
--------

# language
--language=[eng,fre]

# Best configuration for gold and auto args
--best-gold, --best-auto

# Handle passive sentences
--passivize
# Restrict to phrases that obey VerbNet restrictions
--semantic-restrictions

# Select a frame matching algorithm
--fmatching-algo=[baseline, sync_predicates, stop_on_fail]

# Probability models
--model=[predicate_slot, default, slot, slot_class, vnclass_slot]
--bootstrap

# Identify arguments automatically
--argument-identification
--heuristic-rules  # use Lang&Lapata heuristics to find args

# Consider non-core-arg with gold arguments (why?)
--add-non-core-args

# Dump annotation for comparisong
--dump

# Log level
--log=[debug, info, warning, error, critical]

# Display this usage message
--help"""

for opt, value in optionsparsing.options[0]:
    if opt == "--language":
        language = value
    elif opt == "--best-gold":
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
        if value not in probabilitymodel.models:
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
    elif opt == "--wordnet-restrictions":
        wordnetrestr = True
    elif opt == "--passivize":
        passivize = True

    elif opt == "--corpus":
        corpus = value
    elif opt == "--conll_input":
        conll_input = value
        argument_identification = True
    elif opt == "--conll_output":
        conll_output = value
    elif opt == "--training-set":
        use_training_set = True
        fulltext_annotations = sorted([f for f in fulltext_corpus.glob('*.xml') if f.stem not in framenet_test_set])
        fulltext_parses = sorted([f for f in framenet_parsed.glob('*.conll') if f.stem not in framenet_test_set])
    elif opt == "--lu":
        corpus_lu = True
        fulltext_corpus = paths.FRAMENET_LU
        framenet_parsed = paths.FRAMENET_LU_PARSED

    elif opt == "--dump":
        if len(optionsparsing.options[1]) > 0:
            dump = True
            dump_file = optionsparsing.options[1][0]
        else:
            display_usage = True
    elif opt == "--loglevel":
        if value not in loglevels:
            raise Exception("Unknown log level {}. loglevels are: {}".format(value,loglevels))
        loglevel = loglevels[value]
    elif opt == "-d":
        debug = True
        value = 0 if value == "" else int(value)
        if value > 0:
            n_debug = value
    elif opt == "--help":
        display_usage = True

if conll_input is not None and conll_output is None:
    print("--conll_input requires --conll_output. Aborting")
    display_usage = True

if display_usage:
    print(usage_str)
    sys.exit(-1)
