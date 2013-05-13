#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import framenetreader
from framestructure import *
import verbnetreader
import framematcher
import rolematcher
import os
import sys
import getopt
import random
from collections import Counter

options = getopt.getopt(sys.argv[1:], "d:", "fmatching-algo=")
    
corpus_path = "../data/fndata-1.5/fulltext/"
verbnet_path = "../data/verbnet-3.2/"
debug = False
n_debug = 20
framematcher.matching_algorithm = 1

for opt,value in options[0]:
    if opt == "-d":
        debug = True
        value = 0 if value == "" else int(value)
        if value > 0:
            n_debug = value
    if opt == "--fmatching-algo" and value == 0:
        framematcher.matching_algorithm = 0

stats = {
    "files":0,
    "frames":0, "frames_kept":0,
    "args":0, "args_kept":0,
    "one_role":0, "no_role":0,
    "one_correct_role":0, "one_bad_role":0,
    "ambiguous_ok":0, "ambiguous_bad":0,
}

ambiguous_mapping = {
    # Stats of ambiguous mapping when ignoring the FN frame given by the annotations
    "verbs":[], "args_total":0, "args":0,
    # Stats of ambiguous mapping remaining despite the FN frame given by the annotations
    "verbs_with_frame":[], "args_total_with_frame":0, "args_with_frame":0
}

errors = {
   "vn_parsing":[],
   "vn_missing":[],
   "unannotated_layer":[], "predicate_was_arg":[],
   "missing_phrase_type":[], "missing_predicate_data":[],
   "frame_without_slot":[],
   "impossible_role_matching":[],
   "ambiguous_role":[]
}

debug_data = []

def init_verbnet(path):
    reader = verbnetreader.VerbnetReader(path)
    errors["vn_parsing"] = reader.unhandled
    return reader.verbs, reader.classes

def init_fn_reader(path):
    reader = framenetreader.FulltextReader(corpus_path+filename)
    
    errors["unannotated_layer"] += reader.ignored_layers
    errors["predicate_was_arg"] += reader.predicate_is_arg
    errors["missing_phrase_type"] += reader.phrase_not_found
    errors["missing_predicate_data"] += reader.missing_predicate_data
    
    return reader

def stats_performance(good, can_conclude, num_slot):
    if good:
        if num_slot == 1:
            stats["one_correct_role"] += 1
        else:
            stats["ambiguous_ok"] += 1
    elif can_conclude:
        if num_slot == 1:
            stats["one_bad_role"] += 1
        else:
            stats["ambiguous_bad"] += 1    
                    
def stats_frame(distrib, num_args):
    stats["args_kept"] += num_args
    stats["frames_kept"] += 1
    stats["one_role"] += sum([1 if len(x) == 1 else 0 for x in distrib])
    stats["no_role"] += num_args - sum([0 if x == set() else 1 for x in distrib])  
    stats["args_ambiguous"] = stats["args_kept"] - (stats["one_role"] + stats["no_role"])
    
def stats_ambiguous_roles(frame, num_args):
    found_ambiguous_arg = False
    found_ambiguous_arg_2 = False
    for arg in frame.args:
        if not arg.instanciated: continue
        try:
            if len(role_matcher.possible_vn_roles(
                arg.role, vn_classes = verbnet_classes[frame.predicate.lemma]
            )) > 1:
                if not found_ambiguous_arg:
                    found_ambiguous_arg = True
                    ambiguous_mapping["verbs"].append(frame.predicate.lemma)
                    ambiguous_mapping["args_total"] += num_args
                ambiguous_mapping["args"] += 1

                log_ambiguous_role_conversion(filename, frame, arg)
                
                if len(role_matcher.possible_vn_roles(
                    arg.role,
                    fn_frame = frame.frame_name,
                    vn_classes = verbnet_classes[frame.predicate.lemma]
                )) > 1:
                    if not found_ambiguous_arg_2:
                        found_ambiguous_arg_2 = True
                        ambiguous_mapping["verbs_with_frame"].append(frame.predicate.lemma)
                        ambiguous_mapping["args_total_with_frame"] += num_args
                    ambiguous_mapping["args_with_frame"] += 1
        except rolematcher.RoleMatchingError:
            pass

def log_ambiguous_role_conversion(filename, frame, arg):
    errors["ambiguous_role"].append({
        "file":filename,
        "argument":arg.text,"fn_role":arg.role,"fn_frame":frame.frame_name,
        "predicate":frame.predicate.lemma,
        "predicate_classes":verbnet_classes[frame.predicate.lemma],
        "sentence":frame.sentence,
        "vn_roles":role_matcher.possible_vn_roles(
                arg.role, vn_classes = verbnet_classes[frame.predicate.lemma])
    })

def log_vn_missing(filename, frame):
    errors["vn_missing"].append({
        "file":filename,"sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
    })

def log_frame_without_slot(filename, frame, converted_frame):
    errors["frame_without_slot"].append({
        "file":filename,"sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
        "structure":converted_frame.structure
    })

def log_impossible_role_matching(filename, frame, role, msg):
    errors["impossible_role_matching"].append({
        "file":filename, "sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
        "fn_role":frame.args[i].role,
        "vn_role":role,
        "fn_frame":frame.frame_name,
        "msg":msg
    })
    
def log_debug_data(frame, converted_frame, matcher, distrib):
    debug_data.append({
        "sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
        "args":[x.text for x in frame.args],
        "vbclass":verbnet[frame.predicate.lemma],
        "structure":converted_frame.structure,
        "chosen_frames":matcher.best_frames,
        "result":distrib
    })
  
def display_stats():
    print(
        "\n\nFound {} args and {} frames in {} files\n"
        "{} instanciated args and {} frames were kept\n"
        "{} args were discarded by frame matching\n\n"
        
        "{} roles were directly attributed after frame matching\n"
        "{} of thoose where correctly attributed\n"
        "{} of thoose where incorrectly attributed\n"
        "We could not conclude for {} of thoose\n\n"
        
        "The role of {} args are still ambiguous\n"
        "The good role is in the role list in {} cases\n"
        "It was not in {} cases\n"
        "We could not conclude for {} of thoose\n\n".format(
            stats["args"], stats["frames"], stats["files"],
            stats["args_kept"], stats["frames_kept"], stats["no_role"],
            
            stats["one_role"], stats["one_correct_role"], stats["one_bad_role"],
            stats["one_role"] - (stats["one_bad_role"] + stats["one_correct_role"]),
            
            stats["args_ambiguous"], stats["ambiguous_ok"], stats["ambiguous_bad"],
            stats["args_ambiguous"] - (stats["ambiguous_ok"] + stats["ambiguous_bad"]))
    )
    print(
        "Ambiguous VerbNet roles:\n"
        "With FrameNet frame indication:\n"
        "\tArguments: {}\n"
        "\tFrames: {}\n"
        "\tTotal number of arguments in those frames: {}\n"
        "Without FrameNet frame indication:\n"
        "\tArguments: {}\n"
        "\tFrames: {}\n"
        "\tTotal number of arguments in those frames: {}\n".format(
            ambiguous_mapping["args_with_frame"], len(ambiguous_mapping["verbs_with_frame"]),
            ambiguous_mapping["args_total_with_frame"], ambiguous_mapping["args"],
            len(ambiguous_mapping["verbs"]), ambiguous_mapping["args_total"]
        )
    )
    """count_with_frame = Counter(ambiguous_mapping["verbs_with_frame"])
    print(
        "Verbs list :\n"
        "(verb) - (number of ambiguous args without frame indication)"
        " - (number of ambiguous args with frame indications)"
    )
    for v, n1 in Counter(ambiguous_mapping["verbs"]).most_common():
        n2 = count_with_frame[v] if v in count_with_frame else 0
        print("{} : {} - {}".format(v, n1, n2))"""

def display_errors_num():
    print(
        "\n\nProblems :\n"
        "{} unhandled case were encoutered while parsing VerbNet\n"
        "Ignored {} frame for which predicate data was missing\n"
        "Ignored {} non-annotated layers in FrameNet\n"
        "Marked {} arguments which were also predicate as NI\n"
        "Could not retrieve phrase type of {} arguments in FrameNet\n"
        "Ignored {} FrameNet frames which predicate was not in VerbNet\n"
        "Ignored {} empty FrameNet frames\n"
        "Was not able to compare {} roles\n\n".format(
            len(errors["vn_parsing"]), len(errors["missing_predicate_data"]),
            len(errors["unannotated_layer"]), len(errors["predicate_was_arg"]),
            len(errors["missing_phrase_type"]), len(errors["vn_missing"]),
            len(errors["frame_without_slot"]), len(errors["impossible_role_matching"]))
    )

def display_error_details():
    #for data in errors["vn_parsing"]: print(data) 
    #for data in errors["missing_predicate_data"]: print(data) 
    #for data in errors["unannotated_layer"]: print(data) 
    #for data in errors["predicate_was_arg"]: print(data) 
    #for data in errors["missing_phrase_type"]: print(data) 
    #for data in errors["vn_missing"]: print(data)          
    #for data in errors["frame_without_slot"]: print(data)
    #for data in errors["impossible_role_matching"]: print(data)
    #for data in errors["ambiguous_role"]: print(data)
    pass

def display_debug(n):
    random.shuffle(debug_data)
    for i in range(0, n):
        print(debug_data[i]["sentence"])
        print("Predicate : "+debug_data[i]["predicate"])
        print("Structure : "+" ".join(debug_data[i]["structure"]))
        print("Arguments :")
        for arg in debug_data[i]["args"]:
            print(arg)
        print("VerbNet data : ")
        for vbframe in debug_data[i]["vbclass"]:
            print(vbframe)
        print("Chosen frames : ")
        for vbframe in debug_data[i]["chosen_frames"]:
            print(vbframe)
        print("Result : ")
        print(debug_data[i]["result"])
        print("\n\n")
        
verbnet, verbnet_classes = init_verbnet(verbnet_path)

role_matcher = rolematcher.VnFnRoleMatcher(rolematcher.role_matching_file)

for filename in os.listdir(corpus_path):
    if not filename[-4:] == ".xml": continue
    print(filename, file=sys.stderr)

    if stats["files"] % 100 == 0 and stats["files"] > 0:
        print("{} {} {}".format(
            stats["files"], stats["frames"], stats["args"]), file=sys.stderr)   
     
    fn_reader = init_fn_reader(corpus_path + filename)

    for frame in fn_reader.frames:
        stats["frames"] += 1
        stats["args"] += len(frame.args)

        if not frame.predicate.lemma in verbnet:
            log_vn_missing(filename, frame)
            continue
        
        converted_frame = VerbnetFrame.build_from_frame(frame)
 
        num_instanciated = sum([1 if x.instanciated else 0 for x in frame.args])

        stats_ambiguous_roles(frame, num_instanciated)
         
        try:
            matcher = framematcher.FrameMatcher(frame.predicate.lemma, converted_frame)
        except framematcher.EmptyFrameError:
            log_frame_without_slot(filename, frame, converted_frame)
            continue

        for test_frame in verbnet[frame.predicate.lemma]:
            matcher.new_match(test_frame)       

        distrib = matcher.possible_distribs()

        for i, slot in enumerate(distrib):
            if len(slot) == 0: continue
            good = False
            can_conclude = True
            for role in slot:
                try:
                    if role_matcher.match(
                        frame.args[i].role, role,
                        frame.frame_name, verbnet_classes[frame.predicate.lemma]
                    ):
                        good = True
                        break
                except rolematcher.RoleMatchingError as e:
                    can_conclude = False
                    log_impossible_role_matching(filename, frame, role, e.msg)
            
            stats_performance(good, can_conclude, len(slot))          

        if debug and set() in distrib:
            log_debug_data(frame, converted_frame, matcher, distrib)
        
        stats_frame(distrib, num_instanciated)
    stats["files"] += 1

display_stats()
display_errors_num()
display_error_details()
if debug: display_debug(n_debug)


