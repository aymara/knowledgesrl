#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import re
import os

def handle_co_roles(vn_role):
    if vn_role[-1] == "1":
        return vn_role[0:-1]
    if vn_role[-1] == "2":
        return "Co-"+vn_role[0:-1]
    return vn_role

def correct_errors(vn_role, fn_role):
    if vn_role == "Eperiencer":
        issues["typo"] += 1
        vn_role = "Experiencer"
    if vn_role == "Patients":
        issues["typo"] += 1
        vn_role = "Patient"
    if fn_role == "Eperiencer":
        issues["typo"] += 1
        fn_role = "Experiencer"
    return vn_role, fn_role
            
role_matching_file = "../data/vn-fn-roles.xml"
vb_dir = "../data/verbnet-3.2/"

class VerbnetRoleReader:
    
    def __init__(self, path):
        self.classes = {}
        self.classes_names = {}

        self.filename = ""

        for filename in os.listdir(path):
            if not filename[-4:] == ".xml": continue

            self.filename = filename
            class_name = filename.split("-")[0]
            root = ET.ElementTree(file=path+self.filename)
            self._handle_class(root.getroot(), [], set(), class_name)
    
    def _handle_class(self, xml_class, parent_classes, parent_roles, class_name):
        parent_classes = parent_classes[:]
        
        # Use the format of the vn/fn mapping
        vnclass = "-".join(xml_class.attrib["ID"].split('-')[1:])
        
        parent_classes.append(vnclass)

        for xml_frame in xml_class.find("FRAMES"):
            for element in xml_frame.find("SYNTAX"):
                if ((not element.tag in ["VERB", "PREP", "LEX"]) and
                    "value" in element.attrib
                ): 
                    parent_roles.add(element.attrib["value"])

        for vn_class in parent_classes:
            if not vn_class in self.classes:
                self.classes_names[vn_class] = class_name
                self.classes[vn_class] = set()
                
            self.classes[vn_class] = self.classes[vn_class] | parent_roles
            
        for subclass in xml_class.find("SUBCLASSES"):
            self._handle_class(subclass, parent_classes, parent_roles, class_name)

role_reader = VerbnetRoleReader(vb_dir)
vn_classes = role_reader.classes
classes_names  = role_reader.classes_names
vn_classes["13.4"] = vn_classes["13.4.1"]
classes_names["13.4"] = classes_names["13.4.1"]
vn_classes["34"] = vn_classes["34.1"]
classes_names["34"] = classes_names["34.1"]
vn_classes["37.1"] = vn_classes["37.1.1"]
classes_names["37.1"] = classes_names["37.1.1"]
vn_classes["58"] = vn_classes["58.1"]
classes_names["58"] = classes_names["58.1"]
vn_classes["88"] = vn_classes["88.1"]
classes_names["88"] = classes_names["88.1"]

root = ET.ElementTree(file=role_matching_file)

bad_roles = {}
for mapping in root.getroot():
    vn_class = mapping.attrib["class"]
    fn_frame = mapping.attrib["fnframe"]

    for role in mapping.findall("roles/role"):
        vn_role = role.attrib["vnrole"]
        fn_role = role.attrib["fnrole"]
        
        if not vn_role in vn_classes[vn_class]:
            if not vn_class in bad_roles:
                bad_roles[vn_class] = []
            bad_roles[vn_class].append({
                "fn_frame":fn_frame, "fn_role":fn_role,
                "vn_role":vn_role
            })

for vn_class, bad_roles_class in sorted(bad_roles.items()):
    print("VerbNet class : {}-{} ({})".format(
        vn_class, classes_names[vn_class], vn_classes[vn_class]))
    print("{:>30} {:>20} {:>25}".format(
        "FrameNet frame", "FrameNet Role", "Associated VerbNet Role"))
    for bad_role in bad_roles_class:
        print("{:>30} {:>20} {:>25}".format(
            bad_role["fn_frame"], bad_role["fn_role"],
            bad_role["vn_role"]
        ))
    print("\n")
        
    
