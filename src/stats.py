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
    "arg_not_extracted_not_verbnet": 0,


    # Evaluated frames identification.
    "frames_evaluated": 0,
    "no_class": 0,
    "one_class__correct": 0,  # only one class possible, the good one
    "one_class": 0,
    "multiple_classes__correct": 0,  # multiple class possible, good one inside
    "multiple_classes": 0,
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
    print()

    total_classes = s['no_class'] + s['one_class'] + s['multiple_classes']
    assert total_classes == s['frames_evaluated']
    frame_identification_precision = s["one_class__correct"] / s["one_class"]
    frame_identification_recall = s["one_class__correct"] / total_classes
    frame_identification_f1 = hmean(frame_identification_precision, frame_identification_recall)

    print("Frame identification              : {:.1%} precision, {:.1%} recall, {:1.1%} F1".format(frame_identification_precision, frame_identification_recall, frame_identification_f1))
    print("       when multiple possibilities, {:.1%} precision".format(s["multiple_classes__correct"]/s["multiple_classes"]))
    print("Among evaluated: no frame {:.1%}, one frame {:.1%}, multiple frames {:.1%}".format(s['no_class'] / total_classes, s['one_class'] / total_classes, s['multiple_classes'] / total_classes))
    print()

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

    evaluated_roles = s['no_roles_evaluated'] + unique_role_evaluated + several_roles_evaluated
    print("Among evaluated: no match {:.1%} one role {:.1%} multiple roles {:.1%}".format(
        s['no_roles_evaluated'] / evaluated_roles,
        unique_role_evaluated / evaluated_roles,
        several_roles_evaluated / evaluated_roles))
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

def vnclass_to_normalized_name(vnclass):
    """A VerbNet class can have various names, depending on its position in the
    hierarchy, but not only. It's not easy to know weather a given identifier
    (eg. 72-1) is a root VerbNet class or not."""
    root_classes = ["77", "51.7", "95", "96", "26.9", "31.2", "65", "93",
            "37.9", "64", "22.2", "31.1", "38", "31.4", "48.1.1", "29.1",
            "34.1", "50", "52", "10.2", "97.1", "36.4", "109.1", "58.2",
            "55.1", "41.3.3", "45.2", "13.7", "54.5", "49", "40.6", "41.2.2",
            "45.1", "40.1.2", "11.3", "26.1", "47.5.3", "18.4", "9.9", "45.6",
            "28", "29.8", "88.1", "11.4", "21.2", "40.8.4", "29.2", "51.6",
            "10.6", "39.2", "37.6", "29.10", "10.3", "22.5", "9.6", "24",
            "37.8", "55.2", "87.2", "16", "37.10", "92", "98", "29.5", "29.9",
            "71", "66", "47.8", "55.3", "13.2", "26.6.2", "45.3", "73", "83",
            "86.1", "36.1", "54.2", "40.3.2", "26.4", "40.3.3", "21.1", "10.8",
            "29.4", "79", "97.2", "85", "44", "39.4", "23.4", "39.5", "48.2",
            "23.3", "84", "41.1.1", "41.3.2", "11.5", "29.3", "39.1", "88.2",
            "63", "27", "99", "45.5", "47.2", "13.4.2", "51.1", "55.5", "34.2",
            "90", "13.6", "40.1.3", "47.1", "39.7", "35.6", "9.8", "10.10",
            "54.3", "40.5", "41.2.1", "87.1", "67", "59", "80", "13.4.1",
            "9.3", "13.3", "13.5.1", "13.1", "39.3", "39.6", "41.1.2", "26.2",
            "72", "47.5.2", "40.1.1", "13.5.3", "18.1", "15.1", "35.1",
            "40.8.3", "25.3", "25.1", "78", "37.1.2", "37.4", "37.1.3", "35.4",
            "107", "33", "15.2", "26.5", "14", "51.2", "37.11", "43.1", "76",
            "53.1", "46", "32.2", "37.3", "36.2", "31.3", "29.6", "91", "47.7",
            "36.3", "10.9", "22.1", "47.3", "108", "42.1", "75", "51.4.2",
            "40.2", "13.5.2", "48.3", "60", "29.7", "45.4", "37.12", "100",
            "40.8.1", "101", "68", "30.3", "17.2", "26.7", "10.7", "9.10",
            "42.2", "19", "9.5", "26.3", "54.4", "37.13", "102", "12", "9.1",
            "9.4", "9.2", "51.8", "48.1.2", "69", "54.1", "26.8", "86.2", "70",
            "45.7", "10.1", "103", "10.11", "94", "51.3.1", "35.5", "51.3.2",
            "53.2", "37.7", "25.2", "35.2", "30.1", "109", "11.1", "23.1",
            "89", "22.3", "30.2", "41.3.1", "11.2", "43.3", "40.4", "43.2",
            "47.4", "18.3", "47.6", "104", "23.2", "9.7", "35.3", "10.5",
            "30.4", "55.4", "42.3", "43.4", "74", "40.7", "81", "55.6",
            "47.5.1", "18.2", "37.5", "22.4", "37.2", "17.1", "40.8.2", "20",
            "25.4", "37.1.1", "61", "26.6.1", "58.1", "105", "51.4.1", "106",
            "51.5", "32.1", "57", "56", "40.3.1", "10.4.2", "10.4.1", "62",
            "82"]
    vnclass_number = '-'.join(vnclass.split('-')[1:])
    for possible_root in root_classes:
        if vnclass_number.startswith(possible_root):
            return possible_root

    raise Exception('Impossible VerbNet class {}'.format(vnclass))


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

        stats_data['frames_evaluated'] += 1
        if not found_vn_frame.best_classes:
            stats_data['no_class'] += 1
        elif len(found_vn_frame.best_classes) == 1:
            stats_data['one_class'] += 1
            if vnclass_to_normalized_name(next(iter(found_vn_frame.best_classes))) in role_matcher.framenetframe_to_verbnetclasses[gold_fn_frame.frame_name]:
                stats_data['one_class__correct'] += 1
        else:
            stats_data['multiple_classes'] += 1
            if set(role_matcher.framenetframe_to_verbnetclasses[gold_fn_frame.frame_name]) & {vnclass_to_normalized_name(c) for c in found_vn_frame.best_classes}:
                stats_data['multiple_classes__correct'] += 1

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
