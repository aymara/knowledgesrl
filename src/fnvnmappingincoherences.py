#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import re
import os
import sys
import getopt
import framenetreader

display_framenet = False
display_verbnet = False

options = getopt.getopt(sys.argv[1:], "", ["verbnet", "framenet"])

for opt,v in options[0]:
    if opt == "--verbnet": display_verbnet = True
    elif opt == "--framenet": display_framenet = True

if not display_framenet and not display_verbnet:
    display_verbnet = True

role_matching_file = "../data/vn-fn-roles.xml"
vb_dir = "../data/verbnet-3.2/"
fn_frames_dir = "../data/fndata-1.5/frame/"
corpus_dir = "../data/fndata-1.5/fulltext/"

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
    xmlns = "{http://framenet.icsi.berkeley.edu}"
    for filename in os.listdir(fn_frames_dir):
        if not filename[-4:] == ".xml": continue
        root = ET.ElementTree(file=fn_frames_dir+filename).getroot()

        fn_roles[root.attrib["name"]] = []
        for arg_data in root.findall(xmlns+"FE"):
            fn_roles[root.attrib["name"]].append(arg_data.attrib["name"])
    return fn_roles
    
def display_vn_issues():
    for vn_class, bad_roles_class in sorted(bad_vn_roles.items()):
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

fn_roles = load_fn_data()

root = ET.ElementTree(file=role_matching_file)

bad_vn_roles = {}
bad_fn_frames = {}
bad_fn_roles = {}

for mapping in root.getroot():
    vn_class = mapping.attrib["class"]
    fn_frame = mapping.attrib["fnframe"]
        
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
    
