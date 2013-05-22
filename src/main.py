#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import framenetreader
from framestructure import *
from stats import *
import verbnetreader
import framematcher
import rolematcher
import probabilitymodel
import os
import sys
import getopt
import random
from errorslog import *

corpus_path = "../data/fndata-1.5/fulltext/"
verbnet_path = "../data/verbnet-3.2/"

# Default values for command-line options
framematcher.matching_algorithm = 1
core_args_only = False
debug = False
probability_model = "predicate_slot"

def init_verbnet(path):
    print("Loading VerbNet data...", file=sys.stderr)
    reader = verbnetreader.VerbnetReader(path)
    errors["vn_parsing"] = reader.unhandled
    return reader.verbs, reader.classes

def init_fn_reader(path):
    reader = framenetreader.FulltextReader(corpus_path+filename, core_args_only)
    
    errors["unannotated_layer"] += reader.ignored_layers
    errors["predicate_was_arg"] += reader.predicate_is_arg
    errors["missing_phrase_type"] += reader.phrase_not_found
    errors["missing_predicate_data"] += reader.missing_predicate_data
    
    return reader

options = getopt.getopt(sys.argv[1:], "d:", ["fmatching-algo=", "core-args-only"])
for opt,value in options[0]:
    if opt == "-d":
        debug = True
        value = 0 if value == "" else int(value)
        if value > 0:
            n_debug = value
    if opt == "--fmatching-algo" and value == 0:
        framematcher.matching_algorithm = 0
    if opt == "--core-args-only":
        core_args_only = True
   
verbnet, verbnet_classes = init_verbnet(verbnet_path)

print("Loading frames...", file=sys.stderr)

annotated_frames = []
vn_frames = []

for filename in sorted(os.listdir(corpus_path)):
    if not filename[-4:] == ".xml": continue
    print(filename, file=sys.stderr)

    if stats_data["files"] % 100 == 0 and stats_data["files"] > 0:
        print("{} {} {}".format(
            stats_data["files"], stats_data["frames"], stats_data["args"]), file=sys.stderr)   
     
    fn_reader = init_fn_reader(corpus_path + filename)

    for frame in fn_reader.frames:
        stats_data["args"] += len(frame.args)
        stats_data["frames"] += 1

        if not frame.predicate.lemma in verbnet:
            log_vn_missing(filename, frame)
            continue
        
        annotated_frames.append(frame)
        
        converted_frame = VerbnetFrame.build_from_frame(frame)
        converted_frame.compute_slot_types()
        vn_frames.append(converted_frame)
    stats_data["files"] += 1

print("Loading FrameNet and VerbNet roles associations...", file=sys.stderr)
role_matcher = rolematcher.VnFnRoleMatcher(rolematcher.role_matching_file)
model = probabilitymodel.ProbabilityModel()

print("Frame matching...", file=sys.stderr)
for good_frame, frame in zip(annotated_frames, vn_frames):
    num_instanciated = sum([1 if x.instanciated else 0 for x in good_frame.args])
    predicate = good_frame.predicate.lemma
    
    stats_ambiguous_roles(good_frame, num_instanciated,
        role_matcher, verbnet_classes, filename)
 
    try:
        matcher = framematcher.FrameMatcher(predicate, frame)
    except framematcher.EmptyFrameError:
        log_frame_without_slot(filename, good_frame, frame)
        continue

    # Actual frame matching
    for test_frame in verbnet[predicate]:
        matcher.new_match(test_frame)       
    frame.roles = matcher.possible_distribs()
    
    # Update probability model
    for roles, slot_type, prep in zip(frame.roles, frame.slot_types, frame.slot_preps):
        if len(roles) == 1:
            model.add_data(slot_type, next(iter(roles)), prep, predicate)

    stats_data["args_kept"] += num_instanciated
    stats_data["frames_kept"] += 1
    
print("Frame matching stats...", file=sys.stderr) 

stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, debug)
display_stats()

print("Applying probabilistic model...", file=sys.stderr)
for frame in vn_frames:
    for i in range(0, len(frame.roles)):
        if len(frame.roles[i]) > 1:
            new_role = model.best_role(
                frame.roles[i], frame.slot_types[i], frame.slot_preps[i],
                frame.predicate, probability_model)
            if new_role != None:
                frame.roles[i] = set([new_role])

print("Final stats...", file=sys.stderr)   

stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, debug)
display_stats()

if debug: display_debug(n_debug)

