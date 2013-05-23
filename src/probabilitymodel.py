#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Implements the probability models proposed in the article to make a choice
    in slot where frame matching left several possible roles.
    
    There are four possible models :
      * default does not use any collected data, nor the list of possible roles
       and makes default assignement depending on the slot class
      * slot_class choose the most likely of the possible roles given the slot
        class of the slot (the difference with default it is guaranteed that the
        chosen role will be in the list of possible roles for this slot)
      * slot choose the most likely of the possible roles given the slot type
        (that is, the slot class, but with the PP class is divided into one class
        for each preposition)
      * predicate_slot choose the most likely of the possible roles given the
        slot type and the predicate
"""

import unittest
from framestructure import *
from collections import defaultdict
from functools import reduce

NO_PREP = "no_prep_magic_value"

def multi_get(d, l):
    """Traverses multiple levels of a dictionary to get a key or None"""
    return reduce(lambda d,k: d.get(k) if d else None, l, d) if d else None


class ProbabilityModel:

    """Class used to collect data and apply one probability model

    :var data_default: str. Dict The default assignements
    :var data_slot_class: str. 2D Dict The number of occurences of each role in every slot class
    :var data_slot: str. 3D Dict The number of occurences of each role in every slot
    :var data_slot: str. 4D Dict The number of occurences of each role in every (slot, predicate)
    
    """
    
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
        """Use one known occurence of a role in a given context to update the data
        of every model
        
        :param slot_class: The slot class of the slot where the role occured
        :type slot_class: str
        :param role: The role that occured
        :type role: str
        :param prep: The preposition which introduced the slot if it was a PP slot
        :type prep: str
        :param predicate: The predicate of which the slot was an argument
        :type predicate: str
        """
        self.data_slot_class[slot_class][role] += 1
        
        if slot_class == VerbnetFrame.slot_types["prep_object"]:
            self.data_slot[slot_class][prep][role] += 1
            self.data_predicate_slot[predicate][slot_class][prep][role] += 1
        else:
            self.data_slot[slot_class][NO_PREP][role] += 1
            self.data_predicate_slot[predicate][slot_class][NO_PREP][role] += 1
        
    def best_role(self, role_set, slot_class, prep, predicate, model):
        """Apply one probability model to resolve one slot
        
        :param role_set: The set of possible roles left by frame matching
        :type role_set: str Set
        :param slot_class: The slot class of the slot we want to resolve
        :type slot_class: str
        :param prep: If the slot is a PP, the preposition that introduced it
        :type prep: str
        :param predicate: The predicate of which the slot is an argument
        :type predicate: str
        :param model: The model that we want to apply
        :type model: str
        """
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

     """ Test class for ProbabilityModel """

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
