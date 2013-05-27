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

models = ["default", "slot_class", "slot", "predicate_slot"]

def multi_get(d, l, default = None):
    """Traverses multiple levels of a dictionary to get a key or None"""
    if not d: return default
    result = reduce(lambda d,k: d.get(k) if d else default, l, d)
    return result if result else default

def multi_default_dict(dimension):
    """Returns an empty int defaultdict of a given dimension"""
    if dimension <= 1: return defaultdict(int)
    else: return defaultdict(lambda: multi_default_dict(dimension - 1))

def multi_count(obj):
    """Returns the sum of all integers in a multidict"""
    if isinstance(obj, int): return obj
    else: return sum([multi_count(x) for x in obj.values()])

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
        self.data_slot_class = multi_default_dict(2)
        self.data_slot = multi_default_dict(3)
        self.data_predicate_slot = multi_default_dict(4)
                
        self.data_bootstrap_p = multi_default_dict(5)
        self.data_bootstrap_p1 = multi_default_dict(3)
        self.data_bootstrap_p2 = multi_default_dict(3)
        self.data_bootstrap_p3 = multi_default_dict(4)
        self.data_bootstrap_p1_sum = multi_default_dict(2)
        self.data_bootstrap_p2_sum = multi_default_dict(2)
        self.data_bootstrap_p3_sum = multi_default_dict(3)

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

    def add_data_bootstrap(self, role, predicate, predicate_class,
        slot_class, prep, headword, headword_class):
        
        if not slot_class == VerbnetFrame.slot_types["prep_object"]:
            prep = NO_PREP

        # Most specific
        self.data_bootstrap_p[slot_class][prep][predicate][headword][role] += 1
        
        # First backoff level
        self.data_bootstrap_p1[slot_class][predicate][role] += 1
        self.data_bootstrap_p2[predicate][headword_class][role] += 1
        self.data_bootstrap_p3[slot_class][prep][predicate_class][role] += 1
        self.data_bootstrap_p1_sum[slot_class][predicate] += 1
        self.data_bootstrap_p2_sum[predicate][headword_class] += 1
        self.data_bootstrap_p3_sum[slot_class][prep][predicate_class] += 1
        
        # Second backoff level
        self.data_slot_class[slot_class][role] += 1
        
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
        
    def best_roles_bootstrap(self, role_set, predicate, predicate_class, slot_class,
        prep, headword, headword_class, backoff_level, min_evidence):
        if not slot_class == VerbnetFrame.slot_types["prep_object"]:
            prep = NO_PREP
        
        if backoff_level == 0:
            data = multi_get(self.data_bootstrap_p, [slot_class, prep, predicate, headword], {})
        elif backoff_level == 1:
            data1 = multi_get(self.data_bootstrap_p1, [slot_class, predicate], {})
            data2 = multi_get(self.data_bootstrap_p2, [predicate, headword_class], {})
            data3 = multi_get(self.data_bootstrap_p3, [slot_class, prep, predicate_class], {})
            sum1 = multi_get(self.data_bootstrap_p1_sum, [slot_class, predicate], {})
            sum2 = multi_get(self.data_bootstrap_p2_sum, [predicate, headword_class], {})
            sum3 = multi_get(self.data_bootstrap_p3_sum, [slot_class, prep, predicate_class], {})
            
            roles = set(data1.keys()) & set(data2.keys()) & set(data3.keys())
            """roles = filter(lambda x: (x in role_set and 
                                      (data1[x] >= min_evidence) and
                                      (data2[x] >= min_evidence) and
                                      (data3[x] >= min_evidence)), roles)"""
            roles = filter(lambda x: (x in role_set and 
                    data1[x] + data2[x] + data3[x] >= 3 * min_evidence), roles)
            data = {x:((data1[x] / sum1) +
                       (data2[x] / sum2) +
                       (data3[x] / sum3)) for x in roles}
        elif backoff_level == 2:
            data = multi_get(self.data_slot_class, [slot_class], {})
        else:
            raise Exception("Unknown backoff level {}".format(backoff_level))
            
        if backoff_level in [0, 2]:
            data = {x:data[x] for x in data if x in role_set and data[x] >= min_evidence}
        
        if len(data) == 0:
            return None, None, None
        first = max(data, key = lambda r: data[r])
        if len(data) == 1:
            return first, None, 0
        second = max(data, key = lambda r: 0 if r == first else data[r])
        return first, second, data[first] / data[second]
        
        
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
