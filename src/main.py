#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter

from conllreader import ConllSemanticAppender
import stats
import errorslog
from errorslog import log_debug_data, display_debug
from bootstrap import bootstrap_algorithm
from verbnetrestrictions import NoHashDefaultDict
import logging
import paths
import options
import verbnetreader
import framematcher
import probabilitymodel
import dumper
import corpuswrapper

logging.basicConfig(level=options.loglevel)
logger = logging.getLogger(__name__)
logger.setLevel(options.loglevel)

if __name__ == "__main__":
    logger.info("Loading VerbNet...")
    frames_for_verb, verbnet_classes = verbnetreader.init_verbnet(paths.VERBNET_PATH)

    model = probabilitymodel.ProbabilityModel(verbnet_classes, 0)

    all_annotated_frames = []
    all_vn_frames = []

    logger.info("Loading gold annotations and performing frame matching...")
    for annotated_frames, vn_frames in corpuswrapper.get_frames(options.corpus, verbnet_classes, options.argument_identification):
        all_matcher = []
        #
        # Frame matching
        #
        data_restr = NoHashDefaultDict(lambda: Counter())
        assert len(annotated_frames) == len(vn_frames)

        for gold_frame, frame_occurrence in zip(annotated_frames, vn_frames):
            if gold_frame.predicate.lemma not in frames_for_verb:
                errorslog.log_vn_missing(gold_frame)
                continue

            stats.stats_data["frames_with_predicate_in_verbnet"] += 1

            stats.stats_data["args"] += len(gold_frame.args)
            stats.stats_data["args_instanciated"] += len(
                [x for x in gold_frame.args if x.instanciated])

            num_instanciated = len([x for x in gold_frame.args if x.instanciated])
            predicate = gold_frame.predicate.lemma

            if gold_frame.arg_annotated:
                stats.stats_data["args_kept"] += num_instanciated

            stats.stats_data["frames"] += 1

            # Check that FrameNet frame slots have been mapped to VerbNet-style slots
            if frame_occurrence.num_slots == 0:
                errorslog.log_frame_without_slot(gold_frame, frame_occurrence)
                frame_occurrence.matcher = None
                continue

            errorslog.log_frame_with_slot(gold_frame, frame_occurrence)
            stats.stats_data["frames_mapped"] += 1

            matcher = framematcher.FrameMatcher(frame_occurrence, options.matching_algorithm)
            frame_occurrence.matcher = matcher
            all_matcher.append(matcher)

            frames_to_be_matched = []
            for verbnet_frame in sorted(frames_for_verb[predicate]):
                if options.passivize and gold_frame.passive:
                    for passivized_frame in verbnet_frame.passivize():
                        frames_to_be_matched.append(passivized_frame)
                else:
                    frames_to_be_matched.append(verbnet_frame)

            # Actual frame matching
            matcher.perform_frame_matching(frames_to_be_matched)

            if options.wordnetrestr:
                matcher.restrict_headwords_with_wordnet()

            # Update semantic restrictions data (but take no decision)
            for i, restr in matcher.get_matched_restrictions():
                word = frame_occurrence.headwords[i]['top_headword']
                if restr.logical_rel == "AND":
                    for subrestr in restr.children:
                        data_restr[subrestr].update([word])
                else:
                    data_restr[restr].update([word])

            # Update probability model data (but take no decision)
            vnclass = model.add_data_vnclass(matcher)
            if not options.bootstrap:
                for roles, slot_type, prep in zip(
                    frame_occurrence.roles, frame_occurrence.slot_types, frame_occurrence.slot_preps
                ):
                    if len(roles) == 1:
                        model.add_data(slot_type, next(iter(roles)), prep, predicate, vnclass)

            if options.debug and set() in frame_occurrence.roles:
                log_debug_data(gold_frame, frame_occurrence, matcher, frame_occurrence.roles, verbnet_classes)

        if options.semrestr:
            for matcher in all_matcher:
                matcher.handle_semantic_restrictions(data_restr)

        all_vn_frames.extend(vn_frames)
        all_annotated_frames.extend(annotated_frames)

    #
    # Probability models
    #
    logger.info("Probability models...")
    if options.bootstrap:
        logger.info("Applying bootstrap...")
        bootstrap_algorithm(all_vn_frames, model, verbnet_classes)
    elif options.probability_model is not None:
        logger.info("Applying probability model...")
        for frame_occurrence in all_vn_frames:
            # Commented out a version that only allowed possible role
            # combinations after each restriction
            # for i in range(frame_occurrence.num_slots):
            #     roles_for_slot = frame_occurrence.roles[i]
            for i, roles_for_slot in enumerate(frame_occurrence.roles):
                if len(roles_for_slot) > 1:
                    new_role = model.best_role(
                        roles_for_slot,
                        frame_occurrence.slot_types[i], frame_occurrence.slot_preps[i],
                        frame_occurrence.predicate, options.probability_model)
                    if new_role is not None:
                        frame_occurrence.restrict_slot_to_role(i, new_role)
            frame_occurrence.select_likeliest_matches()
    
        if options.debug:
            display_debug(options.n_debug)
    else:
        logger.info("No probability model")

    if options.conll_input is not None:
        logger.info("Dumping semantic CoNLL...")
        semantic_appender = ConllSemanticAppender(options.conll_input)
        for vn_frame in all_vn_frames:
            if vn_frame.best_classes():
                semantic_appender.add_frame_annotation(vn_frame)
        semantic_appender.dump_semantic_file(options.conll_output)

    else:
        logger.info("\n## Evaluation")
        stats.stats_quality(
            all_annotated_frames, all_vn_frames,
            frames_for_verb, verbnet_classes,
            options.argument_identification)
        stats.display_stats(options.argument_identification)

        if options.dump:
            dumper.dump(options.dump_file, stats.annotated_frames_stats)
