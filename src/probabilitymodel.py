#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

class ProbabilityModel:
    def __init__(self):
        self.data = {}
        
    def add_data(self, slot_class, role):
        if not slot_class in self.data:
            self.data[slot_class] = {}
        if not role in self.data[slot_class]:
            self.data[slot_class][role] = 0
        self.data[slot_class][role] += 1
        
    def best_role(self, role_set, slot_class):
        if not slot_class in self.data:
            return None
            
        possible_roles = set(self.data[slot_class].keys()).intersection(role_set)

        best_value = 0
        best_role = None
        for role in possible_roles:
            if self.data[slot_class][role] > best_value:
                best_value = self.data[slot_class][role]
                best_role = role
                
        return best_role

class ProbabilityModelTest(unittest.TestCase):
     def test_1(self):
        model = ProbabilityModel()
        self.assertEqual(model.best_role(set(["Agent", "Theme"]), "SUBJ"), None)
        model.add_data("SUBJ", "Theme")
        self.assertEqual(model.best_role(set(["Agent", "Theme"]), "SUBJ"), "Theme")
        model.add_data("SUBJ", "Agent")
        model.add_data("SUBJ", "Agent")
        model.add_data("SUBJ", "Agent")
        self.assertEqual(model.best_role(set(["Agent", "Theme"]), "SUBJ"), "Agent")
        self.assertEqual(model.best_role(set(["Patient", "Location"]), "SUBJ"), None)
     
if __name__ == "__main__":
    unittest.main()
