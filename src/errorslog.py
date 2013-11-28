#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from collections import Counter


errors = {
   "vn_parsing":[],
   "vn_missing":[],
   "frame_without_slot":[],
   "frame_with_slot":[],
   "impossible_role_matching":[],
   "ambiguous_role":[]
}

debug_data = []

def log_ambiguous_role_conversion(frame, arg, role_matcher, verbnet_classes):
    errors["ambiguous_role"].append({
        "file":frame.filename,
        "argument":arg.text,"fn_role":arg.role,"fn_frame":frame.frame_name,
        "predicate":frame.predicate.lemma,
        "predicate_classes":verbnet_classes[frame.predicate.lemma],
        "sentence":frame.sentence,
        "vn_roles":role_matcher.possible_vn_roles(
                arg.role, vn_classes = verbnet_classes[frame.predicate.lemma])
    })

def log_vn_missing(frame):
    errors["vn_missing"].append({
        "file":frame.filename,"sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
    })

def log_frame_with_slot(frame, converted_frame):
    errors["frame_with_slot"].append({
        "file":frame.filename,"sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
        "structure":converted_frame.structure
    })

def log_frame_without_slot(frame, converted_frame):
    errors["frame_without_slot"].append({
        "file":frame.filename,"sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
        "structure":converted_frame.structure
    })

def log_impossible_role_matching(frame, i, msg):
    errors["impossible_role_matching"].append({
        "file":frame.filename, "sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
        "fn_role":frame.args[i].role,
        "fn_frame":frame.frame_name,
        "msg":msg
    })
      
def log_debug_data(frame, converted_frame, matcher, distrib, verbnet):
    debug_data.append({
        "sentence":frame.sentence,
        "predicate":frame.predicate.lemma,
        "args":[x.text for x in frame.args],
        "vbclass":verbnet[frame.predicate.lemma],
        "structure":converted_frame.structure,
        "chosen_frames":matcher.best_frames,
        "result":distrib
    })

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

def display_mapping_errors():
    predicate_errors = Counter()
    for data in errors['frame_without_slot']:
        print(data)
        predicate_errors[data['predicate']] += 1
    print(predicate_errors.most_common(10))
    print("Mapping errors for {} of {} predicates.".format(len(errors['frame_without_slot']), len(errors['frame_without_slot']) + len(errors['frame_with_slot'])))

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
     
