#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import optionsparsing

from collections import Counter
import tempfile
import errorslog
from errorslog import log_debug_data, display_debug
from bootstrap import bootstrap_algorithm
from verbnetrestrictions import NoHashDefaultDict
import logging
import paths
import options
from conllreader import ConllSemanticAppender
import verbnetreader
import framematcher
import probabilitymodel
import dumper
import corpuswrapper
import rolematcher
import stats
from options import FrameLexicon

class SemanticRoleLabeler:
    def  __init__(self, argv):
        optionsparsing.Options(argv)
        paths.Paths()
        options.Options() 
        """ Load resources """
        logging.basicConfig(level=options.Options.loglevel)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(options.Options.loglevel)
        self.logger.info("Creating Semantic Role Labeller with argv: {}".format(argv))
        
        self.logger.info("Loading VerbNet...")
        self.frames_for_verb, self.verbnet_classes = verbnetreader.init_verbnet(paths.Paths.verbnet_path(options.Options.language))
        self.role_matcher = rolematcher.VnFnRoleMatcher(paths.Paths.VNFN_MATCHING)
        self.model = probabilitymodel.ProbabilityModel(self.verbnet_classes, 0)
        
    def annotate(self, conllinput = None, language = None):
        """ Run the semantic role labelling 
        
        :var conllinput: string -- text to annotate formated in the CoNLL format. If None, annotate
        the  content of the file  given by the --conll_input option
        
        Return the same string than conllinput but with new colums corresponding 
        to the frames and roles found
        """
        if language is not None:
            options.Options.language = language

        tmpfile = None
        if conllinput is not None:
            tmpfile = tempfile.NamedTemporaryFile(delete=False)
            tmpfile.write(bytes(conllinput, 'UTF-8'))
            tmpfile.seek(0)
            options.Options.conll_input = tmpfile.name
            options.Options.argument_identification = True
        self.logger.info("Annotating {}...".format(conllinput))
        all_annotated_frames = []
        all_vn_frames = []

        self.logger.info("Loading gold annotations and performing frame matching...")
        # annotated_frames: list of FrameInstance
        # vn_frames: list of VerbnetFrameOccurrence
        for annotated_frames, vn_frames in corpuswrapper.get_frames(options.Options.corpus, self.verbnet_classes, options.Options.argument_identification):
            all_matcher = []
            #
            # Frame matching
            #
            data_restr = NoHashDefaultDict(lambda: Counter())
            assert len(annotated_frames) == len(vn_frames)

            # gold_frame: FrameInstance
            # frame_occurrence: VerbnetFrameOccurrence
            for gold_frame, frame_occurrence in zip(annotated_frames, vn_frames):
                if gold_frame.predicate.lemma not in self.frames_for_verb:
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

                matcher = framematcher.FrameMatcher(frame_occurrence, options.Options.matching_algorithm)
                frame_occurrence.matcher = matcher
                all_matcher.append(matcher)

                frames_to_be_matched = []
                for verbnet_frame in sorted(self.frames_for_verb[predicate]):
                    if options.Options.passivize and gold_frame.passive:
                        for passivized_frame in verbnet_frame.passivize():
                            frames_to_be_matched.append(passivized_frame)
                    else:
                        frames_to_be_matched.append(verbnet_frame)

                # Actual frame matching
                matcher.perform_frame_matching(frames_to_be_matched)

                if options.Options.wordnetrestr:
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
                vnclass = self.model.add_data_vnclass(matcher)
                if not options.Options.bootstrap:
                    for roles, slot_type, prep in zip(
                        frame_occurrence.roles, frame_occurrence.slot_types, frame_occurrence.slot_preps
                    ):
                        if len(roles) == 1:
                            self.model.add_data(slot_type, next(iter(roles)), prep, predicate, vnclass)

                if options.Options.debug and set() in frame_occurrence.roles:
                    log_debug_data(gold_frame, frame_occurrence, matcher, frame_occurrence.roles, self.verbnet_classes)

            if options.Options.semrestr:
                for matcher in all_matcher:
                    matcher.handle_semantic_restrictions(data_restr)

            all_vn_frames.extend(vn_frames)
            all_annotated_frames.extend(annotated_frames)

        #
        # Probability models
        #
        self.logger.info("Probability models...")
        if options.Options.bootstrap:
            self.logger.info("Applying bootstrap...")
            bootstrap_algorithm(all_vn_frames, self.model, self.verbnet_classes)
        elif options.Options.probability_model is not None:
            self.logger.info("Applying probability model...")
            for frame_occurrence in all_vn_frames:
                # Commented out a version that only allowed possible role
                # combinations after each restriction
                # for i in range(frame_occurrence.num_slots):
                #     roles_for_slot = frame_occurrence.roles[i]
                for i, roles_for_slot in enumerate(frame_occurrence.roles):
                    if len(roles_for_slot) > 1:
                        new_role = self.model.best_role(
                            roles_for_slot,
                            frame_occurrence.slot_types[i], frame_occurrence.slot_preps[i],
                            frame_occurrence.predicate, options.Options.probability_model)
                        if new_role is not None:
                            frame_occurrence.restrict_slot_to_role(i, new_role)
                frame_occurrence.select_likeliest_matches()
        
            if options.Options.debug:
                display_debug(options.Options.n_debug)
        else:
            self.logger.info("No probability model")

        if options.Options.conll_input is not None:
            self.logger.info("\n## Dumping semantic CoNLL...")
            semantic_appender = ConllSemanticAppender(options.Options.conll_input)
            # vn_frame: VerbnetFrameOccurrence
            for vn_frame in all_vn_frames:
                if vn_frame.best_classes():
                    if options.Options.framelexicon == FrameLexicon.VerbNet:
                        semantic_appender.add_frame_annotation(vn_frame)
                    elif options.Options.framelexicon == FrameLexicon.FrameNet:
                        semantic_appender.add_framenet_frame_annotation(self.role_matcher.possible_framenet_mappings(vn_frame))
                    else:
                        self.logger.error("Error: unknown frame lexicon for output {}".format(options.Options.framelexicon))
            if options.Options.conll_output is None:
                return str(semantic_appender)
            else:
                semantic_appender.dump_semantic_file(options.Options.conll_output)

        else:
            self.logger.info("\n## Evaluation")
            stats.stats_quality(
                all_annotated_frames, all_vn_frames,
                self.frames_for_verb, self.verbnet_classes,
                options.Options.argument_identification)
            stats.display_stats(options.Options.argument_identification)

            if options.Options.dump:
                dumper.dump(options.Options.dump_file, stats.annotated_frames_stats)

        return ""