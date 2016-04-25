#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paths
import optionsparsing
import sys
import enum
import logging

class FrameLexicon(enum.Enum):
    VerbNet = 1
    FrameNet = 2

class Options:

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

    framelexicon = FrameLexicon.VerbNet
    framelexicons = {
        'framenet': FrameLexicon.FrameNet,
        'verbnet' : FrameLexicon.VerbNet
        }

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

    fulltext_corpus = None
    framenet_parsed = None

    fulltext_annotations = None
    fulltext_parses = None


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

    # Chose frame lexicon to use for output, defaults to verbnet
    --frame-lexicon=[verbnet,framenet]

    # Log level
    --log=[debug, info, warning, error, critical]

    # Display this usage message
    --help"""

    def __init__(self):
        display_usage = False
    
        for opt, value in optionsparsing.Options.options[0]:
            if opt == "--language":
                Options.language = value
            elif opt == "--best-gold":
                Options.argument_identification = False
                Options.passivize = True
                Options.semrestr = True
                Options.bootstrap = True
            elif opt == "--best-auto":
                Options.argument_identification = True
                Options.passivize = True
                Options.semrestr = True
                Options.bootstrap = True
            elif opt == "--fmatching-algo":
                Options.matching_algorithm = value
            elif opt == "--add-non-core-args":
                Options.add_non_core_args = True
            elif opt == "--model":
                if value not in probabilitymodel.models:
                    raise Exception("Unknown model {}".format(value))
                probability_model = value
            elif opt == "--bootstrap":
                Options.bootstrap = True
            elif opt == "--argument-identification":
                Options.argument_identification = True
            elif opt == "--heuristic-rules":
                Options.heuristic_rules = True
            elif opt == "--semantic-restrictions":
                Options.semrestr = True
            elif opt == "--wordnet-restrictions":
                Options.wordnetrestr = True
            elif opt == "--passivize":
                Options.passivize = True

            elif opt == "--corpus":
                Options.corpus = value
            elif opt == "--conll_input":
                Options.conll_input = value
                Options.argument_identification = True
            elif opt == "--conll_output":
                Options.conll_output = value
            elif opt == "--training-set":
                Options.use_training_set = True
            elif opt == "--lu":
                Options.corpus_lu = True
            elif opt == "--dump":
                if len(optionsparsing.options[1]) > 0:
                    Options.dump = True
                    Options.dump_file = optionsparsing.options[1][0]
                else:
                    display_usage = True
            elif opt == "--loglevel":
                if value not in Options.loglevels:
                    raise Exception("Unknown log level {}. loglevels are: {}".format(value,loglevels))
                Options.loglevel = Options.loglevels[value]
            elif opt == "--frame-lexicon":
                if value not in Options.framelexicons:
                    raise Exception("Unknown frame lexicon {}. known values are: {}".format(value,Options.framelexicons))
                Options.framelexicon = Options.framelexicons[value]
            elif opt == "-d":
                Options.debug = True
                Options.value = 0 if value == "" else int(value)
                if value > 0:
                    Options.n_debug = value
            elif opt == "--help":
                display_usage = True

        if display_usage:
            print(Options.usage_str)
            sys.exit(1)

        Options.fulltext_corpus = paths.Paths.framenet_fulltext(Options.language)
        Options.framenet_parsed = paths.Paths.FRAMENET_PARSED
        if Options.corpus_lu:
            Options.fulltext_corpus = paths.Paths.framenet_lu(Options.language)
            Options.framenet_parsed = paths.Paths.FRAMENET_LU_PARSED

        if Options.use_training_set:
            Options.fulltext_annotations = sorted([f for f in Options.fulltext_corpus.glob('*.xml') if f.stem not in Options.framenet_test_set])
            Options.fulltext_parses = sorted([f for f in Options.framenet_parsed.glob('*.conll') if f.stem not in Options.framenet_test_set])
                
        Options.fulltext_annotations = sorted([f for f in Options.fulltext_corpus.glob('*.xml') if f.stem in Options.framenet_test_set])
        Options.fulltext_parses = sorted([f for f in Options.framenet_parsed.glob('*.conll') if f.stem in Options.framenet_test_set])
            