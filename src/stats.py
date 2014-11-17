#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter

from rolematcher import RoleMatchingError
from errorslog import log_ambiguous_role_conversion


# TODO separate computed values from measured values
stats_data = {
    # Total number of files in the corpus
    "files": 0,
    # Number of annotated verbal frame instances in the corpus
    "frames": 0,
    # Number of annotated verbal frame instances which have a predicate in VerbNet
    "frames_with_predicate_in_verbnet": 0,
    # Number of frame instances for which frame-matching is possible (at least one slot)
    "frames_mapped": 0,
    # Number of args belonging to an annotated verbal frame in the corpus
    "args": 0,
    # Number of instanciated args
    "args_instanciated": 0,
    # Number of instanciated args belonging to a frame wich has a predicate in VerbNet
    "args_kept": 0,
    # Number of annotated, instanciated args with a role mapping ok
    "args_annotated_mapping_ok": 0,

    # Slots states (applies to extracted slots if no gold args)

    # No role attributed
    "no_role": 0,
    # No role attributed, annotated
    "no_role_annotated": 0,
    # One role attributed
    "one_role": 0,
    # One role attributed, annotated
    "one_role_annotated": 0,
    # One role attributed, annotated, role mapping possible, correct role
    "one_correct_role": 0,
    # One role attributed, annotated, role mapping possible, incorrect role
    "one_bad_role": 0,
    # Several role attributed, annotated
    "several_roles_annotated": 0,
    # Several roles attributed, annotated, role mapping ok, correct role in the list
    "several_roles_ok": 0,
    # Several roles attributed, annotated, role mapping ok, correct role not in the list
    "several_roles_bad": 0,
    # All cases where a mapping was possible but no role mapping anyway
    "no_roles_evaluated":  0,
    # Role mapping returned several possible VerbNet roles
    "ambiguous_mapping": 0,
    # Role mapping returned no possible VerbNet roles
    "impossible_mapping": 0,

    # Total number of roles = sum of number of possible roles for each slot
    "attributed_roles": 0,
    # Idem only on slots where role mapping is ok
    "attributed_roles_mapping_ok": 0,

    # Frame instances and argument extraction from raw text

    # Number of correct extracted frame instances
    "frame_extracted_good": 0,
    # Number of incorrect (no annotations) extracted frame instances
    "frame_extracted_bad": 0,
    # Number of non-extracted annotated frame instances
    "frame_not_extracted": 0,
    # Number of non-extracted annotated frame instances which do not have a predicate in VerbNet
    "frame_not_extracted_not_verbnet": 0,
    # Number of correct extracted arguments
    "arg_extracted_good": 0,
    # Number of incorrect (no annotation) extracted arguments
    "arg_extracted_bad": 0,
    # Number of non-extracted annotated arguments
    "arg_not_extracted": 0,
    # Number of non-extracted annotated args which do not have a predicate in VerbNet
    "arg_not_extracted_not_verbnet": 0
}

ambiguous_mapping = {
    # Stats of ambiguous mapping when ignoring the FN frame given by the annotations
    "verbs": [], "args_total": 0, "args": 0,
    # Stats of ambiguous mapping remaining despite the FN frame given by the annotations
    "verbs_with_frame": [], "args_total_with_frame": 0, "args_with_frame": 0
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
    unique_role_evaluated = s["one_correct_role"] + s["one_bad_role"]
    several_roles_evaluated = s["several_roles_ok"] + s["several_roles_bad"]

    if argument_identification:
        # Predicate identification
        predicate_identification_recall = s["frame_extracted_good"] / (
            s["frame_extracted_good"] + s["frame_not_extracted"])
        # The productivity is the ratio between the number of FN predicates and
        # the number of extracted predicates. If productivity is 3x, we
        # produced 3 times as much predicates as FrameNet manual annotation
        # did. There are two reasons for producing so much predicates:
        #  * we're using VerbNet, which includes more senses than FrameNet
        #  * we don't disambiguate, so even if it's not the correct sense, we
        #  assign it to a "frame" (but there are less holes in VerbNet than in
        #  FrameNet, so that's less of an issue.
        predicate_identification_productivity = (
            (s["frame_extracted_good"] + s["frame_extracted_bad"]) /
            (s["frame_extracted_good"] + s["frame_not_extracted"]))
        print("Predicate identification ({:.2f}x):                  {:.1%} recall".format(
            predicate_identification_productivity, predicate_identification_recall))

        # Argument identification
        argument_identification_precision = s["arg_extracted_good"] / (
            s["arg_extracted_good"] + s["arg_extracted_bad"])
        argument_identification_recall = s["arg_extracted_good"] / (
            s["arg_extracted_good"] + s["arg_not_extracted"])
        argument_identification_f1 = hmean(
            argument_identification_precision,
            argument_identification_recall)
        # * If I'm not mistaken, this only concerns arguments for frames that
        # are in FrameNet: any "surproduction" is not caused by producing too
        # much frames.
        argument_identification_productivity = (s["args"]) / s["args_kept"]
        print("Argument identification (*{:.2f}x): {:.1%} precision, {:.1%} recall, {:.1%} F1".format(
            argument_identification_productivity,
            argument_identification_precision, argument_identification_recall,
            argument_identification_f1))
    else:
        print(
            "{} files, {} gold frame instances, {} gold args\n"
            "{} frame instances with predicate in VerbNet, that is {} args".format(
            s["files"], s["frames"], s["args"],
            s["frames_with_predicate_in_verbnet"], s["args_kept"]
        ))

    role_matching_precision = s["one_correct_role"] / unique_role_evaluated
    role_matching_recall = (s["one_correct_role"] / (unique_role_evaluated + several_roles_evaluated + s["no_roles_evaluated"]))
    role_matching_f1 = hmean(role_matching_precision, role_matching_recall)

    # * the reason this is low in argument identification compared to frameid 
    # and argid is that we only evaluate against FrameNet frames, so it can
    # only be < 1. I believe the drop from > 3 to close to 0 is due to VerbNet:
    # every argument that does not fit a VerbNet frame is not assigned to a
    # role. Another reason is that whenever multiple roles are possibles, that
    # doesn't count towards productivity. Even if productivity would stay under
    # 0.1, counting thoses cases would currently make productivity go from 0.12 to 0.25.
    role_matching_productivity = s['one_role'] / s['args_instanciated']
    print("Role matching           (*{:.2f}x): {:.1%} precision, {:.1%} recall, {:.1%} F1".format(
        role_matching_productivity,
        role_matching_precision, role_matching_recall,
        role_matching_f1))
    print("     when multiple possibilities, {:.1%} precision".format(s["several_roles_ok"] / max(several_roles_evaluated, 1)))
    print()

    print("Mapped {:.1%} of {} frames, uniquely mapped {:.1%} of {} arguments".format(
        s["frames_mapped"]/s["frames"], s["frames"],
        s["args_annotated_mapping_ok"]/s["args_instanciated"], s["args_instanciated"]))

    good_slots = s["one_correct_role"] + s["several_roles_ok"]
    precision = good_slots / max(s["attributed_roles_mapping_ok"], 1)
    recall = good_slots / max(s["args_annotated_mapping_ok"], 1)

    accuracy = s["one_correct_role"] / max(s["args_annotated_mapping_ok"], 1)

    extrapolated_one_good = (
        s["one_correct_role"] * s["one_role_annotated"] /
        max(unique_role_evaluated, 1))
    extrapolated_good_slots = (
        extrapolated_one_good + s["several_roles_ok"] * s["several_roles_annotated"] /
        max(several_roles_evaluated, 1))

    extrapolated_precision = extrapolated_good_slots / max(s["attributed_roles"], 1)
    extrapolated_recall = extrapolated_good_slots / max(s["args_instanciated"], 1)
    extrapolated_accuracy = extrapolated_one_good / max(s["args_instanciated"], 1)

    print(
        "Overall when role mapping applies: {:.2%} F1, {:.2%} accuracy\n"
        "Overall extrapolation:             {:.2%} precision, {:.2%} recall, {:.2%} F1, {:.2%} accuracy".format(
            hmean(precision, recall), accuracy,

            extrapolated_precision, extrapolated_recall,
            hmean(extrapolated_precision, extrapolated_recall),
            extrapolated_accuracy))

    # Search for * in this function
    print("*: see comments in stats.py")


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


def stats_quality(annotated_frames, vn_frames, role_matcher, verbnet_classes, argument_identification):
    # This variable is not handled here for non-gold args, because
    # annotated_frame contains only extracted frames at this point and
    # args_annotated_mapping_ok is related to gold annotated frames
    if not argument_identification:
        stats_data["args_annotated_mapping_ok"] = 0

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
            else:
                stats_data["no_roles_evaluated"] += 1


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
        if not arg.instanciated:
            continue
        try:
            if len(role_matcher.possible_vn_roles(
                arg.role, vn_classes=verbnet_classes[frame.predicate.lemma]
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
                    fn_frame=frame.frame_name,
                    vn_classes=verbnet_classes[frame.predicate.lemma]
                )) > 1:
                    if not found_ambiguous_arg_2:
                        found_ambiguous_arg_2 = True
                        ambiguous_mapping["verbs_with_frame"].append(frame.predicate.lemma)
                        ambiguous_mapping["args_total_with_frame"] += num_args
                    ambiguous_mapping["args_with_frame"] += 1
        except RoleMatchingError:
            pass
