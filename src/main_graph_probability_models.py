#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import random
import itertools
import copy

import framenetallreader
from verbnetframe import VerbnetFrame
from stats import stats_data, stats_quality
from errorslog import errors
import options
import verbnetreader
import framematcher
import rolematcher
import probabilitymodel
import paths


if __name__ == "__main__":
    corpus_path = "../data/fndata-1.5/fulltext/"
    test_corpus_path = "../data/fndata-1.5/fulltext/"

    #models = ["slot_class", "slot", "predicate_slot"]
    models = ["predicate_slot"]
    step = 10
    num_same = 5

    def init_verbnet(path):
        print("Loading VerbNet data...", file=sys.stderr)
        reader = verbnetreader.VerbnetReader(path)
        errors["vn_parsing"] = reader.unhandled
        return reader.verbs, reader.classes

       
    verbnet, verbnet_classes = init_verbnet(paths.VERBNET_PATH)

    # Read data that will be used to feed the probability model

    print("Loading data frames...", file=sys.stderr)

    annotated_frames = []
    vn_frames = []

    fn_reader = framenetallreader.FNAllReader(
            corpus_path, options.framenet_parsed,
            core_args_only=options.core_args_only)

    for frame in fn_reader.iter_frames():
        if not frame.predicate.lemma in verbnet: continue
            
        annotated_frames.append(frame)
            
        converted_frame = VerbnetFrame.build_from_frame(frame)
        vn_frames.append(converted_frame)

    print("Loading FrameNet and VerbNet roles associations...", file=sys.stderr)
    role_matcher = rolematcher.VnFnRoleMatcher(paths.VNFN_MATCHING)

    # First frame matching

    print("Frame matching...", file=sys.stderr)
    for good_frame, frame in zip(annotated_frames, vn_frames):
        num_instanciated = len([x for x in good_frame.args if x.instanciated])
        predicate = good_frame.predicate.lemma

        try:
            matcher = framematcher.FrameMatcher(frame, options.matching_algorithm)
        except framematcher.EmptyFrameError:
            continue

        for test_frame in verbnet[predicate]:
            matcher.new_match(test_frame)
        frame.roles = matcher.possible_distribs()
        
    print("Loading evaluation frames...", file=sys.stderr)

    # Read the evaluation data

    annotated_test_frames = []
    vn_test_frames = []

    fn_reader = framenetallreader.FNAllReader(
            test_corpus_path, options.framenet_parsed,
            core_args_only=options.core_args_only)

    for frame in fn_reader.frames:
        stats_data["args"] += len(frame.args)
        stats_data["frames"] += 1

        if not frame.predicate.lemma in verbnet:
            #log_vn_missing(filename, frame)
            continue
        
        stats_data["frames_with_predicate_in_verbnet"] += 1
            
        annotated_test_frames.append(frame)
            
        converted_frame = VerbnetFrame.build_from_frame(frame)
        vn_test_frames.append(converted_frame)
    stats_data["files"] += fn_reader.stats["files"]

    # Frame matching on the evaluation data

    print("Frame matching...", file=sys.stderr)
    for good_frame, frame in zip(annotated_test_frames, vn_test_frames):
        num_instanciated = len([x for x in good_frame.args if x.instanciated])
        predicate = good_frame.predicate.lemma
        stats_data["args_kept"] += num_instanciated

        # Find FrameNet frame <-> VerbNet class mapping
        try:
            matcher = framematcher.FrameMatcher(frame, options.matching_algorithm)
        except framematcher.EmptyFrameError:
            continue
        stats_data["frames_mapped"] += 1

        # Actual frame matching
        for test_frame in verbnet[predicate]:
            matcher.new_match(test_frame)
        frame.roles = matcher.possible_distribs()

    stats_quality(annotated_test_frames, vn_test_frames, role_matcher,
        verbnet_classes, options.gold_args)

    # We need to remember some parameters to evaluate
    # the probability model performances
    good_fm = stats_data["one_correct_role"]
    bad_fm = stats_data["one_bad_role"]
    resolved_fm = stats_data["one_role"]
    identified = (stats_data["args_kept"] - stats_data["no_role"])

    print("Base precision : {}".format(good_fm / (good_fm + bad_fm)), file=sys.stderr)

    copy_of_frames = copy.deepcopy(vn_test_frames)
    order = [x for x in range(0, len(vn_test_frames))]

    percents = [step * i for i in range(1, 1 + int(100 / step))]
    for probability_model in models:
        for n, j in itertools.product(percents, range(0, num_same)):
            print("{} {}% {}".format(probability_model, n, j), file=sys.stderr)
            
            # Reset results if we have reached a new %
            if j == 0: sum_precision, sum_cover, num_data_precision = 0, 0, 0

            random.shuffle(order)

            # Reset the roles of vn_test_frames as they were after frame matching
            for x,y in zip(vn_test_frames, copy_of_frames):
                x.roles = [y.roles[i] for i in range(0, len(x.roles))]

            # Instanciate the probability model and fill it with
            # an appropriate amount of data
            model = probabilitymodel.ProbabilityModel()
            max_frame = int(n * len(annotated_frames) / 100)
            frames_number = 0
            for i in order:
                if frames_number >= max_frame: break
                frames_number += 1
                
                good_frame, frame = annotated_test_frames[i], vn_test_frames[i]
                           
                predicate = good_frame.predicate.lemma
                for roles, slot_type, prep in zip(frame.roles, frame.slot_types, frame.slot_preps):
                    if len(roles) == 1:
                        model.add_data(slot_type, next(iter(roles)), prep, predicate)
            
            print(probabilitymodel.multi_count(model.data_predicate_slot))
            
            # Apply the probability model
            for frame in vn_test_frames:
                for i in range(0, len(frame.roles)):
                    if len(frame.roles[i]) > 1:
                        new_role = model.best_role(
                            frame.roles[i], frame.slot_types[i], frame.slot_preps[i],
                            frame.predicate, probability_model)
                        if new_role != None:
                            frame.roles[i] = set([new_role])

            stats_quality(annotated_test_frames, vn_test_frames,
                role_matcher, verbnet_classes, options.gold_args)

            # Update the results according to the quality statistics
            good = stats_data["one_correct_role"]
            bad = stats_data["one_bad_role"]
            good_model = stats_data["one_correct_role"] - good_fm
            bad_model = stats_data["one_bad_role"] - bad_fm
            resolved_model = stats_data["one_role"] - resolved_fm

            sum_cover += resolved_model / (identified - resolved_fm)
            if good_model + bad_model > 0:
                num_data_precision += 1
                sum_precision += good_model / (good_model + bad_model)

            print("{} {} {}".format(good_model, bad_model, resolved_model))

            # Display the results if we are done with this %
            if j + 1 == num_same:
                if num_data_precision == 0:
                    mean_precision = 0
                else:
                    mean_precision = sum_precision / num_data_precision
                mean_cover = sum_cover / num_same
                print("{} {} {}".format(n, mean_precision, mean_cover))

