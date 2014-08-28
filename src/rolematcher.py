#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Map FrameNet and VerbNet roles """

import unittest
import xml.etree.ElementTree as ET

import paths
from collections import defaultdict


# VN roles given by table 2 of http://verbs.colorado.edu/~mpalmer/projects/verbnet.html
vn_roles_list = [
    "Actor", "Agent", "Asset", "Attribute", "Beneficiary", "Cause",
    "Co-Agent", "Co-Patient", "Co-Theme", # Not in the original list
    "Location", "Destination", "Source", "Experiencer", "Extent",
    "Instrument", "Material", "Product", "Patient", "Predicate",
    "Recipient", "Stimulus", "Theme", "Time", "Topic"]
    
# Added roles
vn_roles_additionnal = ["Goal", "Initial_Location", "Pivot", "Result",
    "Trajectory", "Value"]
    
# List of VN roles that won't trigger an error in unit tests
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
    """Reads the mapping between VN and FN roles, and can then be used to compare them
    
    :var fn_roles: data structure used to store the mapping between VN and FN roles
    :var mappings: associate possible mapping (FN roles -> VN roles) to every FN frames
    :var issues: used to store statistics about the problem encoutered
    """
    
    def __init__(self, path):
        # 4-dimensions matrix :
        # self.fn_roles[fn_role][fn_frame][vn_class][i] is the
        # i-th possible VN role associated to fn_role for the frame fn_frame
        # and a verb in vn_class.
        self.fn_roles = {}
        
        # This is used to compute statistics, but plays no role in role matching
        self.mappings = {}
        
        self.issues = {
            # VerbNet roles stored in vn_roles_additionnal
            "new_vn_roles":{},
            # FrameNet frames with various VerbNet classes attached
            "vbclass_dependent":0,
            # FrameNet frames with contradictory role mappings (depending on VerbNet class)
            "vbclass_contradictory":0,
            # FN roles that can correspond to several VN roles for the same frame
            "ambiguities":0,
            # FN roles that can correspond to several VN roles for the same frame and the same VN class
            "ambiguities2":0
        }
        
        self._build_mapping(path)
    
    def _build_mapping(self, path):
        root = ET.ElementTree(file=path)

        for mapping in root.getroot():
            vn_class = mapping.attrib["class"]
            fn_frame = mapping.attrib["fnframe"]

            mapping_as_dict = {}

            for role in mapping.findall("roles/role"):
                vn_role = role.attrib["vnrole"]
                fn_role = role.attrib["fnrole"]

                vn_role = self._handle_co_roles(vn_role)
                
                mapping_as_dict[fn_role] = vn_role
                  
                self._add_relation(
                    fn_role, vn_role,
                    fn_frame, vn_class)
            
            self._update_mapping_list(fn_frame, mapping_as_dict)

    def _handle_co_roles(self, vn_role):
        if vn_role[-1] == "1":
            return vn_role[0:-1]
        if vn_role[-1] == "2":
            return "Co-"+vn_role[0:-1]
        return vn_role
    
    def _update_mapping_list(self, fn_frame, new_mapping):
        if not fn_frame in self.mappings:
            self.mappings[fn_frame] = []
                
        found = False
        for compare in self.mappings[fn_frame]:
            if compare == new_mapping:
                   found = True
                   break
                   
        if not found:
            self.mappings[fn_frame].append(new_mapping)
                
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

    def possible_vn_roles(self, fn_role, fn_frame = None, vn_classes = None):
        """Returns the set of VN roles that can be mapped to a FN role in a given context
        
        :param fn_role: The FrameNet role.
        :type fn_role: str.
        :parma vn_role: The VerbNet role.
        :type vn_role: str.
        :param fn_frame: The FrameNet frame in which the roles have to be mapped.
        :type fn_frame: str.
        :param vn_classes: A list of VerbNet classes for which the roles have to be mapped.
        :type vn_classes: str List.
        :returns: str List -- The list of VN roles
        """

        if not fn_role in self.fn_roles:
            raise RoleMatchingError(
                "{} role does not seem"\
                " to exist".format(fn_role))
        if fn_frame == None and vn_classes == None:
            return self.fn_roles[fn_role]["all"]
        
        if fn_frame != None and not fn_frame in self.fn_roles[fn_role]:
            raise RoleMatchingError(
                "{} role does not seem"\
                " to belong to frame {}".format(fn_role, fn_frame))
        if vn_classes == None:
            return self.fn_roles[fn_role][fn_frame]["all"]
        
        if fn_frame == None:
            frames = list(self.fn_roles[fn_role].keys())
            frames.remove("all")
        else:
            frames = [fn_frame]
        
        vn_roles = set()

        for vn_class in vn_classes:
            # Use the format of the vn/fn mapping
            vn_class = "-".join(vn_class.split('-')[1:])
            for frame in frames:
                while True:
                    if vn_class in self.fn_roles[fn_role][frame]:
                        vn_roles = vn_roles.union(self.fn_roles[fn_role][frame][vn_class])
                        break
                    position = max(vn_class.rfind("-"), vn_class.rfind("."))
                    if position == -1: break
                    vn_class = vn_class[0:position]
        
        if vn_roles == set():
            # We don't have the mapping for any of the VN class provided in vn_classes
            raise RoleMatchingError(
                "None of the given VerbNet classes ({}) were corresponding to"\
                " {} role and frame {}".format(vn_class, fn_role, fn_frame))
        
        return vn_roles

    def match(self, fn_role, vn_role, fn_frame = None, vn_classes = None):
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
        
        return vn_role in self.possible_vn_roles(fn_role, fn_frame, vn_classes)


    def build_frames_vnclasses_mapping(self):
        """ Builds a mapping between framenet frames and associated verbnet classes """
        self.fn_frames = defaultdict(lambda : set())
        for fn_role in self.fn_roles:
            if fn_role == "all": continue
            for fn_frame in self.fn_roles[fn_role]:
                if fn_frame == "all": continue
                for vn_class in self.fn_roles[fn_role][fn_frame]:
                    if vn_class == "all": continue
                    self.fn_frames[fn_frame].add(vn_class)

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
