#!/usr/bin/env python3

import unittest

from rolematcher import VnFnRoleMatcher, vn_roles_list, authorised_roles, RoleMatchingError
import paths


class VnFnRoleMatcherTest(unittest.TestCase):
    def test_parsing(self):
        matcher = VnFnRoleMatcher(paths.VNFN_MATCHING)

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
                            self.assertIn(vnrole, authorised_roles)
                
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
            
    def test_matching(self):
        matcher = VnFnRoleMatcher(paths.VNFN_MATCHING)
        
        self.assertTrue(matcher.match("Fixed_location", "Location"))
        self.assertFalse(matcher.match("Fixed_location", "Agent"))
        self.assertTrue(matcher.match("Connector", "Patient", "Inchoative_attaching"))
        self.assertFalse(matcher.match("Speaker", "Patient", "Talking_into"))
        self.assertTrue(matcher.match("Grantee", "Recipient", "Grant_permission", ["order-60"]))
        self.assertFalse(matcher.match("Message", "Agent", "Communication_manner", ["nonverbal_expression-40.2"]))
        
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
                "Non_existing_fn_role", "Patient", "Grant_permission", ["order-60"])
