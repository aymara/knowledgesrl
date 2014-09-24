#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os
import sys
import getopt
from distutils.version import LooseVersion

import paths


display_framenet = False
display_verbnet = False

options = getopt.getopt(sys.argv[1:], "", ["verbnet", "framenet"])

for opt,v in options[0]:
    if opt == "--verbnet": display_verbnet = True
    elif opt == "--framenet": display_framenet = True

if not display_framenet and not display_verbnet:
    display_verbnet = True

class VerbnetRoleReader:
    
    def __init__(self, path):
        self.classes = {}
        self.classes_names = {}

        for filename in path.glob('*.xml'):
            class_name = filename.stem.split("-")[0]
            root = ET.ElementTree(file=(path / filename).as_posix())
            self._handle_class(root.getroot(), [], set(), class_name)
    
    def _handle_class(self, xml_class, parent_classes, parent_roles, class_name):
        parent_classes = parent_classes[:]
        
        # Use the format of the vn/fn mapping
        vnclass = "-".join(xml_class.attrib["ID"].split('-')[1:])
        
        parent_classes.append(vnclass)

        for role in xml_class.find("THEMROLES"):
            parent_roles.add(role.attrib["type"])

        for vn_class in parent_classes:
            if not vn_class in self.classes:
                self.classes_names[vn_class] = class_name
                self.classes[vn_class] = set()
                
            self.classes[vn_class] = self.classes[vn_class] | parent_roles
            
        for subclass in xml_class.find("SUBCLASSES"):
            self._handle_class(subclass, parent_classes, parent_roles, class_name)

def load_fn_data():
    fn_roles = {}
    fn_verbal_frames = set()
    xmlns = "{http://framenet.icsi.berkeley.edu}"
    for filename in paths.FRAMENET_FRAMES.glob('*.xml'):
        root = ET.ElementTree(file=filename.as_posix()).getroot()

        fn_roles[root.attrib["name"]] = []
        for arg_data in root.findall(xmlns+"FE"):
            fn_roles[root.attrib["name"]].append(arg_data.attrib["name"])
        for lu in root.findall(xmlns+"lexUnit"):
            if lu.attrib["name"].split(".")[1] == "v":
                fn_verbal_frames.add(root.attrib["name"])
                break
    return fn_roles, fn_verbal_frames
    
def display_vn_issues():
    for vn_class in sorted(bad_vn_roles, key=LooseVersion):
        print("VerbNet class : {}-{} ({})".format(
            vn_class, classes_names[vn_class], vn_classes[vn_class]))
        print("{:>30} {:>20} {:>25}".format(
            "FrameNet frame", "FrameNet Role", "Associated VerbNet Role"))
        for bad_role in bad_vn_roles[vn_class]:
            print("{:>30} {:>20} {:>25}".format(
                bad_role["fn_frame"], bad_role["fn_role"],
                bad_role["vn_role"]
            ))
        print("\n")

def display_fn_issues():
    print("Cannot find following FrameNet frame :\n")

    for fn_frame, vn_classes_list in sorted(bad_fn_frames.items()):
        print("{}:\n{}\n".format(
            fn_frame, "\n".join([x+"-"+classes_names[x] for x in vn_classes_list])
        ))

    for fn_frame, bad_roles_frame in sorted(bad_fn_roles.items()):
        print("\nFrameNet frame : {}".format(fn_frame))
        print("Allowed roles: {}".format(", ".join(fn_roles[fn_frame])))
        print("{:>20} {:>30} {:>30}".format(
            "FrameNet Role", "Associated VerbNet Role", "VerbNet class"))
            
        for bad_role in bad_roles_frame:
            print("{:>20} {:>30} {:>30}".format(
                bad_role["fn_role"], bad_role["vn_role"],
                bad_role["vn_class"]+"-"+classes_names[bad_role["vn_class"]]
            ))
            
role_reader = VerbnetRoleReader(paths.VERBNET_PATH)
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

fn_roles, fn_verbal_frames = load_fn_data()

root = ET.ElementTree(file=paths.VNFN_MATCHING.as_posix())

bad_vn_roles = {}
bad_fn_frames = {}
bad_fn_roles = {}
encountered_fn_frames = set()

for mapping in root.getroot():
    vn_class = mapping.attrib["class"]
    fn_frame = mapping.attrib["fnframe"]
    encountered_fn_frames.add(fn_frame)
        
    if not fn_frame in fn_roles:
        if not fn_frame in bad_fn_frames:
            bad_fn_frames[fn_frame] = []
        bad_fn_frames[fn_frame].append(vn_class)
        
    for role in mapping.findall("roles/role"):
        vn_role = role.attrib["vnrole"]
        fn_role = role.attrib["fnrole"]

        if fn_frame in fn_roles and not fn_role in fn_roles[fn_frame]:
            if not fn_frame in bad_fn_roles:
                bad_fn_roles[fn_frame] = []
            bad_fn_roles[fn_frame].append({
                "fn_role":fn_role,
                "vn_role":vn_role, "vn_class":vn_class
            })

        if not vn_role in vn_classes[vn_class]:
            if not vn_class in bad_vn_roles:
                bad_vn_roles[vn_class] = []
            bad_vn_roles[vn_class].append({
                "fn_frame":fn_frame, "fn_role":fn_role,
                "vn_role":vn_role
            })
            
if display_verbnet: display_vn_issues()
if display_framenet: display_fn_issues()
    


mapped = fn_verbal_frames & encountered_fn_frames
additionnal = encountered_fn_frames - fn_verbal_frames
print("{} verbal frames mapped (out of {})".format(len(mapped), len(fn_verbal_frames)))
print("{} non verbal frames mapped".format(len(additionnal)))
