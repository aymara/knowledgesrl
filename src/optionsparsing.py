#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getopt
import sys

options = getopt.getopt(sys.argv[1:], "d:", [
    # language
    'language=',
    # "manual use"
    "best-gold", "best-auto",
    # tuning algorithms
    "fmatching-algo=", "add-non-core-args", "model=", "bootstrap",
    "argument-identification", "heuristic-rules", "passivize", "semantic-restrictions", "wordnet-restrictions",
    # what do we annotate?
    "conll_input=", "conll_output=", "corpus=", "training-set", "lu",
    # meta
    "loglevel=", "dump", "help"])

