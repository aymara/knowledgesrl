#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from nltk.corpus import wordnet as wn
import pickle

entity_synset = "entity.n.01"

wordclasses = {}

with open("temp_wordlist", "rb") as picklefile:
    words = pickle.load(picklefile)

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
