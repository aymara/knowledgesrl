#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import framenetreader
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
    
    path = paths.FRAMENET_FULLTEXT
    i = 0
    i_max = len(extracted_frames)

    files = os.listdir(path)
    for filename in sorted(files):
        if not filename[-4:] == ".xml": continue

        # Skip any file that is not in our corpus
        while i < i_max and extracted_frames[i].filename not in files:
            i += 1

        frames = defaultdict(lambda : [])
        old_i = i

        while i < i_max and extracted_frames[i].filename == filename:
            frames[extracted_frames[i].sentence_id].append(extracted_frames[i])
            i += 1

        handle_file(frames, path+filename, i - old_i, verbnet_classes, role_matcher)
        print(".", file=sys.stderr, end="", flush=True)
    print()

    # Discard every frame for which there was no match
    return [x for x in extracted_frames if not x.frame_name == ""]

def handle_file(extracted_frames, file_path, num_frames, verbnet_classes, role_matcher):
    """Fills the names and roles of every frames in a file
    
    :param extracted_frames: The extracted frames of the file sorted by sentence in a dict.
    :type extracted_frames: Frame List Dict.
    :param file_path: The path to the FrameNet annotation file.
    :type file_path: str.
    :param num_frames: The total number of extracted frames (used for statistics).
    :type num_frames: int.
    :param verbnet_classes: The VerbNet lexicon, used to determine which frames
    from the corpus we should have extracted.
    :type verbnet_classes: str Dict.
    """
    reader = framenetreader.FulltextReader(file_path,
        core_args_only = True, keep_unannotated = True)
    good_frames = 0
    
    previous_id, matching_id = 0, 0

    for annotated_frame in reader.frames:
        stats_data["args_instanciated"] += len(
                    [x for x in annotated_frame.args if x.instanciated])
        
        # Count annotated args with a role mapping ok
        for arg in annotated_frame.args:
            if not arg.instanciated: continue
            try:
                possible_roles = role_matcher.possible_vn_roles(
                    arg.role,
                    fn_frame=annotated_frame.frame_name,
                    vn_classes=verbnet_classes[annotated_frame.predicate.lemma])
            except Exception: continue
            if len(possible_roles) == 1:
                stats_data["args_annotated_mapping_ok"] += 1
        
        matching_id = find_sentence_id(extracted_frames,
                                        annotated_frame.sentence,
                                        annotated_frame.sentence_id)
        if matching_id == 0: continue
        
        # Remove <num> tags from the extracted frames
        if matching_id != previous_id:
            for extracted_frame in extracted_frames[matching_id]:
                correct_num_tags(extracted_frame, annotated_frame.sentence)
        
        frame_found = False
        for extracted_frame in extracted_frames[matching_id]:
            # See if we have the two "same" frames
            if predicate_match(extracted_frame.predicate, annotated_frame.predicate):
                good_frames += 1
                handle_frame(extracted_frame, annotated_frame)
                frame_found = True
                break
        if not frame_found:
            num_args = len([x for x in annotated_frame.args if x.instanciated])
            if annotated_frame.predicate.lemma not in verbnet_classes:
                stats_data["frame_not_extracted_not_verbnet"] += 1
                stats_data["arg_not_extracted_not_verbnet"] += num_args

            stats_data["frame_not_extracted"] += 1
            stats_data["arg_not_extracted"] += num_args
        previous_id = matching_id

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
    for test_id in extracted_frames:
        if len(extracted_frames[test_id]) > 0:
            sentence_2 = extracted_frames[test_id][0].sentence
        
            if sentence_match(sentence_1, sentence_2):
                return test_id
    return 0

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

def sentence_match(sentence_1, sentence_2):
    # This is not necessary but resolves many cases without computing
    # the symetric difference of the two sets of words of the two sentences
    if sentence_1 == sentence_2:
        return True
    
    # The previous test might fail for the two "same" sentences because of
    # minor differences between the two corpora, or because of parsing errors 
    # that change word order
    words_1 = sentence_1.split(" ")
    words_2 = sentence_2.split(" ")
    if len(set(words_1) ^ set(words_2)) > (len(words_1) + len(words_2)) / 6:
         return False
    return True
    
def predicate_match(predicate1, predicate2):
    """ Tells whether two predicates in the same sentence belongs to the same frame"""
    return predicate1.begin == predicate2.begin

def handle_frame(extracted_frame, annotated_frame):
    # Update the frame name
    extracted_frame.frame_name = annotated_frame.frame_name
    
    extracted_frame.annotated = annotated_frame.annotated
    
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


