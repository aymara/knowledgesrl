#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argguesser
import dumper
import errorslog
import framematcher
import framenet
import logging
import options
import paths
import probabilitymodel
import roleextractor
import rolematcher
import stats
import sys
import tempfile
import verbnetreader

from bootstrap import bootstrap_algorithm
from collections import Counter
from conllreader import ConllSemanticAppender
from errorslog import *
from framenetallreader import FNAllReader
from options import FrameLexicon
from paths import Path
from verbnetframe import VerbnetFrameOccurrence
from verbnetrestrictions import NoHashDefaultDict


class SemanticRoleLabeler:
    def __init__(self, language: str):
        """ Initialize the semantic role labeller

        :var language: string -- the language of input text

        Return the same string than conllinput but with new colums
        corresponding to the frames and roles found
        """
        logging.basicConfig(level=options.Options.loglevel)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(options.Options.loglevel)
        # Ensure paths are initialized
        paths.Paths()
        self.logger.debug("SemanticRoleLabeler::init")
        self.logger.info('Options: {}'.format(options.Options.framelexicon))

        if language:
            options.Options.language = language

        """ Load resources """
        self.frameNet = framenet.FrameNet()
        self.role_matcher = None
        if options.Options.framelexicon == FrameLexicon.FrameNet:
            self.logger.info("Loading FrameNet...")
            framenet.FrameNetReader(
                paths.Paths.framenet_path(language),
                self.frameNet)
            # self.logger.info(f"SemanticRoleLabeler framenet frames: "
            #                  f"{self.frameNet.frames}")
        # elif options.Options.framelexicon == FrameLexicon.VerbNet:
        self.logger.info("Loading VN-FN role matcher...")
        self.role_matcher = rolematcher.VnFnRoleMatcher(paths.Paths.
                                                        VNFN_MATCHING,
                                                        self.frameNet)
        # Load VerbNet
        self.logger.info("Loading VerbNet...")
        (self.frames_for_verb,
         self.verbnet_classes) = verbnetreader.init_verbnet(
            paths.Paths.verbnet_path(language))
        self.logger.debug("SemanticRoleLabeler::init DONE")

    def get_frames(self, corpus, verbnet_classes, frameNet,
                   conll_input: str, argid=False):
        """
        Fills two list of the same size with content dependent of the kind of
        input

        The two lists are annotation_list and parsed_conll_list
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(options.Options.loglevel)
        logger.debug(f"SemanticRoleLabeler.get_frames corpus={corpus} "
                     f"input={conll_input}")

        # Selection of the text to annotate
        if conll_input:
            # We will annotate the given CoNLL input text
            annotation_list = [None]
            parsed_conll_list = [Path(conll_input)]
        elif corpus == 'FrameNet':
            # We will annotate the FrameNet corpus
            annotation_list = options.Options.fulltext_annotations
            parsed_conll_list = options.Options.fulltext_parses
            assert(len(annotation_list) == len(parsed_conll_list))
        elif corpus == 'dicoinfo_fr':
            # We should annotate the dicoinfo_fr corpus
            pass
        else:
            raise Exception('Unknown corpus {}'.format(corpus))

        # if corpus == 'FrameNet':
        logger.info(f"Loading FrameNet and VerbNet role mappings "
                    f"{paths.Paths.VNFN_MATCHING} ...")
        role_matcher = rolematcher.VnFnRoleMatcher(paths.Paths.VNFN_MATCHING,
                                                   frameNet)

        for annotation_file, parsed_conll_file in zip(annotation_list,
                                                      parsed_conll_list):
            logger.debug(f"Handling {annotation_file} {parsed_conll_file}")
            file_stem = (annotation_file.stem
                         if annotation_file else parsed_conll_file.stem)
            annotated_frames = []
            vn_frames = []

            if argid:
                logger.debug("Argument identification")
                #
                # Argument identification
                #
                arg_guesser = argguesser.ArgGuesser(verbnet_classes)

                # Many instances are not actually FrameNet frames
                new_frame_instances = list(
                    arg_guesser.frame_instances_from_file(
                        parsed_conll_file
                        )
                    )
                new_annotated_frames = roleextractor.fill_gold_roles(
                    frame_instances=new_frame_instances, annotation_file=[annotation_file], parsed_conll_file=[parsed_conll_file],
                    verbnet_classes=verbnet_classes, role_matcher=role_matcher)
                logger.debug(f'got nb new_annotated_frames: '
                             f'{len(new_annotated_frames)}')

                for gold_frame, frame_instance in zip(new_annotated_frames,
                                                      new_frame_instances):
                    annotated_frames.append(gold_frame)
                    vn_frames.append(VerbnetFrameOccurrence.build_from_frame(
                        gold_frame, conll_frame_instance=frame_instance))
            else:
                logger.info("Load gold arguments")
                #
                # Load gold arguments
                #
                fn_reader = FNAllReader(
                    add_non_core_args=options.Options.add_non_core_args)

                for framenet_instance in fn_reader.iter_frames(
                        annotation_file, parsed_conll_file):
                    annotated_frames.append(framenet_instance)
                    vn_frames.append(VerbnetFrameOccurrence.build_from_frame(
                        framenet_instance, conll_frame_instance=None))

                stats.stats_data["files"] += fn_reader.stats["files"]

            yield annotated_frames, vn_frames
        # else:
        #     logger.info(f"get_frames: nothing to do for corpus "
        #                 f"{corpus}")

    def annotate(self, conllinput: str) -> None:
        """ Run the semantic role labelling

        :var conllinput: string -- text to annotate formated in the CoNLL
                                   format. If empty, annotate the corpus

        Return the same string than conllinput but with new colums
        corresponding to the frames and roles found
        """
        self.logger.info(f"SemanticRoleLabeler.annotate: {conllinput}")
        model = probabilitymodel.ProbabilityModel(self.verbnet_classes, 0)

        # tmpfile = None
        # if conllinput is not None:
            # options.Options.argument_identification = True
            # if options.Options.loglevel == logging.DEBUG:
            #     tmpfile = tempfile.NamedTemporaryFile(delete=False)
            #     self.logger.error(f'Debug mode: will not delete temporary '
            #                       f'file {tmpfile.name}')
            # else:
            #     tmpfile = tempfile.NamedTemporaryFile(delete=True)
            # tmpfile.write(bytes(conllinput, 'UTF-8'))
            # tmpfile.seek(0)
            # options.Options.conll_input = tmpfile.name
        # self.logger.debug("Annotating {}...".format(conllinput[0:50]))
        all_annotated_frames = []
        all_vn_frames = []

        self.logger.info("annotate: loading gold annotations "
                         "and performing frame matching...")
        # annotated_frames: list of FrameInstance
        # vn_frames: list of VerbnetFrameOccurrence
        for annotated_frames, vn_frames in self.get_frames(
                options.Options.corpus,
                self.verbnet_classes,
                self.frameNet,
                conllinput,
                options.Options.argument_identification):
            self.logger.debug('annotate: handling a pair annotated_frames, '
                              'vn_frames of size {}'.format(len(vn_frames)))
            all_matcher = []
            #
            # Frame matching
            #
            data_restr = NoHashDefaultDict(lambda: Counter())
            assert len(annotated_frames) == len(vn_frames)

            # gold_frame: FrameInstance
            # frame_occurrence: VerbnetFrameOccurrence
            for gold_frame, frame_occurrence in zip(annotated_frames,
                                                    vn_frames):
                self.logger.debug("GOLD_FRAME:{gold_frame}")
                if gold_frame.predicate.lemma not in self.frames_for_verb:
                    errorslog.log_vn_missing(gold_frame)
                    self.logger.debug('gold_frame predicate lemma "{}" not in '
                                      '{}'.format(gold_frame.predicate.lemma,
                                                  self.frames_for_verb))
                    continue

                stats.stats_data["frames_with_predicate_in_verbnet"] += 1

                stats.stats_data["args"] += len(gold_frame.args)
                stats.stats_data["args_instanciated"] += len(
                    [x for x in gold_frame.args if x.instanciated])

                num_instanciated = len(
                    [x for x in gold_frame.args if x.instanciated])
                predicate = gold_frame.predicate.lemma

                if gold_frame.arg_annotated:
                    stats.stats_data["args_kept"] += num_instanciated

                stats.stats_data["frames"] += 1

                # Check that FrameNet frame slots have been mapped to
                # VerbNet-style slots
                if frame_occurrence.num_slots == 0:
                    errorslog.log_frame_without_slot(gold_frame,
                                                     frame_occurrence)
                    self.logger.debug(f'frame occurrence has no slot set '
                                      f'{gold_frame} {frame_occurrence}')
                    frame_occurrence.matcher = None
                    continue

                errorslog.log_frame_with_slot(gold_frame, frame_occurrence)
                stats.stats_data["frames_mapped"] += 1

                matcher = framematcher.FrameMatcher(frame_occurrence,
                                                    options.Options.
                                                    matching_algorithm)
                frame_occurrence.matcher = matcher
                all_matcher.append(matcher)

                frames_to_be_matched = []
                for verbnet_frame in sorted(self.frames_for_verb[predicate]):
                    if options.Options.passivize and gold_frame.passive:
                        for passivized_frame in verbnet_frame.passivize():
                            frames_to_be_matched.append(passivized_frame)
                    else:
                        frames_to_be_matched.append(verbnet_frame)

                self.logger.debug(f'there is {len(frames_to_be_matched)} '
                                  f'frames to be matched')
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
                vnclass = model.add_data_vnclass(matcher)
                if not options.Options.bootstrap:
                    for roles, slot_type, prep in zip(
                        frame_occurrence.roles, frame_occurrence.slot_types,
                        frame_occurrence.slot_preps
                    ):
                        if len(roles) == 1:
                            model.add_data(slot_type, next(iter(roles)), prep,
                                           predicate, vnclass)

                if (options.Options.loglevel == logging.DEBUG
                        and set() in frame_occurrence.roles):
                    log_debug_data(gold_frame, frame_occurrence, matcher,
                                   frame_occurrence.roles,
                                   self.verbnet_classes)

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
            bootstrap_algorithm(all_vn_frames, model,
                                self.verbnet_classes)
        elif options.Options.probability_model is not None:
            self.logger.info("Applying probability model...")
            for frame_occurrence in all_vn_frames:
                # Commented out a version that only allowed possible role
                # combinations after each restriction
                # for i in range(frame_occurrence.num_slots):
                #     roles_for_slot = frame_occurrence.roles[i]
                for i, roles_for_slot in enumerate(frame_occurrence.roles):
                    if len(roles_for_slot) > 1:
                        new_role = model.best_role(
                            roles_for_slot,
                            frame_occurrence.slot_types[i],
                            frame_occurrence.slot_preps[i],
                            frame_occurrence.predicate,
                            options.Options.probability_model)
                        if new_role is not None:
                            frame_occurrence.restrict_slot_to_role(i, new_role)
                frame_occurrence.select_likeliest_matches()

            if options.Options.loglevel == logging.DEBUG:
                display_debug()
        else:
            self.logger.info("No probability model")
        count_annotations=0
        if conllinput is not None:
            self.logger.info("\n## Dumping semantic CoNLL...")
            semantic_appender = ConllSemanticAppender(conllinput)
            # vn_frame: VerbnetFrameOccurrence
            self.logger.debug("VERBNETFRAME_LETSCHECK : {all_vn_frames}")
            for vn_frame in all_vn_frames:
                if vn_frame.best_classes():
                    if options.Options.framelexicon == FrameLexicon.VerbNet:
                        semantic_appender.add_verbnet_frame_annotation(vn_frame)  # noqa
                        count_annotations+=1
                    elif options.Options.framelexicon == FrameLexicon.FrameNet:
                        semantic_appender.add_framenet_frame_annotation(
                            self.role_matcher.possible_framenet_mappings(vn_frame))  # noqa
                        count_annotations+=1
                    else:
                        self.logger.error(
                            f"Error: unknown frame lexicon for output "
                            f"{options.Options.framelexicon}")
            if options.Options.conll_output is None:
                self.logger.debug(f'\nannotate: result '
                                  f'{str(semantic_appender)}')
                if options.Options.loglevel == logging.DEBUG:
                    display_debug()
                    display_errors_num()
                    display_error_details()
                    display_mapping_errors()
                self.logger.debug(str(semantic_appender))
            else:
                semantic_appender.dump_semantic_file(options.Options.
                                                     conll_output)

        else:
            self.logger.info("\n## Evaluation")
            stats.stats_quality(
                all_annotated_frames, all_vn_frames,
                self.frames_for_verb, self.verbnet_classes,
                options.Options.argument_identification, self.frameNet)
            stats.display_stats(options.Options.argument_identification)

            if options.Options.dump:
                dumper.dump(options.Options.dump_file,
                            stats.annotated_frames_stats)
        print(count_annotations)
