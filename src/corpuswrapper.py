#!/usr/bin/env python3

"""Wraps the domain-specific corpus wrapper in a single interface.

The goal is to make easier the transition to other corpora than FrameNet. As of
2014-12-17, the code was indeed very FrameNet-oriented, and this is part of the
efforts to get more decoupling."""

from pathlib import Path

from framenetallreader import FNAllReader
from framenetparsedreader import FNParsedReader
from verbnetframe import VerbnetFrameOccurrence
import errorslog
import roleextractor
import argguesser
import stats
import options
import paths
import rolematcher


def get_frames(corpus, verbnet_classes, argid=False):
    if options.conll_input is not None:
        annotation_list = [None]
        parsed_conll_list = [Path(options.conll_input)]
    elif options.corpus == 'FrameNet':
        annotation_list = options.fulltext_annotations
        parsed_conll_list = options.fulltext_parses
    elif options.corpus == 'dicoinfo_fr':
        pass
    else:
        raise Exception('Unknown corpus {}'.format(corpus))

    if options.corpus == 'FrameNet':
        print("Loading FrameNet and VerbNet role mappings...")
        role_matcher = rolematcher.VnFnRoleMatcher(paths.VNFN_MATCHING)

        for annotation_file, parsed_conll_file in zip(annotation_list, parsed_conll_list):
            file_stem = annotation_file.stem if annotation_file else parsed_conll_file.stem
            print(file_stem)
            annotated_frames = []
            vn_frames = []
            fnparsed_reader = FNParsedReader()

            if argid:
                #
                # Argument identification
                #
                arg_guesser = argguesser.ArgGuesser(verbnet_classes)

                # Many instances are not actually FrameNet frames
                new_frame_instances = list(arg_guesser.frame_instances_from_file(
                    fnparsed_reader.sentence_trees(parsed_conll_file), parsed_conll_file))
                new_annotated_frames = roleextractor.fill_gold_roles(
                    new_frame_instances, annotation_file, parsed_conll_file,
                    verbnet_classes, role_matcher)

                for gold_frame, frame_instance in zip(new_annotated_frames, new_frame_instances):
                    annotated_frames.append(gold_frame)
                    vn_frames.append(VerbnetFrameOccurrence.build_from_frame(gold_frame, conll_frame_instance=frame_instance))
            else:
                #
                # Load gold arguments
                #
                fn_reader = FNAllReader(
                    add_non_core_args=options.add_non_core_args)

                for framenet_instance in fn_reader.iter_frames(annotation_file, parsed_conll_file):
                    annotated_frames.append(framenet_instance)
                    vn_frames.append(VerbnetFrameOccurrence.build_from_frame(
                        framenet_instance, conll_frame_instance=None))

                stats.stats_data["files"] += fn_reader.stats["files"]

            yield annotated_frames, vn_frames
