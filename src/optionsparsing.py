#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Parse options and gives access to them """

import getopt

class Options:
    options = []
    
    def __init__(self, argv):
        Options.options = getopt.getopt(argv, "d:", [
            # language
            'language=',
            # "manual use"
            "best-gold", "best-auto",
            # tuning algorithms
            "fmatching-algo=", "add-non-core-args", "model=", "bootstrap",
            "argument-identification", "heuristic-rules", "passivize", 
            "semantic-restrictions", "wordnet-restrictions",
            # what do we annotate?
            "conll_input=", "conll_output=", "corpus=", "training-set", "lu",
            # what kind of output do we want
            "frame-lexicon=",
            # meta
            "loglevel=", "dump", "help"])
        
