#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import framenetreader
import paths
from stats import stats_data
from collections import defaultdict
from collections import Counter
import os
import sys

"""Fill the roles of some frames extracted from the syntactic parser output
using the annotated FrameNet data.
"""

def fill_roles(extracted_frames, verbnet):
    """Fills the roles of some frames argument, when possible.
    Note : extracted_frames must be sorted by file.
    Note : extracted_frames is altered, even if the final result is returned.
    
    :param extracted_frames: The frames.
    :type extracted_frames: Frame List.
    :param verbnet: The VerbNet lexicon, used to determine which frames
    from the corpus we should have extracted.
    :type verbnet: VerbnetFrame Dict.
    """
    
    print("")
    path = paths.FRAMENET_FULLTEXT
    i = 0
    i_max = len(extracted_frames)
    for filename in sorted(os.listdir(path)):
        if not filename[-4:] == ".xml": continue
        print(".", file=sys.stderr, end="")
        sys.stderr.flush()

        frames = defaultdict(lambda : [])
        old_i = i

        while i < i_max and extracted_frames[i].filename == filename:
            frames[extracted_frames[i].sentence_id].append(extracted_frames[i])
            i += 1

        handle_file(frames, path+filename, i - old_i, verbnet)

    # Discard every frame for which there was no match
    return [x for x in extracted_frames if not x.frame_name == ""]

def handle_file(extracted_frames, file_path, num_frames, verbnet):
    """Fills the names and roles of every frames in a file
    
    :param extracted_frames: The extracted frames of the file sorted by sentence in a dict.
    :type extracted_frames: Frame List Dict.
    :param file_path: The path to the FrameNet annotation file.
    :type file_path: str.
    :param num_frames: The total number of extracted frames (used for statistics).
    :type num_frames: int.
    :param verbnet: The VerbNet lexicon, used to determine which frames
    from the corpus we should have extracted.
    :type verbnet: VerbnetFrame Dict.
    """
    reader = framenetreader.FulltextReader(file_path, core_args_only = True)
    sentence_id = 1
    good_frames = 0

    for annotated_frame in reader.frames:
        matching_id = 0

        matching_id = find_sentence_id(extracted_frames,
                                        annotated_frame.sentence,
                                        annotated_frame.sentence_id)

        frame_found = False
        for extracted_frame in extracted_frames[matching_id]:   
            # See if we have the two "same" frames
            if predicate_match(extracted_frame.predicate, annotated_frame.predicate):
                good_frames += 1
                handle_frame(extracted_frame, annotated_frame)
                frame_found = True
                break
        if not frame_found and annotated_frame.predicate.lemma in verbnet:
            stats_data["frame_not_extracted"] += 1
            stats_data["arg_not_extracted"] += len(annotated_frame.args)
                
    stats_data["frame_extracted_good"] += good_frames
    stats_data["frame_extracted_bad"] += (num_frames - good_frames)


def find_sentence_id(extracted_frames, sentence_1, expected_id):
    """Find the id of the matching sentence of the syntactic annotations
    for a sentence from the annotated corpus.
    We can't be sure that they have the same id because of "junk" sentence
    of the annotated corpus that do not appears in the syntactic annotations.
    
    :param extracted_frames: The frames from the syntactic annotations corpus.
    :type extracted_frames: Frame List Dict.
    :param sentence_1: The sentence we are looking for.
    :type sentence_1: str.
    :param expected_id: The id of the sentence in the annotated corpus.
    :type expected_id: int.
    """
    for i in range(len(extracted_frames)):
        # Loops through every possible ids in ascending order starting at expect_id
        test_id = 1 + (expected_id - 1 + i) % len(extracted_frames)
        
        if len(extracted_frames[test_id]) > 0:
            sentence_2 = extracted_frames[test_id][0].sentence

            # This is not necessary but resolves many cases without computing
            # the symetric difference of the two sets of words of the two sentences
            if sentence_1 == sentence_2:
                return test_id
            
            # The previous test might fail for the two "same" sentences because of
            # minor differences between the two corpora, or because of parsing errors 
            # that change word order
            words_1 = sentence_1.split(" ")
            words_2 = sentence_2.split(" ")
            if len(set(words_1) ^ set(words_2)) > (len(words_1) + len(words_2)) / 6:
                continue
            return test_id
    return 0
    
def predicate_match(predicate1, predicate2):
    """ Tells whether two predicates in the same sentence belongs to the same frame"""
    return predicate1.begin == predicate2.begin

def handle_frame(extracted_frame, annotated_frame):
    # Update the frame name
    extracted_frame.frame_name = annotated_frame.frame_name
    
    good_args = 0
    
    # Update the argument roles and statistics
    for annotated_arg in annotated_frame.args:
        if not annotated_arg.instanciated: continue
        
        arg_found = False
        for extracted_arg in extracted_frame.args:
            if match_score(extracted_arg, annotated_arg) == 1:
                good_args += 1
                extracted_arg.role = annotated_arg.role
                arg_found = True
                break
        if not arg_found:
            stats_data["arg_not_extracted"] += 1
            
    stats_data["arg_extracted_good"] += good_args
    stats_data["arg_extracted_bad"] += (len(extracted_frame.args) - good_args)
    
    # Discard every argument for which there was no match
    extracted_frame.args = [x for x in extracted_frame.args if not x.role == ""]        

def match_score(arg1, arg2):
    if arg1.begin == arg2.begin and arg1.end == arg2.end:
        return 1
    return 0

if __name__ == "__main__":     
    import verbnetreader
    from argguesser import ArgGuesser

    verbnet = verbnetreader.VerbnetReader(paths.VERBNET_PATH).verbs
    arg_finder = ArgGuesser(paths.FRAMENET_PARSED, verbnet)

    frames = [x for x in arg_finder.handle_corpus()]

    len_begin = len(frames)
    frames = fill_roles(frames, verbnet)

    print("\nExtracted {} correct and {} incorrect (non-annotated) frames.\n"
          "Did not extract {} annotated frames.\n"
          "Extracted {} correct, {} partial-match and {} incorrect arguments.\n"
          "Did not extract {} annotated arguments.\n".format(
          stats_data["frame_extracted_good"], stats_data["frame_extracted_bad"],
          stats_data["frame_not_extracted"],
          stats_data["arg_extracted_good"], stats_data["arg_extracted_partial"],
          stats_data["arg_extracted_bad"],
          stats_data["arg_not_extracted"]
    ))


