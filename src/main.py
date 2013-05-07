#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import framenetreader
from framestructure import *
import verbnetreader
import framematcher
import rolematcher
import os
import sys
import random
from collections import Counter

corpus_path = "../data/fndata-1.5/fulltext/"
verbnet_path = "../data/verbnet-3.2/"
debug = False

num_files = 0
num_frames = 0
num_good_frames = 0
num_args = 0
num_good_args = 0
num_resolved = 0
num_discarded = 0

num_resolved_correct = 0
num_ambiguous_possible = 0
num_resolved_bad = 0
num_ambiguous_impossible = 0      
   
verbnet_errors = []
not_found = []
empty_framenet_frames = []
empty_verbnet_frames = []
ignored_layers = []
ignored_predicate_args = []
phrase_not_found = []
missing_predicate_data = []
debug_data = []
unable_to_match = []

verbnet_reader = verbnetreader.VerbnetReader(verbnet_path)
verbnet = verbnet_reader.verbs
verbnet_classes = verbnet_reader.classes
verbnet_errors = verbnet_reader.unhandled

role_matcher = rolematcher.VnFnRoleMatcher(rolematcher.role_matching_file)

for filename in os.listdir(corpus_path):
    if not filename[-4:] == ".xml": continue

    print(filename)

    if num_files % 100 == 0:
        print("{} {} {}".format(num_files, num_frames, num_args), file=sys.stderr)   
     
    reader = framenetreader.FulltextReader(corpus_path+filename)
    ignored_layers += reader.ignored_layers
    ignored_predicate_args += reader.predicate_is_arg
    phrase_not_found += reader.phrase_not_found
    missing_predicate_data += reader.missing_predicate_data
 
    num_files += 1
       
    for frame in reader.frames:
        num_frames += 1
        num_args += len(frame.args)

        if not frame.predicate.lemma in verbnet:
            not_found.append({
                "file":filename,"sentence":frame.sentence,
                "predicate":frame.predicate.lemma,
            })
            continue
        
        converted_frame = VerbnetFrame.build_from_frame(frame)
        
        try:
            matcher = framematcher.FrameMatcher(frame.predicate.lemma, converted_frame)
        except framematcher.EmptyFrameError:
            empty_framenet_frames.append({
                "file":filename,"sentence":frame.sentence,
                "predicate":frame.predicate.lemma,
                "structure":converted_frame.structure
            })
            continue

        for test_frame in verbnet[frame.predicate.lemma]:
            try:
                matcher.new_match(test_frame) 
            except framematcher.EmptyFrameError:    
                empty_verbnet_frames.append({
                    "encountered_in":filename,
                    "predicate":frame.predicate.lemma,
                    "vbframe":test_frame
                })
                

        distrib = matcher.possible_distribs()
        for role_list in distrib:
            if len(role_list) == 1: num_resolved += 1
  
        num_instanciated = sum([1 if x.instanciated else 0 for x in frame.args])

        for i, slot in enumerate(distrib):
            if len(slot) == 0: continue
            good = False
            can_conclude = True
            for role in slot:
                try:
                    if role_matcher.match(
                        frame.args[i].role, role,
                        frame.frame_name, verbnet_classes[frame.predicate.lemma]
                    ):
                        good = True
                        break
                except rolematcher.RoleMatchingError as e:
                    can_conclude = False
                    unable_to_match.append({
                        "file":filename,"sentence":frame.sentence,
                        "predicate":frame.predicate.lemma,
                        "fn_role":frame.args[i].role,
                        "vn_role":role,
                        "fn_frame":frame.frame_name,
                        "msg":e.msg
                    })
            if good:
                if len(slot) == 1:
                    num_resolved_correct += 1
                else:
                    num_ambiguous_possible += 1
            elif can_conclude:
                if len(slot) == 1:
                    num_resolved_bad += 1
                else:
                    num_ambiguous_impossible += 1               
                
                  
        if debug and num_instanciated > len(distrib):
            debug_data.append({
                "sentence":frame.sentence,
                "predicate":frame.predicate.lemma,
                "args":[x.text for x in frame.args],
                "vbclass":verbnet[frame.predicate.lemma],
                "structure":converted_frame.structure,
                "chosen_frames":matcher.best_frames,
                "result":distrib
            })

        num_discarded += num_instanciated - sum([0 if x == set() else 1 for x in distrib])     
        num_good_args += num_instanciated        
        num_good_frames += 1
        
print("\nDone !\n\n")
print("Found {} args and {} frames in {} files".format(num_args, num_frames, num_files))
print("{} instanciated args and {} frames were kept".format(num_good_args, num_good_frames))
print("{} args were discarded by frame matching".format(num_discarded))

print("{} roles were directly attributed after frame matching".format(num_resolved))
print("{} of thoose where correctly attributed".format(num_resolved_correct))
print("{} of thoose where incorrectly attributed".format(num_resolved_bad))
print("We could not conclude for {} of thoose".format(
    num_resolved - num_resolved_bad - num_resolved_correct))
    
print("The role of {} args are still ambiguous".format(num_good_args - num_resolved - num_discarded))
print("The good role is in the role list in {} cases".format(num_ambiguous_possible))
print("It was not in {} cases".format(num_ambiguous_impossible))
print("We could not conclude for {} of thoose".format(
    num_good_args - num_resolved - num_discarded - num_ambiguous_impossible - num_ambiguous_possible))
    
print("\nProblems :\n")

print("{} unhandled case were encoutered while parsing VerbNet".format(len(verbnet_errors)))
#for frame_data in verbnet_errors: print(frame_data) 
print("Ignored {} frame for which predicate data was missing".format(len(missing_predicate_data)))
#for frame_data in missing_predicate_data: print(frame_data) 
print("Ignored {} non-annotated layers in FrameNet".format(len(ignored_layers)))
#for frame_data in ignored_layers: print(frame_data) 
print("Marked {} arguments which were also predicate as NI".format(len(ignored_predicate_args)))
#for frame_data in ignored_predicate_args: print(frame_data) 
print("Could not retrieve phrase type of {} arguments in FrameNet".format(len(phrase_not_found)))
#for frame_data in phrase_not_found: print(frame_data) 
print("Ignored {} FrameNet frames which predicate was not in VerbNet".format(len(not_found)))
#for frame_data in not_found: print(frame_data)          
print("Ignored {} empty FrameNet frames".format(len(empty_framenet_frames)))
#for frame_data in empty_framenet_frames: print(frame_data)
print("Ignored {} empty VerbNet frames".format(len(empty_verbnet_frames)))
#for frame_data in empty_verbnet_frames: print(frame_data)
print("Was not able to compare {} roles".format(len(unable_to_match)))
#for data in unable_to_match: print(data)

if debug:
    random.shuffle(debug_data)
    for i in range(0,20):
        print(debug_data[i]["sentence"])
        print("Predicate : "+debug_data[i]["predicate"])
        print("Structure : "+" ".join(debug_data[i]["structure"]))
        print("Arguments :")
        for arg in debug_data[i]["args"]:
            print(arg)
        print("VerbNet data : ")
        for vbframe in debug_data[i]["vbclass"]:
            print(vbframe)
        print("Chosen frames : ")
        for vbframe in debug_data[i]["chosen_frames"]:
            print(vbframe)
        print("Result : ")
        print(debug_data[i]["result"])
        print("\n\n")

