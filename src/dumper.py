#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
import sys
import getopt

import framematcher


data = {
    "frame_matching":[],
    "prob_model":[]
}

def add_data_frame_matching(annotated_frames, vn_frames, role_matcher,
    verbnet_classes, verbnet_predicates, matching_algorithm):
    
    data["frame_matching"] = clone_and_eval(
            annotated_frames, vn_frames, role_matcher, verbnet_classes,
            frame_matching=True, verbnet_predicates=verbnet_predicates,
            matching_algorithm=matching_algorithm)
    
def add_data_prob_model(annotated_frames, vn_frames, role_matcher, verbnet_classes):
    data["prob_model"] = clone_and_eval(
            annotated_frames, vn_frames, role_matcher, verbnet_classes)

def clone_and_eval(annotated_frames, vn_frames, role_matcher,
    verbnet_classes, frame_matching = False, verbnet_predicates = None,
    matching_algorithm = ""):
    
    result = []
    for gold_fn_frame, found_vn_frame in zip(annotated_frames, vn_frames):
        if frame_matching:
            try:
                matcher = framematcher.FrameMatcher(found_vn_frame, matching_algorithm)
                
                for test_frame in verbnet_predicates[gold_fn_frame.predicate.lemma]:
                    matcher.new_match(test_frame)
            except framematcher.EmptyFrameError:
                pass

            best_match_structures = [x[0].structure for x in matcher.best_data]
            best_match_roles = [x[0].roles for x in matcher.best_data]
               
        for i, slot in enumerate(found_vn_frame.roles):
            status = "?"
            possible_roles = None
            if len(slot) == 0: status = "no_role"

            try:
                possible_roles = role_matcher.possible_vn_roles(
                    gold_fn_frame.args[i].role,
                    fn_frame=gold_fn_frame.frame_name,
                    vn_classes=verbnet_classes[gold_fn_frame.predicate.lemma]
                    )
            except Exception:
                status = "mapping_impossible"

            if status == "?":
                if len(possible_roles) > 1:
                    status = "mapping_ambiguous"
                elif next(iter(possible_roles)) in slot:
                    if len(slot) == 1:  status = "one_role_good"
                    else: status = "several_roles_good"
                elif len(slot) >= 1:
                    if len(slot) == 1: status = "one_role_bad"
                    else: status = "several_roles_bad"

            to_add = {
                "slot":i,
                "structure":found_vn_frame.structure,
                "frame_name":gold_fn_frame.frame_name,
                "sentence":gold_fn_frame.sentence,
                "predicate":gold_fn_frame.predicate.lemma,
                "argument":gold_fn_frame.args[i].text,
                "status":status,
                "role_list":slot,
                "correct_role_fn":gold_fn_frame.args[i].role,
                "correct_role_vn":possible_roles
            }
                           
            if frame_matching:
                to_add["best_match_structures"] = best_match_structures
                to_add["best_match_roles"] = best_match_roles

            result.append(to_add)

    return result

def diff_status(data1, data2):
    good_status = ["one_role_good", "several_roles_good"]
    bad_status = ["one_role_bad", "several_roles_bad", "no_role"]
    
    print("Good -> bad:")
    for slot_data1, slot_data2 in zip(data1, data2):
        if slot_data1["status"] in good_status and slot_data2["status"] in bad_status:
            print("\n")
            print_slot(slot_data1)
            print_slot(slot_data2)
            
    print("Bad -> good:")
    for slot_data1, slot_data2 in zip(data1, data2):
        if slot_data2["status"] in good_status and slot_data1["status"] in bad_status:
            print("\n")
            print_slot(slot_data1)
            print_slot(slot_data2)
    
def diff_all(data1, data2):
    for slot_data1, slot_data2 in zip(data1, data2):
        if slot_data1 != slot_data2:
            print("\n")
            print_slot(slot_data1)
            print_slot(slot_data2)

def print_slot(slot_data):
    print(
        "Sentence: {}\n"
        "Predicate: {}\n"
        "Argument: {}\n"
        "Frame instance structure: {}\n"
        "Frame name: {}\n"
        "Role list: {}\n"
        "Correct role: {} (FrameNet) -> {} (VerbNet)\n"
        "Status: {}\n".format(
            slot_data["sentence"],
            slot_data["predicate"],
            slot_data["argument"],
            slot_data["structure"],
            slot_data["frame_name"],
            slot_data["role_list"],
            slot_data["correct_role_fn"], slot_data["correct_role_vn"],
            slot_data["status"]
        )
    )
    if "best_match_structures" in slot_data:
        print(
            "Frame matching best structures {}\n"
            "Frame matching best roles {}\n".format(
                slot_data["best_match_structures"],
                slot_data["best_match_roles"]
            )
        )
  
def dump(filename):
     with open("dump/"+filename, "wb") as picklefile:
        pickle.dump(data, picklefile)

if __name__ == "__main__":
    status = True
    
    options = getopt.getopt(sys.argv[1:], "", ["status", "all"])
    
    for opt,value in options[0]:
        if opt == "--status":
            status = True
        if opt == "--all":
            status = False

    if len(options[1]) >= 2:
        filename1 = options[1][0]
        filename2 = options[1][1]
    else:
        print("Syntax : dump.py file1 file2")
    
    with open("dump/"+filename1, "rb") as picklefile:
        data1 = pickle.load(picklefile)
    with open("dump/"+filename2, "rb") as picklefile:
        data2 = pickle.load(picklefile)
    
    print("\n\nDifferences after frame matching:")
    if status:
        diff_status(data1["frame_matching"], data2["frame_matching"])
    else:
        diff_all(data1["frame_matching"], data2["frame_matching"])
    
    print("\n\nDifferences after probability model:")
    if status:
        diff_status(data1["prob_model"], data2["prob_model"])
    else:
        diff_all(data1["prob_model"], data2["prob_model"])

    
