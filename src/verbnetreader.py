#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Read VerbNet and build a list of allowed VerbNet frame for each verb"""

import unittest
import xml.etree.ElementTree as ET
import os
import sys
from framestructure import *

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
        
        for filename in os.listdir(path):
            if not filename[-4:] == ".xml": continue
            print(filename)
            root = ET.ElementTree(file=path+filename)
            self._handle_class(root, [])

    
    def _handle_class(self, xml_class, parent_frames):
        """Parse one class of verbs and all its subclasses.
        
        :param xml_class: XML representation of the class of verbs.
        :type xml_class: xml.etree.ElementTree.Element.
        :param parent_frames: the frame inherited from the parent class.
        :type parent_frames: 
            VerbnetFrame list.
        
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
            if element.tag == "PREP":
                for restr in element.find("SELRESTRS"):
                    print("Unhandled restriction for PREP : {} {}".format(
                            restr.attrib["type"], restr.attrib["Value"]))
                            
                if "value" in element.attrib:
                    structure.append(element.attrib["value"])
            elif element.tag == "VERB" and len(element) == 0:
                structure.append("V")
            elif element.tag == "NP":
                if element.find("SYNRESTRS") != None:
                    for restr in element.find("SYNRESTRS"):
                        if not (restr.attrib["Value"] == "+" and
                            restr.attrib["type"] == "plural"):
                               print("Unhandled restriction for NP : {} {}".format(
                                restr.attrib["type"], restr.attrib["Value"]))
                            
                structure.append("NP")
            elif element.tag == "ADV" and len(element) == 0:
                continue
            else:
                print("Unhandled element : {}".format(
                    element.tag), file=sys.stderr)
            
            # If the element has a role, add it to the role list   
            if ((not (element.tag == "VERB" or element.tag == "PREP")) and
                "value" in element.attrib
            ): 
                role.append(element.attrib["value"])

        return VerbnetFrame(structure, role)
        
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
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']),  
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']),
                VerbnetFrame(['NP', 'V'], ['Patient']),
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']),           
                VerbnetFrame(['NP', 'V'], ['Patient']),           
                VerbnetFrame(['NP', 'V', 'with', 'NP'], ['Patient', 'Co-Patient'])],
            'disconnect': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']),
                VerbnetFrame(['NP', 'V'], ['Patient']),  
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']),  
                VerbnetFrame(['NP', 'V', 'with', 'NP'], ['Patient', 'Co-Patient'])],
            'divide': [ 
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']),
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']),
                VerbnetFrame(['NP', 'V'], ['Patient']),
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient'])],
            'disassociate': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']),
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']),
                VerbnetFrame(['NP', 'V'], ['Patient'])],
            'disentangle': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient'])], 
            'divorce': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient'])], 
            'separate': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'with', 'NP'], ['Patient', 'Co-Patient'])], 
            'segregate': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient'])], 
            'part': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'with', 'NP'], ['Patient', 'Co-Patient'])], 
            'differentiate': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient'])], 
            'uncoil': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient'])], 
            'decouple': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient'])], 
            'sever': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient'])], 
            'dissimilate': [
                VerbnetFrame(['NP', 'V', 'NP', 'from', 'NP'], ['Agent', 'Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V', 'NP'], ['Agent', 'Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient']), 
                VerbnetFrame(['NP', 'V'], ['Patient']), 
                VerbnetFrame(['NP', 'V', 'from', 'NP'], ['Patient', 'Co-Patient'])]
        }

        self.assertEqual(reader.verbs, expected_result)
        
        
if __name__ == "__main__":
    unittest.main()

