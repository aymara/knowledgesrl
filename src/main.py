#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import random
from errorslog import *
import framenetallreader
from verbnetframe import *
from stats import *
from errorslog import *
from bootstrap import bootstrap_algorithm
from verbnetrestrictions import NoHashDefaultDict
import options
import argguesser
import roleextractor
import verbnetreader
import framematcher
import rolematcher
import probabilitymodel
import headwordextractor
import paths
import dumper

def init_verbnet(path):
    print("Loading VerbNet data...", file=sys.stderr)
    reader = verbnetreader.VerbnetReader(path)
    errors["vn_parsing"] = reader.unhandled
    return reader.verbs, reader.classes

if __name__ == "__main__":
    verbnet_predicates, verbnet_classes = init_verbnet(paths.VERBNET_PATH)

    print("Loading FrameNet and VerbNet roles associations...", file=sys.stderr)
    role_matcher = rolematcher.VnFnRoleMatcher(paths.VNFN_MATCHING)
    model = probabilitymodel.ProbabilityModel(verbnet_classes, 0)
 
    annotated_frames = []
    vn_frames = []
   
    if options.gold_args:
        print("Loading frames...", file=sys.stderr)
        fn_reader = framenetallreader.FNAllReader(
            options.fulltext_corpus, options.framenet_parsed,
            core_args_only=options.core_args_only)

        for frame in fn_reader.iter_frames():
            stats_data["args"] += len(frame.args)
            stats_data["args_instanciated"] += len(
                [x for x in frame.args if x.instanciated])
            stats_data["frames"] += 1
            
            if not frame.predicate.lemma in verbnet_predicates:
                log_vn_missing(frame)
                continue

            stats_data["frames_with_predicate_in_verbnet"] += 1
                
            annotated_frames.append(frame)
                
            converted_frame = VerbnetFrame.build_from_frame(frame)

            vn_frames.append(converted_frame)
        stats_data["files"] += fn_reader.stats["files"]
    else:
        arg_guesser = argguesser.ArgGuesser(options.framenet_parsed, verbnet_classes)
        
        print("Extracting frames and matching them with real frames...")
        annotated_frames = []
        
        while arg_guesser.file_remains():
            filename = arg_guesser.current_file()
            extracted_frames = [x for x in arg_guesser.handle_next_file()]
            annotated_frames += roleextractor.fill_roles(
                extracted_frames, verbnet_classes, role_matcher, filename)
        
        print("\nBuilding VerbNet-like structures...")
        for frame in annotated_frames:
            converted_frame = VerbnetFrame.build_from_frame(frame)
            vn_frames.append(converted_frame)

    hw_extractor = headwordextractor.HeadWordExtractor(options.framenet_parsed)

    print("Extracting arguments headwords...", file=sys.stderr)
    hw_extractor.compute_all_headwords(annotated_frames, vn_frames)
    
    print("Frame matching...", file=sys.stderr)
    all_matcher = []
    data_restr = NoHashDefaultDict(lambda : Counter())
    for good_frame, frame in zip(annotated_frames, vn_frames):
        num_instanciated = len([x for x in good_frame.args if x.instanciated])
        predicate = good_frame.predicate.lemma
        
        if good_frame.arg_annotated:
            stats_data["args_kept"] += num_instanciated
        
        stats_ambiguous_roles(good_frame, num_instanciated,
            role_matcher, verbnet_classes)
     
        # Find FrameNet frame <-> VerbNet class mapping
        try:
            matcher = framematcher.FrameMatcher(frame, options.matching_algorithm)
            all_matcher.append(matcher)
        except framematcher.EmptyFrameError:
            log_frame_without_slot(good_frame, frame)
            continue

        stats_data["frames_mapped"] += 1

        # Actual frame matching
        for test_frame in verbnet_predicates[predicate]:
            if options.passive and good_frame.passive:
                try:
                    for passivized_frame in test_frame.passivize():
                        matcher.new_match(passivized_frame)
                except:
                    pass
            else:
                matcher.new_match(test_frame)
                
        frame.roles = matcher.possible_distribs()
        
        # Update semantic restrictions data
        for word, restr in matcher.get_matched_restrictions().items():
            if restr.logical_rel == "AND":
                for subrestr in restr.children:
                    data_restr[subrestr].update([word])
            else:
                data_restr[restr].update([word])
            
        # Update probability model
        vnclass = model.add_data_vnclass(matcher)
        if not options.bootstrap:
            for roles, slot_type, prep in zip(
                frame.roles, frame.slot_types, frame.slot_preps
            ):
                if len(roles) == 1:
                    model.add_data(slot_type, next(iter(roles)), prep, predicate, vnclass)
                    
        if options.debug and set() in frame.roles:
            log_debug_data(good_frame, frame, matcher, frame.roles, verbnet_classes)
    
    if options.dump:
        dumper.add_data_frame_matching(annotated_frames, vn_frames,
            role_matcher, verbnet_classes,
            verbnet_predicates, options.matching_algorithm)
    else:       
        print("Frame matching stats...", file=sys.stderr)
        stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, options.gold_args)
        display_stats(options.gold_args)
    
    if options.semrestr:
        for matcher in all_matcher:
            matcher.handle_semantic_restrictions(data_restr)
            matcher.frame.roles = matcher.possible_distribs()

        stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, options.gold_args)
        display_stats(options.gold_args)
        
    if options.bootstrap:
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
                        frame.predicate, options.probability_model)
                    if new_role != None:
                        frame.roles[i] = set([new_role])

    if options.dump:
        dumper.add_data_prob_model(annotated_frames, vn_frames, role_matcher, verbnet_classes)
        dumper.dump(options.dump_file)
    else:
        print("Final stats...", file=sys.stderr)

        stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, options.gold_args)
        display_stats(options.gold_args)

    if options.debug: display_debug(options.n_debug)

