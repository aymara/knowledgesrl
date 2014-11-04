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

        # fnrole-fnframe entries
        self.assertEqual(num_role_frames, 1179)
        # different FrameNet frames
        self.assertEqual(len(matcher.mappings), 274)
        # FN frames that have different possible VN mappings
        self.assertEqual(matcher.issues["vbclass_dependent"], 244)
        # FN frames that have contradictory mappings
        self.assertEqual(matcher.issues["vbclass_contradictory"], 108)
        # FrameNet role corresponding to several VerbNet roles in the same
        # FN frame for the same VerbNet class
        self.assertEqual(matcher.issues["ambiguities"], 185)
        # Framenet role corresponding to several VerbNet roles in the same
        # FN frame for the same VerbNet class
        self.assertEqual(matcher.issues["ambiguities2"], 7)

        role_encounters = {
            'Trajectory': 9, 'Goal': 4, 'Initial_Location': 15,
            'Value': 9, 'Result': 37, 'Pivot': 7}

        for role, n in matcher.issues["new_vn_roles"].items():
            self.assertEqual(role_encounters[role], n)
            
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
