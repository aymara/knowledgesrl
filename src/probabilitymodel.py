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
    if isinstance(obj, int) or isinstance(obj, float): return obj
    else: return sum([multi_count(x) for x in obj.values()])
      
def check_depth(data, depth):
    is_scalar = isinstance(data, int) or isinstance(data, float)
    if depth == 0: return is_scalar
    if is_scalar: return False
    return all([check_depth(x, depth - 1) for x in data.values()])

def root_vnclass(vnclass):
    position = vnclass.find("-")
    if position == -1: return vnclass
    return vnclass[0:position]
  
class ProbabilityModel:

    """Class used to collect data and apply one probability model

    :var data_default: str. Dict The default assignements
    :var data_slot_class: str. 2D Dict The number of occurences of each role in every slot class
    :var data_slot: str. 3D Dict The number of occurences of each role in every slot
    :var data_slot: str. 4D Dict The number of occurences of each role in every (slot, predicate)
    
    """
    
    def __init__(self, vn_classes = None, vn_init_value = None):
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
        
        if vn_classes != None and vn_init_value != None:
            self.data_vnclass = defaultdict(lambda : {})
            for verb, verb_vnclass in vn_classes.items():
                for vnclass in verb_vnclass:
                    vnclass = root_vnclass(vnclass)
                    self.data_vnclass[verb][vnclass] = vn_init_value

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

    def add_data_bootstrap(self, role, predicate, predicate_classes,
        slot_class, prep, headword, headword_class):
        """Use one known occurence of a role in a given context to update the data
        of the bootstrap algorithm
        
        :param role: The attributed role
        :type role: str
        :param predicate: The predicate of which the slot is an argument
        :type predicate: str
        :param predicate_classes: The VerbNet classes of the predicate
        :type predicate_classes: str List
        :param slot_class: The slot class of the slot we want to resolve
        :type slot_class: str
        :param prep: If the slot is a PP, the preposition that introduced it
        :type prep: str
        :param headword: The headword of the argument
        :type headword: str:
        param headword_class: The WordNet class of the headword
        :type headword_class: str:
        """
        if not slot_class == VerbnetFrame.slot_types["prep_object"]:
            prep = NO_PREP

        # Most specific
        self.data_bootstrap_p[slot_class][prep][predicate][headword][role] += 1
        
        # First backoff level
        self.data_bootstrap_p1[slot_class][predicate][role] += 1
        self.data_bootstrap_p2[predicate][headword_class][role] += 1
        self.data_bootstrap_p1_sum[slot_class][predicate] += 1
        self.data_bootstrap_p2_sum[predicate][headword_class] += 1
        
        # For verbs with multiple posible VerbNet classes, the score is
        # uniformly repartited amon every classes
        increment = 1 / len(predicate_classes)
        for vn_class in predicate_classes:
            self.data_bootstrap_p3[slot_class][prep][vn_class][role] += increment
            self.data_bootstrap_p3_sum[slot_class][prep][vn_class] += increment

        # Second backoff level
        self.data_slot_class[slot_class][role] += 1

    def add_data_vnclass(self, matcher):
        """Fill data_vnclass using the data of a framematcher object
        
        :param matcher: A frame matcher after at least one matching
        :type matcher: FrameMatcher
        
        """
        
        verb = matcher.frame.predicate
        
        vnclass = None
        for frame, junk in matcher.best_data:
            if vnclass == None:
                vnclass = root_vnclass(frame.vnclass)
            elif vnclass != root_vnclass(frame.vnclass):
                vnclass = None
                break
                
        if vnclass != None:
            vnclass = root_vnclass(vnclass)
            self.data_vnclass[verb][vnclass] += 1
    
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
            possible_roles = sorted(list(set(data.keys()) & role_set))
            if possible_roles:
                return max(possible_roles, key = lambda role: data[role])

        return None

    def best_roles_bootstrap(self, role_set, predicate, predicate_classes, slot_class,
        prep, headword, headword_class, backoff_level, min_evidence):
        """Computes the two best roles for a slot at a given backoff level
        of the bootstrap algorithm
        
        :param role_set: The set of possible roles left by frame matching
        :type role_set: str Set
        :param predicate: The predicate of which the slot is an argument
        :type predicate: str
        :param predicate_classes: The VerbNet classes of the predicate
        :type predicate_classes: str List
        :param slot_class: The slot class of the slot we want to resolve
        :type slot_class: str
        :param prep: If the slot is a PP, the preposition that introduced it
        :type prep: str
        :param headword: The headword of the argument
        :type headword: str:
        param headword_class: The WordNet class of the headword
        :type headword_class: str:
        param backoff_level: The backoff level
        :type backoff_level: int
        :param min_evidence: The minimum number of occurences that a role must have to be returned
        :type min_evidence: int
        
        :returns (str, str, float) -- The two roles and their probability ratio
        """
        if not slot_class == VerbnetFrame.slot_types["prep_object"]:
            prep = NO_PREP
        
        if backoff_level == 0:
            data = multi_get(self.data_bootstrap_p,
                                [slot_class, prep, predicate, headword], {})
            data = {x:data[x] for x in data if x in role_set and data[x] >= min_evidence}
        elif backoff_level == 1:
            data1 = multi_get(self.data_bootstrap_p1,
                                [slot_class, predicate], {})
            data2 = multi_get(self.data_bootstrap_p2,
                                [predicate, headword_class], {})
            sum1 = multi_get(self.data_bootstrap_p1_sum,
                                [slot_class, predicate], 0)
            sum2 = multi_get(self.data_bootstrap_p2_sum,
                                [predicate, headword_class], 0)

            # We still have the problem of verbs with multiple VN classes
            # We choose not to give them an equal weight :
            # the weight of each class is proportionnal to its number of occurences
            # in the already resolved slots : n is not divided by sum(d.values())

            data3 = defaultdict(int)
            for vn_class in predicate_classes:
                d = multi_get(self.data_bootstrap_p3,
                                [slot_class, prep, vn_class], {})
                for role, n in d.items():
                    data3[role] += n
                
            sum3 = sum(multi_get(self.data_bootstrap_p3_sum,
                                [slot_class, prep, vn_class], 0)
                       for vn_class in predicate_classes)
            
            roles = set(data1.keys()) & set(data2.keys()) & set(data3.keys())
            roles = list(filter(lambda x: (x in role_set and
                                    data1[x] + data2[x] + data3[x] >= 3 * min_evidence),
                             roles))
            data = {x:(data1[x] / sum1 + data2[x] / sum2 + data3[x] / sum3)
                        for x in roles}
        elif backoff_level == 2:
            data = multi_get(self.data_slot_class, [slot_class], {})
            data = {x:data[x] for x in data if x in role_set and data[x] >= min_evidence}
        else:
            raise Exception("Unknown backoff level {}".format(backoff_level))
        
        # At this point, data is a dictionnary that maps every role of :role_set
        # that meet the evidence count :min_evidence in the model :backoff_level
        # to the number of occurences of this role in the given conditions
        # according to the model.
        
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
