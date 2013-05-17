#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from framestructure import *

class ProbabilityModel:
    def __init__(self):
        self.data_slot_class = {}
        self.data_slot = {}

    def add_data(self, slot_class, role, prep):
        if not slot_class in self.data_slot_class:
            self.data_slot_class[slot_class] = {}
        if not role in self.data_slot_class[slot_class]:
            self.data_slot_class[slot_class][role] = 0
        self.data_slot_class[slot_class][role] += 1
        
        if not slot_class in self.data_slot:
            self.data_slot[slot_class] = {}
        if slot_class == VerbnetFrame.slot_types["prep_object"]:
            if not prep in self.data_slot[slot_class]:
                self.data_slot[slot_class][prep] = {}
            role_dict = self.data_slot[slot_class][prep]
        else:
            role_dict = self.data_slot[slot_class]
            
        if not role in role_dict:
            role_dict[role] = 0
        role_dict[role] += 1
        
    def best_role(self, role_set, slot_class, prep, model):
        if model == "slot_class":
            if not slot_class in self.data_slot_class: return None
            data = self.data_slot_class[slot_class]
        elif model == "slot":
            if not slot_class in self.data_slot: return None
            if slot_class == VerbnetFrame.slot_types["prep_object"]:
                if not prep in self.data_slot[slot_class]: return None
                data = self.data_slot[slot_class][prep]
            else:
                data = self.data_slot[slot_class]
        else:
            return None
                
        possible_roles = set(data.keys()).intersection(role_set)

        best_value = 0
        best_role = None
        for role in possible_roles:
            if data[role] > best_value:
                best_value = data[role]
                best_role = role
                
        return best_role

class ProbabilityModelTest(unittest.TestCase):
     def test_1(self):
        model = ProbabilityModel()
        
        # No data : best_role should always return None
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", None, "slot_class"), None)
            
        model.add_data("SUBJ", "Theme", "for")
        
        # Simple test with only one entry in the data
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", None, "slot_class"), "Theme")
            
        model.add_data("SUBJ", "Agent", "against")
        model.add_data("SUBJ", "Agent", "against")
        model.add_data("SUBJ", "Agent", "against")
        
        # We added more entry for Agent, which should change the result
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", "without", "slot_class"), "Agent")
            
        # Unknown roles should return None
        self.assertEqual(model.best_role(
            set(["Patient", "Location"]), "SUBJ", None, "slot_class"), None)
            
        model.add_data("PPOBJ", "Agent", "with")
        model.add_data("PPOBJ", "Agent", "with")
        model.add_data("PPOBJ", "Agent", "with")
        model.add_data("PPOBJ", "Location", "in")
        model.add_data("PPOBJ", "Location", "to")
        model.add_data("PPOBJ", "Destination", "to")
        model.add_data("PPOBJ", "Destination", "to")
        
        # The 'slot' model should return None when it never saw the preposition
        self.assertEqual(model.best_role(
            set(["Agent", "Location"]), "PPOBJ", "without", "slot"), None)
            
        # The 'slot_class' model should ignore the preposition
        self.assertEqual(model.best_role(
            set(["Agent", "Location"]), "PPOBJ", "to", "slot_class"), "Agent")
        
        # The 'slot' model should see that 'Location' is more frequent with 'to'
        self.assertEqual(model.best_role(
            set(["Agent", "Location"]), "PPOBJ", "to", "slot"), "Location")
        
        # The model should ignore the preposition, since this is a 'SUBJ' slot 
        self.assertEqual(model.best_role(
            set(["Agent", "Theme"]), "SUBJ", "for", "slot"), "Agent")
     
if __name__ == "__main__":
    unittest.main()
