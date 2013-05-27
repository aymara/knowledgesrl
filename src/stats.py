#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
from rolematcher import RoleMatchingError
from errorslog import *

stats_data = {
    "files":0,
    "frames":0, 
    "frames_kept":0,
    "args":0, 
    "args_kept":0,
    "one_role":0, 
    "no_role":0,
    "one_correct_role":0, 
    "one_bad_role":0,
    "several_roles_ok":0, 
    "several_roles_bad":0,
    "roles_conversion_impossible":0, 
    "roles_conversion_ambiguous":0
}

ambiguous_mapping = {
    # Stats of ambiguous mapping when ignoring the FN frame given by the annotations
    "verbs":[], "args_total":0, "args":0,
    # Stats of ambiguous mapping remaining despite the FN frame given by the annotations
    "verbs_with_frame":[], "args_total_with_frame":0, "args_with_frame":0
}
  
def display_stats():
    stats_data["several_roles"] = stats_data["args_kept"] - (stats_data["one_role"] + stats_data["no_role"])
    print(
        "\n\nFiles: {} - annotated frames: {} - annotated args: {}\n"
        "Frames with predicate in VerbNet: {} frames ({} args) \n\n"
        
        "Frame matching:\n"
        "{} args without possible role\n"
        "{} args with exactly one possible role\n"
        "\t{} correct\n"
        "\t{} not correct\n"
        "\t{} cases where we cannot conclude (no role mapping for "
        "any possible VerbNet class and this frame or several possible roles)\n"
        "{} args with multiple possible roles\n"
        "\t{} correct (correct role is in role list)\n"
        "\t{} not correct (correct role is not in role list)\n"
        "\t{} cases where we cannot conclude (no role mapping for "
        "any possible VerbNet class and this frame or several possible roles)\n\n"
        "Role conversion issues:\n"
        "\t{} args with several possible VerbNet roles\n"
        "\t{} args for which no mapping between FrameNet and VerbNet roles was found"
        "\n\n".format(
            stats_data["files"], stats_data["frames"], stats_data["args"],
            stats_data["frames_kept"], stats_data["args_kept"],
            
            stats_data["no_role"],
            
            stats_data["one_role"], stats_data["one_correct_role"], stats_data["one_bad_role"],
            stats_data["one_role"] - (stats_data["one_bad_role"] + stats_data["one_correct_role"]),
            
            stats_data["several_roles"], stats_data["several_roles_ok"],
            stats_data["several_roles_bad"],
            stats_data["several_roles"] - (stats_data["several_roles_ok"] + stats_data["several_roles_bad"]),
            stats_data["roles_conversion_ambiguous"],
            stats_data["roles_conversion_impossible"])
    )
    
def display_stats_ambiguous_mapping():
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
    count_with_frame = Counter(ambiguous_mapping["verbs_with_frame"])
    print(
        "Verbs list :\n"
        "(verb) - (number of ambiguous args without frame indication)"
        " - (number of ambiguous args with frame indications)"
    )
    for v, n1 in Counter(ambiguous_mapping["verbs"]).most_common():
        n2 = count_with_frame[v] if v in count_with_frame else 0
        print("{:>12}: {:>3} - {:<3}".format(v, n1, n2))
                    
def stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, debug):
    stats_data["roles_conversion_impossible"] = 0
    stats_data["roles_conversion_ambiguous"] = 0
    stats_data["one_correct_role"] = 0
    stats_data["several_roles_ok"] = 0
    stats_data["one_bad_role"] = 0
    stats_data["several_roles_bad"] = 0
    stats_data["one_role"] = 0
    stats_data["no_role"] = 0
    
    for good_frame, frame in zip(annotated_frames, vn_frames):    
        for i, slot in enumerate(frame.roles):
            if len(slot) == 0: stats_data["no_role"] += 1
            elif len(slot) == 1: stats_data["one_role"] += 1
            
            try:
                possible_roles = role_matcher.possible_vn_roles(
                    good_frame.args[i].role,
                    fn_frame=good_frame.frame_name,
                    vn_classes=verbnet_classes[good_frame.predicate.lemma]
                    )
            except RoleMatchingError as e:
                stats_data["roles_conversion_impossible"] += 1
                continue
  
            if len(possible_roles) > 1:
                stats_data["roles_conversion_ambiguous"] += 1
            elif next(iter(possible_roles)) in slot:
                if len(slot) == 1: stats_data["one_correct_role"] += 1
                else: stats_data["several_roles_ok"] += 1
            elif len(slot) >= 1:
                if len(slot) == 1: stats_data["one_bad_role"] += 1
                else: stats_data["several_roles_bad"] += 1
                    
        if debug and set() in distrib:
            log_debug_data(frame, converted_frame, matcher, distrib)

def stats_precision_cover(good_fm, bad_fm, resolved_fm, identified, is_fm):
    good = stats_data["one_correct_role"]
    bad = stats_data["one_bad_role"]
    resolved = stats_data["one_role"]
    not_resolved = stats_data["args_kept"] - (stats_data["one_role"] + stats_data["no_role"])
    good_model = stats_data["one_correct_role"] - good_fm
    bad_model = stats_data["one_bad_role"] - bad_fm
    resolved_model = stats_data["one_role"] - resolved_fm

    precision_all = good / (good + bad)
    cover_all = resolved / identified
    if is_fm:
        precision, cover = precision_all, cover_all
    else:
        precision = good_model / (good_model + bad_model)
        cover = resolved_model / (identified - resolved_fm)
        
    return precision, cover, precision_all, cover_all
    
def stats_ambiguous_roles(frame, num_args, role_matcher, verbnet_classes, filename):
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

                log_ambiguous_role_conversion(filename, frame, arg,
                    role_matcher, verbnet_classes)
                
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
        except RoleMatchingError:
            pass

