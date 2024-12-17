#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import enum
import logging
import paths
import sys

import probabilitymodel


class FrameLexicon(enum.Enum):
    VerbNet = 1
    FrameNet = 2


class Options:

    predicate_pos = [
        "VERB",  # UD
        "md", "MD",
        "VB", "VBD", "VBG", "VBN", "VBP", "VBZ",
        "VV", "VVD", "VVG", "VVN", "VVP", "VVZ",
        "VH", "VHD", "VHG", "VHN", "VHP", "VHZ",
        # French tags:
        "V", "VIMP", "VINF", "VPP", "VPR", "VS"]

    matching_algorithm: str = "sync_predicates"
    language: str = None  # Init from args

    model: str = probabilitymodel.models[0]
    argument_identification: bool = True
    heuristic_rules: bool = False
    bootstrap: bool = False
    probability_model = None
    passivize: bool = False
    semrestr: bool = False
    wordnetrestr: bool = False
    corpus = None  # Init from args
    loglevel: int = logging.WARNING

    framelexicon = "VerbNet"
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
        # TODO Complete the conditional initialization with a possibly empty
        # args
        display_usage = False
        Options.language = args.language if hasattr(args, "language") else "eng"
        Options.argument_identification = hasattr(args, "no_argument_identification") and not args.no_argument_identification
        if hasattr(args, "best_gold") and args.best_gold:
            Options.argument_identification = False
            Options.passivize = True
            Options.semrestr = True
            Options.bootstrap = True
        if hasattr(args, "best_auto") and args.best_auto:
            Options.argument_identification = True
            Options.passivize = True
            Options.semrestr = True
            Options.bootstrap = True
        if hasattr(args, "matching_algorithm"):
            Options.matching_algorithm = args.matching_algorithm
        if hasattr(args, "add_non_core_args"):
            Options.add_non_core_args = args.add_non_core_args
        if hasattr(args, "model"):
            Options.probability_model = args.model
        if hasattr(args, "bootstrap"):
            Options.bootstrap = args.bootstrap
        if hasattr(args, "heuristic_rules"):
            Options.heuristic_rules = args.heuristic_rules
        if hasattr(args, "semantic_restrictions"):
            Options.semrestr = args.semantic_restrictions
        if hasattr(args, "wordnet_restrictions"):
            Options.wordnetrestr = args.wordnet_restrictions
        if hasattr(args, "passivize"):
            Options.passivize = args.passivize
        if hasattr(args, "corpus"):
            Options.corpus = args.corpus
        if hasattr(args, "conll_output"):
            Options.conll_output = args.conll_output
        if hasattr(args, "training_set"):
            Options.use_training_set = args.training_set
        if hasattr(args, "lu"):
            Options.corpus_lu = args.lu
        if hasattr(args, "dump") and args.dump is not None:
            Options.dump = True
            Options.dump_file = args.dump

        Options.loglevel = Options.loglevels[
            args.loglevel if hasattr(args, "loglevel") else "info"]
        if hasattr(args, "frame_lexicon") and args.frame_lexicon is not None:
            Options.framelexicon = Options.framelexicons[args.frame_lexicon]

        framenet_parsed = paths.Paths.FRAMENET_PARSED
        fulltext_corpus = paths.Paths.framenet_fulltext(Options.language)

        if Options.corpus_lu:
            fulltext_corpus = paths.Paths.framenet_lu(Options.language)
            framenet_parsed = paths.Paths.FRAMENET_LU_PARSED

        if Options.use_training_set:
            Options.fulltext_annotations = sorted(
                [f for f in fulltext_corpus.glob('*.xml')
                 if f.stem not in Options.framenet_test_set])
            Options.fulltext_parses = sorted(
                [f for f in framenet_parsed.glob('*.conll')
                 if f.stem not in Options.framenet_test_set])
        else:
            Options.fulltext_annotations = sorted(
                [f for f in fulltext_corpus.glob('*.xml')
                 if f.stem in Options.framenet_test_set])
            Options.fulltext_parses = sorted(
                [f for f in framenet_parsed.glob('*.conll')
                 if f.stem in Options.framenet_test_set])
