#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import xml.etree.ElementTree as ET
import re

role_matching_file = "../data/vn-fn-roles.xml"

vn_roles_list = [
    "Actor", "Agent", "Asset", "Attribute", "Beneficiary", "Cause",
    "Location", "Destination", "Source", "Experiencer", "Extent",
    "Instrument", "Material", "Product", "Patient", "Predicate",
    "Recipient", "Stimulus", "Theme", "Time", "Topic"]
# Added roles
vn_roles_additionnal = [
    "Concept", "Eclipsed", "Event", 
    "Oblique", "Proposition", "Value"]
authorised_roles = vn_roles_list + vn_roles_additionnal

class RoleMatchingError(Exception):
    """ Missing data to compare a vn and a fn role
    
    :var msg: str, a message detailing what is missing
    """
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return ("Error : {}".format(self.msg))

class VnFnRoleMatcher():
    def __init__(self, path):
        self.fn_roles = {}
        self.mappings = {}
        self.issues = {
            "empty_vn_role":0,
            "typo":0,
            "new_vn_roles":{},
            "vbclass_dependent":0,
            "vbclass_contradictory":0,
            "ambiguities":0,
            "ambiguities2":0
        }
        
        root = ET.ElementTree(file=path)

        for mapping in root.getroot():
            vn_class = mapping.attrib["class"]
            fn_frame = mapping.attrib["fnframe"]

            mapping_as_dict = {}                          

            for role in mapping.findall("roles/role"):
                vn_role = role.attrib["vnrole"]
                fn_role = role.attrib["fnrole"]
                
                if vn_role == "":
                    self.issues["empty_vn_role"] += 1
                    continue
                if vn_role == "Eperiencer":
                    self.issues["typo"] += 1
                    vn_role = "Experiencer"
                if vn_role == "Patients":
                    self.issues["typo"] += 1
                    vn_role = "Patient"
                if fn_role == "Eperiencer":
                    self.issues["typo"] += 1
                    fn_role = "Experiencer"
                
                mapping_as_dict[fn_role] = vn_role
                  
                self._add_relation(
                    fn_role, vn_role,
                    fn_frame, vn_class)
                    
            if not fn_frame in self.mappings:
                self.mappings[fn_frame] = []
                
            found = False
            for compare in self.mappings[fn_frame]:
                if compare == mapping_as_dict:
                       found = True
                       break
                       
            if not found:
                self.mappings[fn_frame].append(mapping_as_dict)
                
    def _add_relation(self, fn_role, vn_role, fn_frame, vn_class):
        if not fn_role in self.fn_roles:
            self.fn_roles[fn_role] = {"all":set()}
        if not fn_frame in self.fn_roles[fn_role]:
            self.fn_roles[fn_role][fn_frame] = {"all":set()}
        if not vn_class in self.fn_roles[fn_role][fn_frame]:
            self.fn_roles[fn_role][fn_frame][vn_class] = set()
            
        self.fn_roles[fn_role]["all"].add(vn_role)
        self.fn_roles[fn_role][fn_frame]["all"].add(vn_role)
        self.fn_roles[fn_role][fn_frame][vn_class].add(vn_role)

    def match(self, fn_role, vn_role, fn_frame = None, vn_classes = None):
        if not fn_role in self.fn_roles:
            raise RoleMatchingError(
                "{} role does not seem"\
                " to exist".format(fn_role))
        if fn_frame == None:
            return vn_role in self.fn_roles[fn_role]["all"]
            
        if not fn_frame in self.fn_roles[fn_role]:
            raise RoleMatchingError(
                "{} role does not seem"\
                " to belong to frame {}".format(fn_role, fn_frame))
        if vn_classes == None:
            return vn_role in self.fn_roles[fn_role][fn_frame]["all"]

        can_conclude = False
        for vn_class in vn_classes:
            if vn_class in self.fn_roles[fn_role][fn_frame]:
                can_conclude = True
                if vn_role in self.fn_roles[fn_role][fn_frame][vn_class]:
                    return True      
                    
        if not can_conclude:
            raise RoleMatchingError(
                "None of the given VerbNet classes ({}) were corresponding to"\
                " {} role and frame {}".format(vn_class, fn_role, fn_frame))
        return False  

class VnFnRoleMatcherTest(unittest.TestCase):
    def test_parsing(self):
        matcher = VnFnRoleMatcher(role_matching_file)
        
        self.assertEqual(len(matcher.fn_roles), 438)

        num_role_frames = 0
        for fnrole_name, fnrole_data in matcher.fn_roles.items():
            for frame_name, frame_data in fnrole_data.items():
                num_role_frames += 1
                if frame_name == "all": continue
                for class_name, class_data in frame_data.items():
                    if class_name == "all":
                        if len(class_data) > 1:
                            matcher.issues["ambiguities"] += 1
                        continue
                    if len(class_data) > 1:
                        matcher.issues["ambiguities2"] += 1
                        
                    for vnrole in class_data:
                        if not vnrole in vn_roles_list:
                            if not vnrole in matcher.issues["new_vn_roles"]:
                                matcher.issues["new_vn_roles"][vnrole] = 0
                            matcher.issues["new_vn_roles"][vnrole] += 1
                            self.assertIn(re.sub('[^a-zA-Z]', '', vnrole), authorised_roles)
                
        for fn_frame,data in matcher.mappings.items():
            contradictory = False
            for mapping in data:
                for arg, role in mapping.items():
                    for mapping2 in data:
                        if arg in mapping2 and role != mapping2[arg]:
                            contradictory = True
 
            if len(mapping) > 1:
                matcher.issues["vbclass_dependent"] += 1
            if contradictory: 
                matcher.issues["vbclass_contradictory"] += 1           
                    
        print("Found {} fnrole-fnframe entries".format(num_role_frames))
        print("{} different FrameNet frames".format(len(matcher.mappings)))
        
        print("{} frames have different possible mappings".format(matcher.issues["vbclass_dependent"]))
        print("{} frames have contradictory mappings".format(matcher.issues["vbclass_contradictory"]))
        print("Found {} cases of a FrameNet role corresponding to several"\
            " VerbNet roles in the same FrameNet frame".format(matcher.issues["ambiguities"]))
        print("Found {} cases of a FrameNet role corresponding to several"\
            " VerbNet roles in the same FrameNet frame for the same VerbNet"\
            " class".format(matcher.issues["ambiguities2"]))

        for role, n in matcher.issues["new_vn_roles"].items():
            print("VerbNet role \"{}\" was encountered {} time(s)".format(
                role, n))
                
        print("{} other minor errors".format(matcher.issues["typo"]+matcher.issues["empty_vn_role"]))
        
            
    def test_matching(self):
        matcher = VnFnRoleMatcher(role_matching_file)
        
        self.assertTrue(matcher.match("Fixed_location", "Destination"))
        self.assertFalse(matcher.match("Fixed_location", "Agent"))
        self.assertTrue(matcher.match("Individuals", "Actor", "Make_acquaintance"))
        self.assertFalse(matcher.match("Speaker", "Patient", "Talking_into"))
        self.assertTrue(matcher.match("Grantee", "Patient", "Grant_permission", ["60"]))
        self.assertFalse(matcher.match("Purpose", "Agent", "Exhaust_resource", ["66"]))
        
        with self.assertRaises(RoleMatchingError):
            matcher.match(
                "Non_existing_fn_role", "Agent")
        with self.assertRaises(RoleMatchingError):
            matcher.match(
                "Fixed_location", "Destination", "Non_existing_fn_frame")
        with self.assertRaises(RoleMatchingError):
            matcher.match(
                "Non_existing_fn_role", "Agent", "Talking_into")
        with self.assertRaises(RoleMatchingError):
            matcher.match(
                "Purpose", "Agent", "Non_existing_fn_frame", ["66"])
        with self.assertRaises(RoleMatchingError):
            matcher.match(
                "Non_existing_fn_role", "Patient", "Grant_permission", ["60"])

if __name__ == "__main__":
    unittest.main()
