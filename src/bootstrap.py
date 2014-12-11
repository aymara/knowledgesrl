#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import log
import headwordextractor


def bootstrap_algorithm(vn_frames, probability_model, verbnet_classes):
    # See Swier and Stevenson, Unsupervised Semantic Role Labelling, 2004, 5.4
    # for information about the parameters' values
    log_ratio = 8
    log_ratio_step = 0.5
    min_evidence = [1, 1, 10]
    # [1, 3, 10] -> [17, 65, 2076]
    # [3, 5, 10] -> [17, 65, 2076]

    total = [0, 0, 0]
    while log_ratio >= 1:
        # Update probability model with resolved slots (only one role)
        for frame_occurrence in vn_frames:
            for slot_position, role_set in enumerate(frame_occurrence.roles):
                if len(role_set) != 1:
                    continue

                headword = headwordextractor.headword(
                    frame_occurrence.args[slot_position],
                    frame_occurrence.tree)['content_headword'][1]
                probability_model.add_data_bootstrap(
                    next(iter(role_set)),
                    frame_occurrence.predicate,
                    verbnet_classes[frame_occurrence.predicate],
                    frame_occurrence.slot_types[slot_position],
                    frame_occurrence.slot_preps[slot_position],
                    headword,
                    headwordextractor.get_class(headword)
                )

        # According to the article, there is no longer a min evidence threshold
        # when log_ratio reaches 1
        if log_ratio == 1:
            min_evidence = [1, 1, 1]

        for frame_occurrence in vn_frames:
            for slot_position in range(frame_occurrence.num_slots):
                role_set = frame_occurrence.roles[slot_position]
                if len(role_set) <= 1:
                    continue

                headword = headwordextractor.headword(
                    frame_occurrence.args[slot_position],
                    frame_occurrence.tree)['content_headword'][1]
                role = None
                for backoff_level in [0, 1, 2]:
                    role1, role2, ratio = probability_model.best_roles_bootstrap(
                        role_set,
                        frame_occurrence.predicate,
                        # Choosing the first class here is arbitrary
                        verbnet_classes[frame_occurrence.predicate],
                        frame_occurrence.slot_types[slot_position],
                        frame_occurrence.slot_preps[slot_position],
                        headword,
                        headwordextractor.get_class(headword),
                        backoff_level,
                        min_evidence[backoff_level]
                    )

                    if (role1 is not None and
                        ((role2 is not None and log(ratio) > log_ratio) or
                        log_ratio <= 1)):

                        role = role1
                        total[backoff_level] += 1
                        break

                if role is not None:
                    frame_occurrence.restrict_slot_to_role(slot_position, role)

        log_ratio -= log_ratio_step
