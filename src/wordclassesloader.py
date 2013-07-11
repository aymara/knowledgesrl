#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""This is the python2 script used to interact with nltk. It can:
  * computes the word classes of head nouns for the bootstrap algorithm
  * retrieve the infinitive forms of verbs for the argguesser module
"""

from nltk.corpus import wordnet as wn
import pickle
import getopt
import sys

# Read the arguments to know which of the two tasks we have to do
handle_wordclasses, handle_morph, handle_restr = True, False, False
options = getopt.getopt(sys.argv[1:], "", ["morph"])
for opt,value in options[0]:
    if opt == "--morph":
        handle_wordclasses, handle_morph = False, True

if handle_wordclasses:
    # The class of a word is the highest hypernym, except
    # when this is "entity". In this case, we take the second
    # highest hypernym
    
    # Load input data
    with open("temp_wordlist", "rb") as picklefile:
        words = pickle.load(picklefile)

    entity_synset = "entity.n.01"

    wordclasses = {}

    for word in words:
        synsets = wn.synsets(word)
        
        if(len(synsets) == 0): continue

        # Since WSD is complicated, we choose the first synset.
        # Taking the path of the first element of the synset is a less
        # important decision, since the two highest nodes are very likely
        # to be identical for two words in the same synset
        hypernyms = synsets[0].hypernym_paths()[0]
        
        if hypernyms[0].name == entity_synset and len(hypernyms) > 1:
            wordclasses[word] = hypernyms[1].name
        else:
            wordclasses[word] = hypernyms[0].name

    # Save output
    with open("temp_wordclasses", "wb") as picklefile:
        pickle.dump(wordclasses, picklefile)
        
if handle_morph:
    # Load input data
    with open("temp_wordlist", "rb") as picklefile:
        words = pickle.load(picklefile)
        
    # Second task : obtaining the infinitive forms of a list of verbs
    base_forms = {}
    
    for word in words:
        base_form = wn.morphy(word, "v")
        if base_form != None: base_forms[word] = base_form
    
    # Save output
    with open("temp_morph", "wb") as picklefile:
        pickle.dump(base_forms, picklefile)
