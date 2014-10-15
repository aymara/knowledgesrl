#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
import sys
import os
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
    for gold_fn_frame, frame_instance in zip(annotated_frames, vn_frames):
        if frame_matching:
            if frame_instance.num_slots == 0:
                continue

            matcher = framematcher.FrameMatcher(frame_instance, matching_algorithm)

            for test_frame in verbnet_predicates[gold_fn_frame.predicate.lemma]:
                matcher.new_match(test_frame)

            best_matches_syntax = [x[0].syntax for x in matcher.best_data]
            best_matches_roles = [x[0].roles for x in matcher.best_data]
               
        for i, slot in enumerate(frame_instance.roles):
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
                "structure":frame_instance.structure,
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
                to_add["best_matches_syntax"] = best_matches_syntax
                to_add["best_matches_roles"] = best_matches_roles

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
    if "best_matches_syntax" in slot_data:
        print(
            "Frame matching best syntax{}\n"
            "Frame matching best roles {}\n".format(
                slot_data["best_matches_syntax"],
                slot_data["best_matches_roles"]
            )
        )
  
def dump(filename):
    os.makedirs('dump', exist_ok=True)
    with open("dump/"+filename, "wb") as picklefile:
        pickle.dump(data, picklefile)
    print('Dumped to dump/{}'.format(filename))

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
