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
        
        # Debug data
        self.filename = ""
        self.unhandled = []

        for filename in os.listdir(path):
            if not filename[-4:] == ".xml": continue
            print(filename)
            
            self.filename = filename
            root = ET.ElementTree(file=path+self.filename)
            self._handle_class(root, [])

    
    def _handle_class(self, xml_class, parent_frames):
        """Parse one class of verbs and all its subclasses.
        
        :param xml_class: XML representation of the class of verbs.
        :type xml_class: xml.etree.ElementTree.Element.
        :param parent_frames: the frame inherited from the parent class.
        :type parent_frames: VerbnetFrame list.
        
        """
        frames = parent_frames[:]
        for xml_frame in xml_class.find("FRAMES"):
            frames.append(self._build_frame(xml_frame))
        
        for xml_verb in xml_class.find("MEMBERS"):
            verb = xml_verb.attrib["name"]
            if not verb in self.verbs: self.verbs[verb] = []
            self.verbs[verb] += frames
            
        for subclass in xml_class.find("SUBCLASSES"):
            self._handle_class(subclass, frames)
        
    def _build_frame(self, xml_frame):
        """Parse one frame
        
        :param xml_frame: XML representation of the frame..
        :type xml_frame: xml.etree.ElementTree.Element.
        
        """
        structure = []
        role = [] 
              
        for element in xml_frame.find("SYNTAX"):
            to_add = ""
            if element.tag == "PREP":
                to_add = self._handle_prep(element)
            elif element.tag == "VERB":
                to_add = self._handle_verb(element)
            elif element.tag == "NP":
                to_add = self._handle_np(element)
            elif element.tag == "ADV":
                to_add = self._handle_adv(element)
            elif element.tag == "LEX":
                to_add = self._handle_lex(element)
            else:
                self.unhandled.append({
                    "file":self.filename,
                    "elem":element.tag,
                    "data":"Unknown element"
                })
            
            if to_add != "":                     
                structure.append(to_add)

                # If the element has a role, add it to the role list   
                if ((not (element.tag == "VERB" or element.tag == "PREP")) and
                    "value" in element.attrib
                ): 
                    role.append(element.attrib["value"])
                    
        return VerbnetFrame(structure, role)
        
    def _handle_adv(self, xml):
        if len(xml) != 0:
            self.unhandled.append({
                "file":self.filename,
                "elem":"ADV",
                "data":"Adverb had restrictions"
            })
        
        return ""
     
    def _handle_lex(self, xml):
        if len(xml) != 0:
            self.unhandled.append({
                "file":self.filename,
                "elem":"LEX",
                "data":"Lexeme had restrictions"
            })
        
        for group in verbnetprepclasses.keywords:
            if xml.attrib["value"] in group:
                return xml.attrib["value"]
                
        self.unhandled.append({
            "file":self.filename,
            "elem":"LEX",
            "data":"Unhandled lexeme : {}".format(xml.attrib["value"])
        })
        return ""
           
    def _handle_np(self, xml):
        for restr_group in xml:
            if restr_group.tag == "SYNRESTRS":
                for restr in restr_group:
                    # The NP should be plural- > ignored
                    if restr.attrib["Value"] == "+" and restr.attrib["type"] == "plural":
                        continue
                    else:
                        self.unhandled.append({
                            "file":self.filename,
                            "elem":"NP",
                            "data":"SYNRESTR {}={}".format(restr.attrib["type"], restr.attrib["Value"])
                        })
            elif restr_group.tag == "SELRESTRS":
                for restr in restr_group:
                    self.unhandled.append({
                        "file":self.filename,
                        "elem":"NP",
                        "data":"SELRESTRS {}={}".format(restr.attrib["type"], restr.attrib["Value"])
                    })
            else:
                self.unhandled.append({
                    "file":self.filename,
                    "elem":"NP",
                    "data":"Unknown restriction : {}".format(restr_group.tag)
                }) 
        return "NP"
                            
    def _handle_prep(self, xml):
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
            
    def _handle_verb(self, xml):
        if len(xml) != 0:
            self.unhandled.append({
                "file":self.filename,
                "elem":"V",
                "data":"Verb had restrictions"
            })
        
        return "V"

        
class VerbnetReaderTest(unittest.TestCase):

    """Unit test class"""

    def test_global(self):
        path = "../data/verbnet-3.2/"
        reader = VerbnetReader(path)
        self.assertEqual(len(reader.verbs), 4154)

        reader.verbs = {}
        root = ET.ElementTree(file=path+"separate-23.1.xml")
        reader._handle_class(root, [])
        
        expected_result = {
            'dissociate': [  
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']),  
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']),
                VerbnetFrame(['NP', 'V'], ['Patient']),
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']),           
                VerbnetFrame(['NP', 'V'], ['Patient']),           
                VerbnetFrame(['NP', 'V', ['with'], 'NP'], ['Patient', 'Co-Patient'])],
            'disconnect': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']),
                VerbnetFrame(['NP', 'V'], ['Patient']),  
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']),  
                VerbnetFrame(['NP', 'V', ['with'], 'NP'], ['Patient', 'Co-Patient'])],
            'divide': [ 
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']),
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']),
                VerbnetFrame(['NP', 'V'], ['Patient']),
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient'])],
            'disassociate': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']),
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']),
                VerbnetFrame(['NP', 'V'], ['Patient'])],
            'disentangle': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient'])], 
            'divorce': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient'])], 
            'separate': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['with'], 'NP'], ['Patient', 'Co-Patient'])], 
            'segregate': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient'])], 
            'part': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['with'], 'NP'], ['Patient', 'Co-Patient'])], 
            'differentiate': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient'])], 
            'uncoil': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient'])], 
            'decouple': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient'])], 
            'sever': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient'])], 
            'dissimilate': [
                VerbnetFrame(['NP', 'V', 'NP', ['from'], 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', ['from'], 'NP'], ['Patient', 'Co-Patient'])]
        }

        self.assertEqual(reader.verbs, expected_result)
        
        
if __name__ == "__main__":
    unittest.main()

