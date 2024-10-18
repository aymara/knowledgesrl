#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import enum
import logging
import paths
import sys


class FrameLexicon(enum.Enum):
    VerbNet = 1
    FrameNet = 2


class Options:

    matching_algorithm: str = "sync_predicates"

    language: str = None  # Init from args

    argument_identification: bool = False
    heuristic_rules: bool = False
    bootstrap: bool = False
    probability_model = None
    passivize: bool = False
    semrestr: bool = False
    wordnetrestr: bool = False
    corpus = None  # Init from args
    loglevel: int = logging.WARNING

    framelexicon = None  # Init from args
    framelexicons = {
        'FrameNet': FrameLexicon.FrameNet,
        'VerbNet': FrameLexicon.VerbNet
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
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL,
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

    fulltext_annotations = None
    fulltext_parses = None

    #@classmethod
    def __init__(self, args: argparse.Namespace) -> None:
        display_usage = False
        Options.language = args.language
        Options.argument_identification = not args.no_argument_identification
        if args.best_gold:
            Options.argument_identification = False
            Options.passivize = True
            Options.semrestr = True
            Options.bootstrap = True
        if args.best_auto:
            Options.argument_identification = True
            Options.passivize = True
            Options.semrestr = True
            Options.bootstrap = True
        Options.matching_algorithm = args.matching_algorithm
        Options.add_non_core_args = args.add_non_core_args
        probability_model = args.model
        Options.bootstrap = args.bootstrap
        Options.heuristic_rules = args.heuristic_rules
        Options.semrestr = args.semantic_restrictions
        Options.wordnetrestr = args.wordnet_restrictions
        Options.passivize = args.passivize
        Options.corpus = args.corpus
        Options.conll_output = args.conll_output
        Options.use_training_set = args.training_set
        Options.corpus_lu = args.lu
        if args.dump is not None:
            Options.dump = True
            Options.dump_file = args.dump

        Options.loglevel = Options.loglevels[args.loglevel]
        Options.framelexicon = Options.framelexicons[args.frame_lexicon]

        framenet_parsed = paths.Paths.FRAMENET_PARSED
        fulltext_corpus = paths.Paths.framenet_fulltext(args.language)

        if Options.corpus_lu:
            fulltext_corpus = paths.Paths.framenet_lu(args.language)
            framenet_parsed = paths.Paths.FRAMENET_LU_PARSED

        if Options.use_training_set:
            print('option1')
            Options.fulltext_annotations = sorted(
                [f for f in fulltext_corpus.glob('*.xml')
                 if f.stem not in Options.framenet_test_set])
            Options.fulltext_parses = sorted(
                [f for f in framenet_parsed.glob('*.conll')
                 if f.stem not in Options.framenet_test_set])
        else:
            print('pilulebleue')
            Options.fulltext_annotations = sorted(
                [f for f in fulltext_corpus.glob('*.xml')
                if f.stem in Options.framenet_test_set])
            Options.fulltext_parses = sorted(
                [f for f in framenet_parsed.glob('*.conll')
                if f.stem in Options.framenet_test_set])


