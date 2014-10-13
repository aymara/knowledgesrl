#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
import sys
from pathlib import Path

from framenetallreader import FNAllReader
from verbnetframe import VerbnetFrameOccurrence
from conllreader import ConllSemanticAppender
from stats import stats_quality, display_stats, stats_data, stats_ambiguous_roles
import errorslog
from errorslog import log_debug_data, log_vn_missing, display_debug
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


if __name__ == "__main__":
    print("Loading VerbNet...")
    frames_for_verb, verbnet_classes = verbnetreader.init_verbnet(paths.VERBNET_PATH)

    print("Loading FrameNet and VerbNet roles mappings...")
    role_matcher = rolematcher.VnFnRoleMatcher(paths.VNFN_MATCHING)

    model = probabilitymodel.ProbabilityModel(verbnet_classes, 0)
    hw_extractor = headwordextractor.HeadWordExtractor()

    all_annotated_frames = []
    all_vn_frames = []

    if options.conll_input is not None:
        annotation_list = [None]
        parsed_conll_list = [Path(options.conll_input)]
    else:
        annotation_list = options.fulltext_annotations
        parsed_conll_list = options.fulltext_parses

    print("Loading FrameNet annotations and frame matching...")
    for annotation_file, parsed_conll_file in zip(annotation_list, parsed_conll_list):
        print(annotation_file.stem)
        annotated_frames = []
        vn_frames = []

        if options.argument_identification:
            #
            # Argument identification
            #
            arg_guesser = argguesser.ArgGuesser(verbnet_classes)

            new_frame_instances = list(arg_guesser.frame_instances_from_file(parsed_conll_file))
            new_annotated_frames = roleextractor.fill_gold_roles(new_frame_instances,
                annotation_file, parsed_conll_file, verbnet_classes,
                role_matcher)

            for gold_frame, frame_instance in zip(new_annotated_frames, new_frame_instances):
                annotated_frames.append(gold_frame)
                vn_frames.append(VerbnetFrameOccurrence.build_from_frame(gold_frame, conll_frame_instance=frame_instance))
        else:
            #
            # Load gold arguments
            #
            fn_reader = FNAllReader(
                add_non_core_args=options.add_non_core_args)

            for frame in fn_reader.iter_frames(annotation_file, parsed_conll_file):
                stats_data["args"] += len(frame.args)
                stats_data["args_instanciated"] += len(
                    [x for x in frame.args if x.instanciated])
                stats_data["frames"] += 1

                if not frame.predicate.lemma in frames_for_verb:
                    log_vn_missing(frame)
                    continue

                stats_data["frames_with_predicate_in_verbnet"] += 1

                annotated_frames.append(frame)
                vn_frames.append(VerbnetFrameOccurrence.build_from_frame(frame, conll_frame_instance=None))

            stats_data["files"] += fn_reader.stats["files"]

        #
        # Frame matching
        #
        all_matcher = []
        data_restr = NoHashDefaultDict(lambda : Counter())
        assert len(annotated_frames) == len(vn_frames)
        for good_frame, frame_occurrence in zip(annotated_frames, vn_frames):
            num_instanciated = len([x for x in good_frame.args if x.instanciated])
            predicate = good_frame.predicate.lemma

            if good_frame.arg_annotated:
                stats_data["args_kept"] += num_instanciated

            stats_ambiguous_roles(good_frame, num_instanciated,
                role_matcher, verbnet_classes)

            # Check that FrameNet frame slots have been mapped to VerbNet-style slots
            if frame_occurrence.num_slots == 0:
                errorslog.log_frame_without_slot(good_frame, frame_occurrence)
                continue

            matcher = framematcher.FrameMatcher(frame_occurrence, options.matching_algorithm)
            all_matcher.append(matcher)

            errorslog.log_frame_with_slot(good_frame, frame_occurrence)
            stats_data["frames_mapped"] += 1

            # Actual frame matching
            for verbnet_frame in sorted(frames_for_verb[predicate]):
                if options.passivize and good_frame.passive:
                    try:
                        for passivized_frame in verbnet_frame.passivize():
                            matcher.new_match(passivized_frame)
                    except:
                        continue
                else:
                    matcher.new_match(verbnet_frame)

            frame_occurrence.roles = matcher.possible_distribs()
            frame_occurrence.best_classes = matcher.best_classes

            # Update semantic restrictions data
            #for word, restr in matcher.get_matched_restrictions().items():
            #    if restr.logical_rel == "AND":
            #        for subrestr in restr.children:
            #            data_restr[subrestr].update([word])
            #    else:
            #        data_restr[restr].update([word])

            # Update probability model
            vnclass = model.add_data_vnclass(matcher)
            if not options.bootstrap:
                for roles, slot_type, prep in zip(
                    frame_occurrence.roles, frame_occurrence.slot_types, frame_occurrence.slot_preps
                ):
                    if len(roles) == 1:
                        model.add_data(slot_type, next(iter(roles)), prep, predicate, vnclass)

            if options.debug and set() in frame_occurrence.roles:
                log_debug_data(good_frame, frame_occurrence, matcher, frame_occurrence.roles, verbnet_classes)

        if options.dump:
            dumper.add_data_frame_matching(annotated_frames, vn_frames,
                role_matcher, verbnet_classes,
                frames_for_verb, options.matching_algorithm)

        if options.semrestr:
            for matcher in all_matcher:
                matcher.handle_semantic_restrictions(data_restr)
                matcher.frame_occurrence.roles = matcher.possible_distribs()

        all_vn_frames.extend(vn_frames)
        all_annotated_frames.extend(annotated_frames)

    #
    # Probability models
    #
    if options.bootstrap:
        print("Applying bootstrap...")
        for annotation_file, parsed_conll_file in zip(annotation_list, parsed_conll_list):
            bootstrap_algorithm(all_vn_frames, model, hw_extractor, verbnet_classes)
    elif options.probability_model is not None:
        print("Applying probability model...")
        for annotation_file, parsed_conll_file in zip(annotation_list, parsed_conll_list):
            print(annotation_file.stem)
            for frame in all_vn_frames:
                for i, roles in enumerate(frame.roles):
                    if len(frame.roles[i]) > 1:
                        new_role = model.best_role(
                            frame.roles[i], frame.slot_types[i], frame.slot_preps[i],
                            frame.predicate, options.probability_model)
                        if new_role != None:
                            frame.roles[i] = set([new_role])

            if options.dump:
                dumper.add_data_prob_model(all_annotated_frames, all_vn_frames, role_matcher, verbnet_classes)

            if options.debug:
                display_debug(options.n_debug)

    if options.dump:
        dumper.dump(options.dump_file)

    if options.conll_input is not None:
        print("Dumping semantic CoNLL...")
        semantic_appender = ConllSemanticAppender(options.conll_input)
        for vn_frame in all_vn_frames:
            if vn_frame.best_classes is not None:
                semantic_appender.add_frame_annotation(vn_frame)
        semantic_appender.dump_semantic_file(options.conll_output)

    else:
        print("\n\n## Final stats")
        stats_quality(all_annotated_frames, all_vn_frames, role_matcher, verbnet_classes, options.argument_identification)
        display_stats(options.argument_identification)
