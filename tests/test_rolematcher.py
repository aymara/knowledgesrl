#!/usr/bin/env python3

import sys
sys.path.append('/home/cjaffre/knowledgesrl/src')


import unittest
from xml.etree import ElementTree as ET
from collections import defaultdict

import framenet
from rolematcher import VnFnRoleMatcher, vn_roles_list, authorised_roles, RoleMatchingError
import paths


class VnFnRoleMatcherTest(unittest.TestCase):

    def setUp(self):
        self.mappings = defaultdict(lambda: defaultdict(dict)) # Dict[fnframe, Dict[fnrole, Dict[vnclass, vnrole]]]
        self.issues = {
            # VerbNet roles stored in vn_roles_additionnal
            "new_vn_roles": {},
            # FrameNet frames with various VerbNet classes attached
            "frame_is_vnclass_dependent": 0,
            # FrameNet frames with contradictory role mappings (depending on VerbNet class)
            "frame_is_vnclass_contradictory": 0,
            # FN roles that can correspond to several VN roles for the same frame
            "ambiguities": 0,
            # FN roles that can correspond to several VN roles for the same frame and the same VN class
            "ambiguities2": 0
        }

        self.matcher = VnFnRoleMatcher(paths.Paths.VNFN_MATCHING,
                                       framenet.FrameNet())

        for mapping in ET.ElementTree(file=str(paths.Paths.VNFN_MATCHING)).findall("vncls"):
            fnframe, vnclass = mapping.get("fnframe"), mapping.get("class")
            for role in mapping.findall("roles/role"):
                fnrole, vnrole = role.get("fnrole"), role.get("vnrole")
                self.mappings[fnframe][fnrole][vnclass] = vnrole


    def test_parsing(self):

        num_role_frames = 0
        for fnrole_name, fnrole_data in self.matcher.fn_roles.items():
            for frame_name, frame_data in fnrole_data.items():
                num_role_frames += 1
                if frame_name == "all": continue
                for class_name, class_data in frame_data.items():
                    if class_name == "all":
                        if len(class_data) > 1:
                            self.issues["ambiguities"] += 1
                        continue
                    if len(class_data) > 1:
                        self.issues["ambiguities2"] += 1
                        
                    for vnrole in class_data:
                        if not vnrole in vn_roles_list:
                            if not vnrole in self.issues["new_vn_roles"]:
                                self.issues["new_vn_roles"][vnrole] = 0
                            self.issues["new_vn_roles"][vnrole] += 1
                            self.assertIn(vnrole, authorised_roles)
                
        for fnframe in self.mappings:
            frame_is_vnclass_dependent = False
            frame_is_vnclass_contradictory = False
            for fnrole in self.mappings[fnframe]:
                role_mapping_per_vnclass = self.mappings[fnframe][fnrole]
                if len(role_mapping_per_vnclass.keys()) > 1:
                    frame_is_vnclass_dependent = True
                if len(set(role_mapping_per_vnclass.values())) > 1:
                    frame_is_vnclass_contradictory = True

            if frame_is_vnclass_dependent:
                self.issues["frame_is_vnclass_dependent"] += 1

            if frame_is_vnclass_contradictory:
                self.issues["frame_is_vnclass_contradictory"] += 1

        # fnrole-fnframe entries
        self.assertEqual(num_role_frames, 1179)
        # different FrameNet frames
        self.assertEqual(len(self.mappings), 273)
        # FN frames that have different possible VN mappings
        self.assertEqual(self.issues["frame_is_vnclass_dependent"], 154)
        # FN frames that have contradictory mappings
        self.assertEqual(self.issues["frame_is_vnclass_contradictory"], 108)
        # FrameNet role corresponding to several VerbNet roles in the same
        # FN frame for the same VerbNet class
        self.assertEqual(self.issues["ambiguities"], 185)
        # Framenet role corresponding to several VerbNet roles in the same
        # FN frame for the same VerbNet class
        self.assertEqual(self.issues["ambiguities2"], 7)

        role_encounters = {
            "Trajectory": 9, "Goal": 4, "Initial_Location": 15,
            "Value": 9, "Result": 37, "Pivot": 7}

        for role, n in self.issues["new_vn_roles"].items():
            self.assertEqual(role_encounters[role], n)
            
    def test_matching(self):
        def match(fn_role, vn_role, fn_frame=None, vn_classes=None):
            """Tell wether fn_role can be mapped to vn_role in a given context

            :param fn_role: The FrameNet role.
            :type fn_role: str.
            :parma vn_role: The VerbNet role.
            :type vn_role: str.
            :param fn_frame: The FrameNet frame in which the roles have to be mapped.
            :type fn_frame: str.
            :param vn_classes: A list of VerbNet classes for which the roles have to be mapped.
            :type vn_classes: str List.
            :returns: bool -- True if the two roles can be mapped, False otherwise
            """

            return vn_role in self.matcher.possible_vn_roles(fn_role, fn_frame, vn_classes)
        
        self.assertTrue(match("Fixed_location", "Location"))
        self.assertFalse(match("Fixed_location", "Agent"))
        self.assertTrue(match("Connector", "Patient", "Inchoative_attaching"))
        self.assertFalse(match("Speaker", "Patient", "Talking_into"))
        self.assertTrue(match("Grantee", "Recipient", "Grant_permission", ["order-60"]))
        self.assertFalse(match("Message", "Agent", "Communication_manner", ["nonverbal_expression-40.2"]))
        
        with self.assertRaises(RoleMatchingError):
            match("Non_existing_fn_role", "Agent")
        with self.assertRaises(RoleMatchingError):
            match("Fixed_location", "Destination", "Non_existing_fn_frame")
        with self.assertRaises(RoleMatchingError):
            match("Non_existing_fn_role", "Agent", "Talking_into")
        with self.assertRaises(RoleMatchingError):
            match("Purpose", "Agent", "Non_existing_fn_frame", ["66"])
        with self.assertRaises(RoleMatchingError):
            match("Non_existing_fn_role", "Patient", "Grant_permission", ["order-60"])
        
if __name__ == '__main__':
    unittest.main()
