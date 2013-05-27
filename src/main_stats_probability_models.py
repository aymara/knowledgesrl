#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import getopt
import random
import copy
from errorslog import *

import framenetreader
from framestructure import *
from stats import *
import verbnetreader
import framematcher
import rolematcher
import probabilitymodel
import headwordextractor
from bootstrap import *
import paths

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
    reader = framenetreader.FulltextReader(path, core_args_only)
    
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
   
verbnet, verbnet_classes = init_verbnet(paths.VERBNET_PATH)

print("Loading frames...", file=sys.stderr)

annotated_frames = []
vn_frames = []

for filename in sorted(os.listdir(paths.FRAMENET_FULLTEXT)):
    if not filename[-4:] == ".xml": continue
    print(".", file=sys.stderr, end="")
    sys.stderr.flush()

    if stats_data["files"] % 100 == 0 and stats_data["files"] > 0:
        print("{} {} {}".format(
            stats_data["files"], stats_data["frames"], stats_data["args"]), file=sys.stderr)   
     
    fn_reader = init_fn_reader(paths.FRAMENET_FULLTEXT + filename)

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

print("\nLoading FrameNet and VerbNet roles associations...", file=sys.stderr)
role_matcher = rolematcher.VnFnRoleMatcher(paths.VNFN_MATCHING)
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

good_fm = stats_data["one_correct_role"]
bad_fm = stats_data["one_bad_role"]
resolved_fm = stats_data["one_role"]
identified = (stats_data["args_kept"] - stats_data["no_role"])

copy_of_frames = copy.deepcopy(vn_frames)

print("{:>15} {:>15} {:>20} {:>10} {:>15}".format(
       "Model", "Precision", "Total precision", "Cover", "Total cover"))
       
for probability_model in ["FM", "default", "slot_class", "slot", "predicate_slot"]:
    if probability_model != "FM":
        for frame in vn_frames:
            for i in range(0, len(frame.roles)):
                if len(frame.roles[i]) > 1:
                    new_role = model.best_role(
                        frame.roles[i], frame.slot_types[i], frame.slot_preps[i],
                        frame.predicate, probability_model)
                    if new_role != None:
                        frame.roles[i] = set([new_role])
    stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, debug)

    good = stats_data["one_correct_role"]
    bad = stats_data["one_bad_role"]
    resolved = stats_data["one_role"]
    not_resolved = stats_data["args_kept"] - (stats_data["one_role"] + stats_data["no_role"])
    good_model = stats_data["one_correct_role"] - good_fm
    bad_model = stats_data["one_bad_role"] - bad_fm
    resolved_model = stats_data["one_role"] - resolved_fm

    precision_all = good / (good + bad)
    cover_all = resolved / identified
    if probability_model == "FM":
        precision, cover = precision_all, cover_all
    else:
        precision = good_model / (good_model + bad_model)
        cover = resolved_model / (identified - resolved_fm)
    
    is_fm = probability_model == "FM"
    data = stats_precision_cover(good_fm, bad_fm, resolved_fm, identified, is_fm)
    precision, cover, precision_all, cover_all = data
          
    print("{:>15} {:>15.2%} {:>20.2%} {:>10.2%} {:>15.2%}".format(
        probability_model, precision, precision_all, cover, cover_all))
    
    # Reset frame roles as they were after frame matching
    for x,y in zip(vn_frames, copy_of_frames):
        x.roles = [y.roles[i] for i in range(0, len(x.roles))]
        
hw_extractor = headwordextractor.HeadWordExtractor(paths.FRAMENET_PARSED)
model = probabilitymodel.ProbabilityModel()

print("Extracting arguments headwords...", file=sys.stderr)
hw_extractor.compute_all_headwords(annotated_frames, vn_frames)

print("Computing headwords classes...", file=sys.stderr);
hw_extractor.compute_word_classes()
    
print("Bootstrap algorithm...", file=sys.stderr)
bootstrap_algorithm(vn_frames, model, hw_extractor, verbnet_classes)

stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, debug)
data = stats_precision_cover(good_fm, bad_fm, resolved_fm, identified, False)
precision, cover, precision_all, cover_all = data
    
print("{:>15} {:>15.2%} {:>20.2%} {:>10.2%} {:>15.2%}".format(
        "bootstrap", precision, precision_all, cover, cover_all))

