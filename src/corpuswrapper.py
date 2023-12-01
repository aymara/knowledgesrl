#!/usr/bin/env python3

"""Wraps the domain-specific corpus wrapper in a single interface.

The goal is to make easier the transition to other corpora than FrameNet. As of
2014-12-17, the code was indeed very FrameNet-oriented, and this is part of the
efforts to get more decoupling.

Defines a unique function: get_frames

"""

from pathlib import Path

from framenetallreader import FNAllReader
from verbnetframe import VerbnetFrameOccurrence
import errorslog
import roleextractor
import argguesser
import stats
import options
import paths
import rolematcher

import logging

def get_frames(corpus, verbnet_classes, frameNet, argid=False):
    """ Fills two list of the same size with content dependent of the kind of input
    
    The two lists are annotation_list and parsed_conll_list
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(options.Options.loglevel)
    logger.debug("get_frames corpus={} input={}".format(
        corpus, options.Options.conll_input))

    if options.Options.conll_input is not None:
        annotation_list = [None]
        parsed_conll_list = [Path(options.Options.conll_input)]
    elif options.Options.corpus == 'FrameNet':
        annotation_list = options.Options.fulltext_annotations
        parsed_conll_list = options.Options.fulltext_parses
        assert(len(annotation_list) == len(parsed_conll_list))
    elif options.Options.corpus == 'dicoinfo_fr':
        pass
    else:
        raise Exception('Unknown corpus {}'.format(corpus))

    if options.Options.corpus == 'FrameNet':
        logger.info("Loading FrameNet and VerbNet role mappings %s ..."%paths.Paths.VNFN_MATCHING)
        role_matcher = rolematcher.VnFnRoleMatcher(paths.Paths.VNFN_MATCHING, frameNet)

        for annotation_file, parsed_conll_file in zip(annotation_list, parsed_conll_list):
            logger.debug("Handling {} {}" .format(annotation_file, parsed_conll_file))
            file_stem = annotation_file.stem if annotation_file else parsed_conll_file.stem
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
                    new_frame_instances, annotation_file, parsed_conll_file,
                    verbnet_classes, role_matcher)
                logger.debug('got nb new_annotated_frames: {}'.format(len(new_annotated_frames)))
                
                for gold_frame, frame_instance in zip(new_annotated_frames, new_frame_instances):
                    annotated_frames.append(gold_frame)
                    vn_frames.append(VerbnetFrameOccurrence.build_from_frame(gold_frame, conll_frame_instance=frame_instance))
            else:
                logger.info("Load gold arguments")
                #
                # Load gold arguments
                #
                fn_reader = FNAllReader(
                    add_non_core_args=options.Options.add_non_core_args)

                for framenet_instance in fn_reader.iter_frames(annotation_file, parsed_conll_file):
                    annotated_frames.append(framenet_instance)
                    vn_frames.append(VerbnetFrameOccurrence.build_from_frame(
                        framenet_instance, conll_frame_instance=None))

                stats.stats_data["files"] += fn_reader.stats["files"]

            yield annotated_frames, vn_frames
