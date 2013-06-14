#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import framenetallreader
import paths
from stats import stats_data
from framestructure import *
from collections import defaultdict
from collections import Counter
import os
import sys
import unittest

"""Fill the roles of some frames extracted from the syntactic parser output
using the annotated FrameNet data.
"""

def fill_roles(extracted_frames, verbnet_classes, role_matcher):
    """Fills the roles of some frames argument, when possible.
    Note : extracted_frames must be sorted by file.
    Note : extracted_frames is altered, even if the final result is returned.
    
    :param extracted_frames: The frames.
    :type extracted_frames: Frame List.
    :param verbnet_classes: The VerbNet lexicon, used to determine which frames
    from the corpus we should have extracted.
    :type verbnet_classes: Str Dict.
    """
    
    frames = defaultdict(lambda : (defaultdict(lambda : []) ))
    for frame in extracted_frames:
        frames[frame.filename][frame.sentence_id_fn_parsed].append(frame)
    
    fn_reader = framenetallreader.FNAllReader(
            paths.FRAMENET_FULLTEXT, paths.FRAMENET_PARSED,
            core_args_only = True, keep_unannotated = True)
    
    previous_id = -1
    sentence_frames = []
    for frame in fn_reader.frames:
        stats_data["args_instanciated"] += len(
            [x for x in frame.args if x.instanciated])
        
        for arg in frame.args:
            if not arg.instanciated: continue
            try:
                possible_roles = role_matcher.possible_vn_roles(
                    arg.role,
                    fn_frame=frame.frame_name,
                    vn_classes=verbnet_classes[frame.predicate.lemma])
            except Exception: continue
            if len(possible_roles) == 1:
                stats_data["args_annotated_mapping_ok"] += 1
            
        if frame.sentence_id_fn_parsed == -1: continue
        if frame.sentence_id_fn_parsed != previous_id:
            sentence_frames = frames[frame.filename][frame.sentence_id_fn_parsed]
            for extracted_frame in sentence_frames:
                correct_num_tags(extracted_frame, frame.sentence)
        previous_id = frame.sentence_id_fn_parsed
        
        frame_found = False
        for extracted_frame in sentence_frames:
            # See if we have the two "same" frames
            if predicate_match(extracted_frame.predicate, frame.predicate):
                stats_data["frame_extracted_good"] += 1
                handle_frame(extracted_frame, frame)
                frame_found = True
                break
        if not frame_found:
            num_args = len([x for x in frame.args if x.instanciated])
            if frame.predicate.lemma not in verbnet_classes:
                stats_data["frame_not_extracted_not_verbnet"] += 1
                stats_data["arg_not_extracted_not_verbnet"] += num_args

            stats_data["frame_not_extracted"] += 1
            stats_data["arg_not_extracted"] += num_args
        previous_id = frame.sentence_id_fn_parsed

    stats_data["frame_extracted_bad"] = (
        len(extracted_frames) - stats_data["frame_extracted_good"])

    # Discard every frame for which there was no match
    return extracted_frames

def correct_num_tags(extracted_frame, original_sentence):
    """ Replace <num> tags by their real equivalents
    and update begin/end attributes where necessary.
    
    :param extracted_frame: The frame that contains <num> tags
    :type extracted_frame: Frame
    :param original_sentence: The original unaltered sentence of the frame
    :type original_sentence: str
    
    """
    
    search = "<num>"
    correct_words = original_sentence.split(" ")

    for word_number, word in enumerate(extracted_frame.sentence.split(" ")):
        if word != search: continue
        
        position = extracted_frame.sentence.find(search)
        replacement = correct_words[word_number]
        offset = len(replacement) - len(search)
        
        extracted_frame.sentence = extracted_frame.sentence.replace(
            search, replacement, 1)
        
        if extracted_frame.predicate.begin > position:
            extracted_frame.predicate.begin += offset
            extracted_frame.predicate.end += offset
        for arg in extracted_frame.args:
            if arg.begin > position:
                arg.begin += offset
            elif arg.end > position:
                arg.text = arg.text.replace(search, replacement, 1)
            if arg.end > position:
                arg.end += offset
    
def predicate_match(predicate1, predicate2):
    """ Tells whether two predicates in the same sentence belongs to the same frame"""
    return predicate1.begin == predicate2.begin

def handle_frame(extracted_frame, annotated_frame):
    # Update the frame name
    extracted_frame.frame_name = annotated_frame.frame_name
    
    extracted_frame.arg_annotated = annotated_frame.arg_annotated
    
    good_args, partial_args = 0, 0
    
    # Update the argument roles and statistics
    for annotated_arg in annotated_frame.args:
        if not annotated_arg.instanciated: continue
        
        arg_found = False
        for extracted_arg in extracted_frame.args:
            score = match_score(extracted_arg, annotated_arg)
            if score == 1:
                good_args += 1
                extracted_arg.role = annotated_arg.role
                extracted_arg.annotated = True
                arg_found = True
                break
            elif score > 0.5:
                partial_args += 1
                extracted_arg.role = annotated_arg.role
                extracted_arg.annotated = True
                arg_found = True
                break
        if not arg_found:
            stats_data["arg_not_extracted"] += 1
    
    if extracted_frame.arg_annotated:
        stats_data["arg_extracted_good"] += good_args
        stats_data["arg_extracted_bad"] += (len(extracted_frame.args) - good_args - partial_args)
        stats_data["arg_extracted_partial"] += partial_args

def match_score(arg1, arg2):
    intersect = 1 + min(arg1.end, arg2.end) - max(arg1.begin, arg2.begin)
    sum_length = (1 + arg1.end - arg1.begin) + (1 + arg2.end - arg2.begin)
    return 2 * max(0, intersect) / sum_length

class RoleExtractorTest(unittest.TestCase):
    def test_num_replacements(self):
        initial_sentence = ("She tells me that the <num> people we helped find"
                            " jobs in <num> earned approximately $ <num>"
                            " million dollars .")
        final_sentence = ("She tells me that the 3,666 people we helped find"
                          " jobs in 1998 earned approximately $ 49"
                          " million dollars .")
                          
        initial_predicate = Predicate(64, 69, "earned", "earn")
        final_predicate = Predicate(63, 68, "earned", "earn")
        
        initial_args = [
            Arg(18, 62, "the <num> people we helped find jobs in <num>",
                "role1", True, "phrase_type"),
            Arg(71, 107, "approximately $ <num> million dollars",
                "role2", True, "phrase_type")
        ]
        final_args = [
            Arg(18, 61, "the 3,666 people we helped find jobs in 1998",
                "role1", True, "phrase_type"),
            Arg(70, 103, "approximately $ 49 million dollars",
                "role2", True, "phrase_type")
        ]
        words = []
        
        frame = Frame(initial_sentence, initial_predicate, initial_args,
            words, "fn_frame_name")
        
        correct_num_tags(frame, final_sentence)
        self.assertEqual(frame.sentence, final_sentence)
        self.assertEqual(frame.predicate, final_predicate)
        self.assertEqual(frame.args, final_args)

if __name__ == "__main__":
    #unittest.main()
      
    import verbnetreader
    from argguesser import ArgGuesser
    from rolematcher import VnFnRoleMatcher

    role_matcher = VnFnRoleMatcher(paths.VNFN_MATCHING)
    verbnet_classes = verbnetreader.VerbnetReader(paths.VERBNET_PATH).classes
    arg_finder = ArgGuesser(paths.FRAMENET_PARSED, verbnet_classes)

    frames = [x for x in arg_finder.handle_corpus()]

    len_begin = len(frames)
    frames = fill_roles(frames, verbnet_classes, role_matcher)

    print("\nExtracted {} correct and {} incorrect (non-annotated) frames.\n"
          "Did not extract {} annotated frames ({} had a predicate not in VerbNet).\n"
          "Extracted {} correct, {} partial-match and {} incorrect arguments.\n"
          "Did not extract {} annotated arguments ({} had a predicate not in VerbNet).\n".format(
          stats_data["frame_extracted_good"], stats_data["frame_extracted_bad"],
          stats_data["frame_not_extracted"], stats_data["frame_not_extracted_not_verbnet"],
          stats_data["arg_extracted_good"], stats_data["arg_extracted_partial"],
          stats_data["arg_extracted_bad"],
          stats_data["arg_not_extracted"], stats_data["arg_not_extracted_not_verbnet"]
    ))


