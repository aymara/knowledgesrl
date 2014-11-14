#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter

from rolematcher import RoleMatchingError
from errorslog import log_ambiguous_role_conversion
import options


# TODO separate computed values from measured values
stats_data = {
    # Total number of files in the corpus
    "files":0,
    # Number of annotated verbal frame instances in the corpus
    "frames":0,
    # Number of annotated verbal frame instances which have a predicate in VerbNet
    "frames_with_predicate_in_verbnet":0,
    # Number of frame instances for which frame-matching is possible (at least one slot)
    "frames_mapped":0,
    # Number of args belonging to an annotated verbal frame in the corpus
    "args":0,
    # Number of instanciated args
    "args_instanciated":0,
    # Number of instanciated args belonging to a frame wich has a predicate in VerbNet
    "args_kept":0,
    # Number of annotated, instanciated args with a role mapping ok
    "args_annotated_mapping_ok":0,
    
    # Slots states (applies to extracted slots if no gold args)
    
    # No role attributed
    "no_role":0,
    # No role attributed, annotated
    "no_role_annotated":0,
    # One role attributed
    "one_role":0,
    # One role attributed, annotated
    "one_role_annotated":0,
    # One role attributed, annotated, role mapping possible, correct role
    "one_correct_role":0,
    # One role attributed, annotated, role mapping possible, incorrect role
    "one_bad_role":0,
    # Several role attributed, annotated
    "several_roles_annotated":0,
    # Several roles attributed, annotated, role mapping ok, correct role in the list
    "several_roles_ok":0,
    # Several roles attributed, annotated, role mapping ok, correct role not in the list
    "several_roles_bad":0,
    # Role mapping returned several possible VerbNet roles
    "ambiguous_mapping":0,
    # Role mapping returned no possible VerbNet roles
    "impossible_mapping":0,
    
    # Total number of roles = sum of number of possible roles for each slot
    "attributed_roles":0,
    # Idem only on slots where role mapping is ok
    "attributed_roles_mapping_ok":0,
    
    # Frame instances and argument extraction from raw text
    
    # Number of correct extracted frame instances
    "frame_extracted_good":0,
    # Number of incorrect (no annotations) extracted frame instances
    "frame_extracted_bad":0,
    # Number of non-extracted annotated frame instances
    "frame_not_extracted":0,
    # Number of non-extracted annotated frame instances which do not have a predicate in VerbNet
    "frame_not_extracted_not_verbnet":0,
    # Number of correct extracted arguments
    "arg_extracted_good":0,
    # Number of partial-match in extracted arguments
    "arg_extracted_partial":0,
    # Number of incorrect (no annotation) extracted arguments
    "arg_extracted_bad":0,
    # Number of non-extracted annotated arguments
    "arg_not_extracted":0,
    # Number of non-extracted annotated args which do not have a predicate in VerbNet
    "arg_not_extracted_not_verbnet":0
}

ambiguous_mapping = {
    # Stats of ambiguous mapping when ignoring the FN frame given by the annotations
    "verbs":[], "args_total":0, "args":0,
    # Stats of ambiguous mapping remaining despite the FN frame given by the annotations
    "verbs_with_frame":[], "args_total_with_frame":0, "args_with_frame":0
}

annotated_frames_stats = []

def hmean(x, y):
    if x < 0 or y < 0:
        raise ValueError("Harmonic mean does not apply to negative parameters.")
    if x == 0 and y == 0:
        return 0
    return (2 * x * y) / (x + y)

def display_stats(argument_identification):
    s = stats_data
    several_roles = s["args_kept"] - (s["one_role"] + s["no_role"])
    unique_role_evaluated = s["one_correct_role"] + s["one_bad_role"]
    several_roles_evaluated = s["several_roles_ok"] + s["several_roles_bad"]
    
    good_slots = s["one_correct_role"] + s["several_roles_ok"]

    precision = good_slots / max(s["attributed_roles_mapping_ok"], 1)
    recall = good_slots / max(s["args_annotated_mapping_ok"], 1)

    accuracy = s["one_correct_role"] / max(s["args_annotated_mapping_ok"], 1)
    
    extrapolated_one_good = (s["one_correct_role"] *
        s["one_role_annotated"] / max(unique_role_evaluated, 1))
    extrapolated_good_slots = (extrapolated_one_good +
        s["several_roles_ok"] * s["several_roles_annotated"] /
        max(several_roles_evaluated, 1))
    
    extrapolated_precision = extrapolated_good_slots / max(s["attributed_roles"], 1)
    extrapolated_recall = extrapolated_good_slots / max(s["args_instanciated"], 1)
    extrapolated_accuracy = extrapolated_one_good / max(s["args_instanciated"], 1)
    
    if argument_identification:
        # Give frame identification scores and argument identification scores

        frame_identification_recall = s["frame_extracted_good"] / (
            s["frame_extracted_good"] + s["frame_not_extracted"])
        frame_identification_productivity = (
            (s["frame_extracted_good"] + s["frame_extracted_bad"]) /
            (s["frame_extracted_good"] + s["frame_not_extracted"]))
        print("Frame identification: Recall: {:.1%}, Productivity: {:.0%}".format(
            frame_identification_recall, frame_identification_productivity))

        argument_identification_precision = s["arg_extracted_good"] / (
            s["arg_extracted_good"] + s["arg_extracted_bad"])
        argument_identification_recall = s["arg_extracted_good"] / (
                s["arg_extracted_good"] + s["arg_not_extracted"])
        argument_identification_f1 = 2 * (
            (argument_identification_precision * argument_identification_recall) /
            (argument_identification_precision + argument_identification_recall))
        print("Argument identification: Precision: {:.1%}, Recall: {:.1%}, F1: {:.1%}".format(
            argument_identification_precision, argument_identification_recall,
            argument_identification_f1))

        print("Extracted {} partial-match arguments.".format(s["arg_extracted_partial"]))
    else:
        print(
            "\nFiles: {} - annotated frame instances: {} - annotated args: {}\n"
            "Frame instances with predicate in VerbNet: {} frame instances ({} args)\n".format(
            s["files"], s["frames"], s["args"],
            s["frames_with_predicate_in_verbnet"],  s["args_kept"]
        ))
        
    if options.use_training_set:
        print(
            "Frame instances mapped: {} frames\n"
            
            "\nFrame matching:\n"
            "{} args not matched ({} not annotated)\n"
            "{} args with exactly one possible role\n"
            "\t{:.2%} correct out of {} evaluated\n"
            "{} args with multiple possible roles\n"
            "\t{:.2%} correct (correct role is in role list) out of {} evaluated\n"
            "\n{} slots with at least one possible role where we cannot verify the labeling\n"
            "{} slots where no role mapping was found\n"
            "{} slots where several VerbNet roles are mapped to the FrameNet role\n"
            .format(
                s["frames_mapped"],

                s["no_role"], s["no_role"] - s["no_role_annotated"],
                s["one_role"],
                s["one_correct_role"] / max(unique_role_evaluated, 1), unique_role_evaluated,
                several_roles,
                s["several_roles_ok"] / max(several_roles_evaluated, 1), several_roles_evaluated,
                s["one_role"] + several_roles - (unique_role_evaluated + several_roles_evaluated),

                s["impossible_mapping"], s["ambiguous_mapping"])

        )

    print(
        "Overall extrapolation : {:.2%} precision, {:.2%} recall, {:.2%} F1, {:.2%} accuracy\n"
        "Overall when role mapping applies: {:.2%} F1, {:.2%} accuracy\n".format(
            extrapolated_precision, extrapolated_recall,
            hmean(extrapolated_precision, extrapolated_recall),
            extrapolated_accuracy,

            hmean(precision, recall), accuracy)
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

def reset_computed_stats():
    stats_data["one_correct_role"] = 0
    stats_data["several_roles_ok"] = 0
    stats_data["one_bad_role"] = 0
    stats_data["several_roles_bad"] = 0
    stats_data["one_role"] = 0
    stats_data["no_role"] = 0
    stats_data["no_role_annotated"] = 0
    stats_data["impossible_mapping"] = 0
    stats_data["ambiguous_mapping"] = 0
    stats_data["one_role_annotated"] = 0
    stats_data["several_roles_annotated"] = 0
    stats_data["attributed_roles"] = 0
    stats_data["attributed_roles_mapping_ok"] = 0
    annotated_frames_stats = []

def stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, argument_identification):
    # We first reset computed values to 0, eg. if we modified them before
    reset_computed_stats()

    # This variable is not handled here for non-gold args, because
    # annotated_frame contains only extracted frames at this point and
    # args_annotated_mapping_ok is related to gold annotated frames
    if not argument_identification:
        stats_data["args_annotated_mapping_ok"] = 0

    total_roles = 0
    
    for gold_fn_frame, found_vn_frame in zip(annotated_frames, vn_frames):
        annotated_frames_stats.append({'gold_fn_frame': gold_fn_frame, 'slots': []})
        # We don't know how to evaluate args that were extracted from a frame
        # that exist in the fulltext corpus but that lacks argument annotations
        if gold_fn_frame.frame_name != "" and not gold_fn_frame.arg_annotated:
            continue
        
        # Do not penalize arguments extracted from frames that do not exist
        # in the fulltext corpus
        if gold_fn_frame.frame_name == "":
            continue
        
        for i, slot in enumerate(found_vn_frame.roles):
            # Add number of possibles role for this slot (eg. the subject slot)
            stats_data["attributed_roles"] += len(slot)
            if len(slot) == 0:
                stats_data["no_role"] += 1
                if gold_fn_frame.args[i].annotated:
                    stats_data["no_role_annotated"] += 1
            elif len(slot) == 1:
                stats_data["one_role"] += 1
                if gold_fn_frame.args[i].annotated:
                    stats_data["one_role_annotated"] += 1
            elif gold_fn_frame.args[i].annotated:
                stats_data["several_roles_annotated"] += 1
            
            # Penalize slots extracted from frames that do not exist
            # or associated with arguments that are not annotated
            # when they have at least one possible roles
            if not gold_fn_frame.args[i].annotated:
                if len(slot) == 1:
                    stats_data["one_bad_role"] += 1
                elif len(slot) >= 1:
                    stats_data["several_roles_bad"] += 1
                stats_data["attributed_roles_mapping_ok"] += len(slot)
                continue

            try:
                possible_roles = role_matcher.possible_vn_roles(
                    gold_fn_frame.args[i].role,
                    fn_frame=gold_fn_frame.frame_name,
                    # TODO don't forget we need to specify the VN class?
                    # If the mapping is ambiguous, it could be our mistake here
                    vn_classes=verbnet_classes[gold_fn_frame.predicate.lemma]
                    )
            except RoleMatchingError:
                stats_data["impossible_mapping"] += 1
                continue
  
            if len(possible_roles) > 1:
                stats_data["ambiguous_mapping"] += 1
                continue

            stats_data["attributed_roles_mapping_ok"] += len(slot)
            
            if not argument_identification:
                stats_data["args_annotated_mapping_ok"] += 1

            annotated_frames_stats[-1]['slots'].append({'text': gold_fn_frame.args[i].text, 'found_roles': slot, 'wanted_roles': possible_roles})
            
            if next(iter(possible_roles)) in slot:
                if len(slot) == 1:
                    stats_data["one_correct_role"] += 1
                else:
                    stats_data["several_roles_ok"] += 1
            elif len(slot) >= 1:
                if len(slot) == 1:
                    stats_data["one_bad_role"] += 1
                else:
                    stats_data["several_roles_bad"] += 1
    
def stats_precision_cover(good_fm, bad_fm, resolved_fm, identified, is_fm):
    good = stats_data["one_correct_role"]
    bad = stats_data["one_bad_role"]
    resolved = stats_data["one_role"]
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

