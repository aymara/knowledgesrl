#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from framestructure import *
from collections import defaultdict
from functools import reduce

NO_PREP = "no_prep_magic_value"

def multi_get(d, l):
    """Traverses multiple levels of a dictionary to get a key or None"""
    return reduce(lambda d,k: d.get(k) if d else None, l, d) if d else None


class ProbabilityModel:
    def __init__(self):
        self.data_default = {
            VerbnetFrame.slot_types["subject"]:"Agent",
            VerbnetFrame.slot_types["object"]:"Theme",
            VerbnetFrame.slot_types["indirect_object"]:"Recipient",
            VerbnetFrame.slot_types["prep_object"]:"Location"
        }
        self.data_slot_class = defaultdict(lambda: defaultdict(int))
        self.data_slot = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.data_predicate_slot = defaultdict(lambda: defaultdict(lambda:
                defaultdict(lambda: defaultdict(int))))

    def add_data(self, slot_class, role, prep, predicate):
        self.data_slot_class[slot_class][role] += 1
        
        if slot_class == VerbnetFrame.slot_types["prep_object"]:
            self.data_slot[slot_class][prep][role] += 1
            self.data_predicate_slot[predicate][slot_class][prep][role] += 1
        else:
            self.data_slot[slot_class][NO_PREP][role] += 1
            self.data_predicate_slot[predicate][slot_class][NO_PREP][role] += 1
        
    def best_role(self, role_set, slot_class, prep, predicate, model):
        if slot_class != VerbnetFrame.slot_types["prep_object"]:
            final_prep = NO_PREP
        else:
            final_prep = prep

        if model == "default":
            return self.data_default[slot_class]
        elif model == "slot_class":
            data = self.data_slot_class.get(slot_class)
        elif model == "slot":
            data = multi_get(self.data_slot, [slot_class, final_prep])
        elif model == "predicate_slot":
            data = multi_get(self.data_predicate_slot, [predicate, slot_class, final_prep])
        else:
            raise Exception("Unknown model {}".format(model))
                
        if data:
            possible_roles = set(data.keys()) & role_set
            if possible_roles:
                return max(possible_roles, key = lambda role: data[role])

        return None

class ProbabilityModelTest(unittest.TestCase):
     def test_1(self):
        model = ProbabilityModel()
        
        # No data : best_role should always return None
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", None, "sleep", "slot_class"), None)
            
        model.add_data("SUBJ", "Theme", "for", "eat")
        
        # Simple test with only one entry in the data
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", None, "sleep", "slot_class"), "Theme")
            
        model.add_data("SUBJ", "Agent", "against", "drink")
        model.add_data("SUBJ", "Agent", "against", "drink")
        model.add_data("SUBJ", "Agent", "against", "drink")
        
        # We added more entry for Agent, which should change the result
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", "without", "sleep", "slot_class"), "Agent")
            
        # Unknown roles should return None
        self.assertEqual(model.best_role(
            set(["Patient", "Location"]), "SUBJ", None, "sleep", "slot_class"), None)
            
        model.add_data("PPOBJ", "Agent", "with", "eat")
        model.add_data("PPOBJ", "Agent", "with", "eat")
        model.add_data("PPOBJ", "Agent", "with", "eat")
        model.add_data("PPOBJ", "Location", "in", "eat")
        model.add_data("PPOBJ", "Location", "to", "eat")
        model.add_data("PPOBJ", "Destination", "to", "eat")
        model.add_data("PPOBJ", "Destination", "to", "eat")
        
        # The 'slot' model should return None when it never saw the preposition
        self.assertEqual(model.best_role(
            set(["Agent", "Location"]), "PPOBJ", "without", "sleep", "slot"), None)
            
        # The 'slot_class' model should ignore the preposition
        self.assertEqual(model.best_role(
            set(["Agent", "Location"]), "PPOBJ", "to", "sleep", "slot_class"), "Agent")
        
        # The 'slot' model should see that 'Location' is more frequent with 'to'
        self.assertEqual(model.best_role(
            set(["Agent", "Location"]), "PPOBJ", "to", "sleep", "slot"), "Location")
        
        # The model should ignore the preposition, since this is a 'SUBJ' slot 
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", "for", "sleep", "slot"), "Agent")
            
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", "for", "eat", "predicate_slot"), "Theme")
     
if __name__ == "__main__":
    unittest.main()
