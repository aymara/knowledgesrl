#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import probabilitymodel
from functools import reduce

def bootstrap_algorithm(frames, probability_model, hw_extractor, verbnet_classes):
    # See Swier and Stevenson, Unsupervised Semantic Role Labelling, 2004, 5.4
    # for information about the parameters' values
    log_ratio = 8
    log_ratio_step = 0.5
    min_evidence = [3, 5, 10]
    
    
    # Transform the frame list (with the slots in frame.roles) into
    # a list of (frame, role_set, frame_position, slot_position)
    grouped_roles = [[(x, y, i, j) for j, y in enumerate(x.roles)] for i, x in enumerate(frames)]
    slots = reduce(lambda a,b:a+b, grouped_roles)
    
    while log_ratio > 0:
        for frame, role_set, i, j in slots:
            if len(role_set) == 1:
                probability_model.add_data_bootstrap(
                    next(iter(role_set)),
                    frame.predicate,
                    verbnet_classes[frame.predicate][0],
                    frame.slot_types[j],
                    frame.slot_preps[j],
                    frame.headwords[j],
                    hw_extractor.get_class(frame.headwords[j])
                )
        
        # Remove resolved and empty slots
        slots = list(filter(lambda x: len(x[1]) > 1, slots))
 
        if log_ratio == 1: min_evidence = [1, 1, 1]
        
        for frame, role_set, i, j in slots:
            if len(role_set) <= 1: continue
            
            role = None
            for backoff_level in [0, 1, 2]:
                role1, role2, ratio = probability_model.best_roles_bootstrap(
                    role_set,
                    frame.predicate,
                    verbnet_classes[frame.predicate][0], #Randomly choose the first class
                    frame.slot_types[j],
                    frame.slot_preps[j],
                    frame.headwords[j],
                    hw_extractor.get_class(frame.headwords[j]),
                    backoff_level,
                    min_evidence[backoff_level]
                )

                if (role1 != None and 
                    ((role2 != None and ratio > log_ratio) or
                    log_ratio <= 1)
                ):
                    role = role1
                    break

            if role != None:
                frames[i].roles[j] = set([role])
        log_ratio -= log_ratio_step

