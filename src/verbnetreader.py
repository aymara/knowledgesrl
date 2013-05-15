#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Read VerbNet and build a list of allowed VerbNet frame for each verb"""

import unittest
import xml.etree.ElementTree as ET
import os
import sys
from framestructure import *
import verbnetprepclasses

class VerbnetReader:

    """Class used to parse VerbNet and build its representation in memory.
    
    :var verbs: Dictionnary of 
            VerbnetFrame lists representing VerbNet.
    """
    
    def __init__(self, path):
        """Read VerbNet and fill verbs with its content.
        
        :param path: Path to VerbNet.
        :type path: str.
        
        """
        self.verbs = {}
        self.classes = {}
        
        # Debug data
        self.filename = ""
        self.unhandled = []

        for filename in os.listdir(path):
            if not filename[-4:] == ".xml": continue

            self.filename = filename
            root = ET.ElementTree(file=path+self.filename)
            self._handle_class(root.getroot(), [])

    
    def _handle_class(self, xml_class, parent_frames):
        """Parse one class of verbs and all its subclasses.
        
        :param xml_class: XML representation of the class of verbs.
        :type xml_class: xml.etree.ElementTree.Element.
        :param parent_frames: the frame inherited from the parent class.
        :type parent_frames: VerbnetFrame list.
        
        """
        frames = parent_frames[:]
        
        # Use the format of the vn/fn mapping
        vnclass = "-".join(xml_class.attrib["ID"].split('-')[1:])
        
        for xml_frame in xml_class.find("FRAMES"):
            frames.append(self._build_frame(xml_frame, vnclass))
        
        for xml_verb in xml_class.find("MEMBERS"):
            verb = xml_verb.attrib["name"]
            if not verb in self.verbs:
                self.verbs[verb] = []
                self.classes[verb] = []
                
            self.verbs[verb] += frames
            self.classes[verb].append(vnclass)
            
        for subclass in xml_class.find("SUBCLASSES"):
            self._handle_class(subclass, frames)
        
    def _build_frame(self, xml_frame, vnclass):
        """Parse one frame
        
        :param xml_frame: XML representation of the frame.
        :type xml_frame: xml.etree.ElementTree.Element.
        :param vnclass: The VerbNet class to which the frame belongs.
        :type vnclass: str.
        
        """
        # Extract the structure
        base_structure = xml_frame.find("DESCRIPTION").attrib["primary"]
        # Transform it into a list and replace "NP.xxx" by "NP"
        base_structure = [x.split(".")[0] for x in base_structure.split(" ")]
        
        # Lexeme at the beginning of a structure are capitalized.
        # We need to them to be completely lowercase to match them against syntax item.
        element = base_structure[0]
        if element[0].isupper and element.upper() != element:
            base_structure[0] = element.lower()
        
        structure = []
        role = [] 
        
        index_xml = 0
        syntax_data = xml_frame.find("SYNTAX")
        
        replacements = {
            "ADVP-Middle":[], "ADV-Middle":[],
            "NP-Fulfilling":["NP"],
            "S-Quote":["S"], "S_INF":["to", "S"],
            "v":["V"] # see snooze-40.4 for instance (intransitive verbs)
        }
        
        # Build the final structure from base_structure
        for element in base_structure:
            # Handle some syntax issues : see last entry of steal-10.5
            if element == "" or "\n" in element:
                continue
            # Handle simple replacements
            if element in replacements:
                structure = structure + replacements[element]
                continue
            # Handle the "a/b" syntax (which means "a" or "b")
            elif "/" in element:
                structure.append(element.split("/"))
            # Replace PP by "[preposition list] + NP"
            elif element == "PP":
                to_add = ""
                while to_add == "":
                    if index_xml >= len(syntax_data):
                        self.unhandled.append({
                            "file":self.filename,
                            "elem":"PP",
                            "data":"No syntax data found"
                        })
                        break
                    if syntax_data[index_xml].tag == "PREP":
                        to_add = self._handle_prep(syntax_data[index_xml])
                    if syntax_data[index_xml].tag == "LEX":
                        to_add = self._handle_lex(syntax_data[index_xml], base_structure)
                    index_xml += 1
                if to_add != "":
                    structure += [to_add, "NP"]
            # Everything else (NP, V, ...) is unmodified
            else:
                structure.append(element)
            
        # Fill the role list           
        for element in syntax_data:
            if ((not element.tag in ["VERB", "PREP", "LEX"]) and
                "value" in element.attrib
            ): 
                role.append(element.attrib["value"])

        return VerbnetFrame(structure, role, vnclass)
     
    def _handle_lex(self, xml, base_structure):
        """Choose wether or not to keep a <LEX> entry
        
        :param xml: The <LEX> entry.
        :type xml:xml.etree.ElementTree.Element.
        :param base_structure: The VerbNet primary structure.
        :type base_structure: str List.
        :returns: String -- the lexeme value if accepted, "" otherwise
        """
        
        # The lexeme is already mentionned in the primary structure
        # We don't want to add it a second time
        if xml.attrib["value"] in base_structure:
            return ""
        
        #for group in verbnetprepclasses.keywords:
        if xml.attrib["value"] in verbnetprepclasses.keywords:
            return xml.attrib["value"]

        self.unhandled.append({
            "file":self.filename,
            "elem":"LEX",
            "data":"Unhandled lexeme : {}".format(xml.attrib["value"])
        })
        
        return ""
                            
    def _handle_prep(self, xml):
        """Generate the list of acceptable preposition from a <PREP> entry
        
        :param xml: The <PREP> entry.
        :type xml:xml.etree.ElementTree.Element.
        :returns: String List -- the list of acceptable prepositions
        """
        for restr_group in xml:
            if restr_group.tag == "SELRESTRS":
                for restr in restr_group:
                    if (restr.attrib["Value"] == "+" 
                        and restr.attrib["type"] in verbnetprepclasses.prep
                    ):
                        return list(verbnetprepclasses.prep[restr.attrib["type"]])
                    else:
                        self.unhandled.append({
                            "file":self.filename,
                            "elem":"PREP",
                            "data":"SELRESTR {}={}".format(
                                restr.attrib["type"], restr.attrib["Value"])
                        })
            else:
                self.unhandled.append({
                    "file":self.filename,
                    "elem":"PREP",
                    "data":"Unknown restriction : {}".format(restr_group.tag)
                })                         
        if "value" in xml.attrib:
            return xml.attrib["value"].split(" ")
        else:
            return ""

        
class VerbnetReaderTest(unittest.TestCase):

    """Unit test class"""

    def test_global(self):
        path = "../data/verbnet-3.2/"
        reader = VerbnetReader(path)
        self.assertEqual(len(reader.verbs), 4154)

        test_verbs = ["sparkle", "employ", "break", "suggest", "snooze"]
        test_frames = [
            VerbnetFrame(
                ['there', 'V', 'NP', list(verbnetprepclasses.prep["loc"]), 'NP'],
                ['Theme', 'Location'], "43.1"),
            VerbnetFrame(
                ["NP", "V", "NP", "ADV"],
                ["Agent", "Theme"], "105"),
            VerbnetFrame(
                ["NP", "V"],
                ["Patient"], "45.1"),
            VerbnetFrame(
                ["NP", "V", "how", "to", "S"],
                ["Agent", "Topic"], "37.7"),
            VerbnetFrame(["NP", "V"], ["Agent"], "40.4")
        ]
        
        for verb, frame in zip(test_verbs, test_frames):
            self.assertIn(verb, reader.verbs)
            self.assertIn(frame, reader.verbs[verb])
        
        reader.verbs = {}
        root = ET.ElementTree(file=path+"separate-23.1.xml")
        reader._handle_class(root.getroot(), [])
        
        list1 = [  
            VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']),  
            VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']),
            VerbnetFrame(['NP', 'V'], ['Patient']),
            VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']),           
            VerbnetFrame(['NP', 'V'], ['Patient'])]           
        list2 = [VerbnetFrame(['NP', 'V', ['with'], 'NP'], ['Patient', 'Co-Patient'])]
        list3 = [VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient'])]
        expected_result = {
            'dissociate': list1+list2,
            'disconnect': list1+list2,
            'divide': list1+list3,
            'disassociate': list1,
            'disentangle': list1+list3, 
            'divorce': list1+list3, 
            'separate': list1+list2, 
            'segregate': list1+list3, 
            'part': list1+list2, 
            'differentiate': list1+list3, 
            'uncoil': list1, 
            'decouple': list1+list3, 
            'sever': list1, 
            'dissimilate': list1+list3
        }
        
        for verb in expected_result:
            if expected_result[verb] != reader.verbs[verb]:
                print("Error :")
                print(verb)
                for data in expected_result[verb]:
                    print(data)
                print("\n")
                for data in reader.verbs[verb]:
                    print(data)
                print("\n")
            
        self.assertEqual(reader.verbs, expected_result)
        
if __name__ == "__main__":
    unittest.main()

