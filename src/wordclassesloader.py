#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from nltk.corpus import wordnet as wn
import pickle
import getopt
import sys

handle_wordclasses, handle_morph = True, False
options = getopt.getopt(sys.argv[1:], "", ["morph"])
for opt,value in options[0]:
    if opt == "--morph":
        handle_wordclasses, handle_morph = False, True

with open("temp_wordlist", "rb") as picklefile:
    words = pickle.load(picklefile)

if handle_wordclasses:
    entity_synset = "entity.n.01"

    wordclasses = {}

    for word in words:
        try:
            synsets = wn.synsets(word)
        except Exception:
            continue
            
        if(len(synsets) == 0): continue
        
        hypernyms = synsets[0].hypernym_paths()[0]
        
        if hypernyms[0].name == entity_synset and len(hypernyms) > 1:
            wordclasses[word] = hypernyms[1].name
        else: 
            wordclasses[word] = hypernyms[0].name

    with open("temp_wordclasses", "wb") as picklefile:
        pickle.dump(wordclasses, picklefile)
        
if handle_morph:
    base_forms = {}
    
    for word in words:
        base_form = wn.morphy(word, "v")
        if base_form != None: base_forms[word] = base_form
    
    with open("temp_morph", "wb") as picklefile:
        pickle.dump(base_forms, picklefile)
