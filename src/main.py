#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import getopt
import random
from errorslog import *

import framenetreader
from framestructure import *
from stats import *
from errorslog import *
from bootstrap import bootstrap_algorithm
import verbnetreader
import framematcher
import rolematcher
import probabilitymodel
import headwordextractor
import paths

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

if __name__ == "__main__":
    # Default values for command-line options
    framematcher.matching_algorithm = 1
    core_args_only = True
    debug = False
    bootstrap = False
    probability_model = "predicate_slot"

    options = getopt.getopt(sys.argv[1:], "d:",
        ["fmatching-algo=", "add-non-core-args", "model=", "bootstrap"])
    for opt,value in options[0]:
        if opt == "-d":
            debug = True
            value = 0 if value == "" else int(value)
            if value > 0:
                n_debug = value
        if opt == "--fmatching-algo" and value == 0:
            framematcher.matching_algorithm = 0
        if opt == "--add-non-core-args":
            core_args_only = False
        if opt == "--model":
            if not value in probabilitymodel.models:
                raise Exception("Unknown model {}".format(value))
            probability_model = value
        if opt == "--bootstrap":
            bootstrap = True
       
    verbnet_predicates, verbnet_classes = init_verbnet(paths.VERBNET_PATH)

    print("Loading frames...", file=sys.stderr)

    annotated_frames = []
    vn_frames = []

    for filename in sorted(os.listdir(paths.FRAMENET_FULLTEXT)):
        if not filename[-4:] == ".xml": continue
        print(".", file=sys.stderr, end="")
        sys.stderr.flush()

        if stats_data["files"] % 100 == 0 and stats_data["files"] > 0:
            print("{} {} {}".format(
                stats_data["files"], stats_data["frames"],
                stats_data["args"]), file=sys.stderr)   
         
        fn_reader = init_fn_reader(paths.FRAMENET_FULLTEXT + filename)

        for frame in fn_reader.frames:
            stats_data["args"] += len(frame.args)
            stats_data["frames"] += 1

            if not frame.predicate.lemma in verbnet_predicates:
                log_vn_missing(filename, frame)
                continue

            stats_data["frames_with_predicate_in_verbnet"] += 1
            
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
        num_instanciated = len([x for x in good_frame.args if x.instanciated])
        predicate = good_frame.predicate.lemma
        stats_data["args_kept"] += num_instanciated
        
        stats_ambiguous_roles(good_frame, num_instanciated,
            role_matcher, verbnet_classes, filename)
     
        # Find FrameNet frame <-> VerbNet class mapping
        try:
            matcher = framematcher.FrameMatcher(predicate, frame)
        except framematcher.EmptyFrameError:
            log_frame_without_slot(filename, good_frame, frame)
            continue

        stats_data["frames_mapped"] += 1

        # Actual frame matching
        for test_frame in verbnet_predicates[predicate]:
            matcher.new_match(test_frame)       
        frame.roles = matcher.possible_distribs()
        
        # Update probability model
        if not bootstrap:
            for roles, slot_type, prep in zip(
                frame.roles, frame.slot_types, frame.slot_preps
            ):
                if len(roles) == 1:
                    model.add_data(slot_type, next(iter(roles)), prep, predicate)

        
    print("Frame matching stats...", file=sys.stderr) 
    stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, debug)
    display_stats()

    if bootstrap:
        hw_extractor = headwordextractor.HeadWordExtractor(paths.FRAMENET_PARSED)

        print("Extracting arguments headwords...", file=sys.stderr)
        hw_extractor.compute_all_headwords(annotated_frames, vn_frames)

        print("Computing headwords classes...", file=sys.stderr);
        hw_extractor.compute_word_classes()
        
        print("Bootstrap algorithm...", file=sys.stderr)
        bootstrap_algorithm(vn_frames, model, hw_extractor, verbnet_classes)
    else:
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

