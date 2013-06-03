#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
from rolematcher import RoleMatchingError
from errorslog import *

stats_data = {
    "files":0,
    "frames":0, 
    "frames_with_predicate_in_verbnet":0,
    "frames_mapped":0, 
    "args":0, 
    "args_kept":0,
    "one_role":0, 
    "no_role":0,
    "one_correct_role":0, 
    "one_bad_role":0,
    "several_roles_ok":0, 
    "several_roles_bad":0,
    "ambiguous_mapping":0,
    "impossible_mapping":0,
    "frame_extracted_good":0,
    "frame_extracted_bad":0,
    "frame_not_extracted":0,
    "arg_extracted_good":0,
    "arg_extracted_partial":0,
    "arg_extracted_bad":0,
    "arg_not_extracted":0
}

ambiguous_mapping = {
    # Stats of ambiguous mapping when ignoring the FN frame given by the annotations
    "verbs":[], "args_total":0, "args":0,
    # Stats of ambiguous mapping remaining despite the FN frame given by the annotations
    "verbs_with_frame":[], "args_total_with_frame":0, "args_with_frame":0
}
  
def display_stats(gold_args):
    s = stats_data
    several_roles = s["args_kept"] - (s["one_role"] + s["no_role"])
    unique_role_evaluated = s["one_correct_role"] + s["one_bad_role"]
    several_roles_evaluated = s["several_roles_ok"] + s["several_roles_bad"]
    
    if gold_args:
        print(
            "\n\nFiles: {} - annotated frames: {} - annotated args: {}\n"
            "Frames with predicate in VerbNet: {} frames ({} args)\n".format(
            s["files"], s["frames"], s["args"],
            s["frames_with_predicate_in_verbnet"],  s["args_kept"]
        ))
    else:
        print(
            "\n\nExtracted {} correct and {} incorrect (non-annotated) frames.\n"
            "Did not extract {} annotated frames.\n"
            "Extracted {} correct, {} partial-match and {} incorrect arguments.\n"
            "Did not extract {} annotated arguments.\n".format(
            s["frame_extracted_good"], s["frame_extracted_bad"],
            s["frame_not_extracted"],
            s["arg_extracted_good"], s["arg_extracted_partial"],
            s["arg_extracted_bad"],
            s["arg_not_extracted"]
        ))
        
    print(
        "Frames mapped: {} frames\n"
        
        "\nFrame matching:\n"
        "{} args not matched\n"
        "{} args with exactly one possible role\n"
        "\t{:.2%} correct out of {} evaluated\n"
        "{} args with multiple possible roles\n"
        "\t{:.2%} correct (correct role is in role list) out of {} evaluated\n"
        "\n{} cases where we cannot verify the labeling:\n"
        "\t{} because no role mapping was found\n"
        "\t{} because several VerbNet roles are mapped to the FrameNet role\n"
        "\nOverall: {:.2%} precision, {:.2%} accuracy\n"
        "\n".format(
            s["frames_mapped"],

            s["no_role"],
            s["one_role"],
            s["one_correct_role"] / max(unique_role_evaluated, 1), unique_role_evaluated,
            several_roles,
            s["several_roles_ok"] / max(several_roles_evaluated, 1), several_roles_evaluated,
            s["one_role"] + several_roles - (unique_role_evaluated + several_roles_evaluated),

            s["impossible_mapping"], s["ambiguous_mapping"],

            s["one_correct_role"] / max(unique_role_evaluated, 1),
            s["one_correct_role"] / max(unique_role_evaluated + several_roles_evaluated + s["no_role"], 1))
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
                    
def stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes):
    stats_data["roles_conversion_impossible"] = 0
    stats_data["roles_conversion_ambiguous"] = 0
    stats_data["one_correct_role"] = 0
    stats_data["several_roles_ok"] = 0
    stats_data["one_bad_role"] = 0
    stats_data["several_roles_bad"] = 0
    stats_data["one_role"] = 0
    stats_data["no_role"] = 0
    stats_data["impossible_mapping"] = 0
    stats_data["ambiguous_mapping"] = 0
    
    for gold_fn_frame, found_vn_frame in zip(annotated_frames, vn_frames):    
        for i, slot in enumerate(found_vn_frame.roles):
            if len(slot) == 0:
                stats_data["no_role"] += 1
            elif len(slot) == 1:
                stats_data["one_role"] += 1

            try:
                possible_roles = role_matcher.possible_vn_roles(
                    gold_fn_frame.args[i].role,
                    fn_frame=gold_fn_frame.frame_name,
                    vn_classes=verbnet_classes[gold_fn_frame.predicate.lemma]
                    )
            except RoleMatchingError as e:
                stats_data["impossible_mapping"] += 1
                continue
  
            if len(possible_roles) > 1:
                stats_data["ambiguous_mapping"] += 1
            elif next(iter(possible_roles)) in slot:
                if len(slot) == 1: stats_data["one_correct_role"] += 1
                else: stats_data["several_roles_ok"] += 1
            elif len(slot) >= 1:
                if len(slot) == 1: stats_data["one_bad_role"] += 1
                else: stats_data["several_roles_bad"] += 1

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
    
def stats_ambiguous_roles(frame, num_args, role_matcher, verbnet_classes):
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

                log_ambiguous_role_conversion(frame, arg,
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

