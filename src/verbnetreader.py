#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Read VerbNet and build a list of allowed VerbNet frame for each verb"""

import unittest
import xml.etree.ElementTree as ET
import sys

from errorslog import errors
from verbnetframe import VerbnetOfficialFrame
from verbnetrestrictions import VNRestriction
import verbnetprepclasses
import paths


class VerbnetReader:

    """Class used to parse VerbNet and build its representation in memory.
    
    :var verbs: Dictionary of VerbnetOfficialFrame lists representing VerbNet.
    """
    
    def __init__(self, path, normalize = False):
        """Read VerbNet and fill verbs with its content.
        
        :param path: Path to VerbNet.
        :type path: pathlib.Path.
        :param normalize: Either stick to VerbNet content closely or make it
            easier for the frame matching to proceed.
        :type normalize: boolean.
        
        """
        
        self.normalize = normalize
        
        self.frames_for_verb = {}
        self.classes = {}
        self.roles = {}
        self.cnames = {}

        # Debug data
        self.filename = ""
        self.unhandled = []

        if not list(path.glob('*.xml')):
            raise Exception('VerbNet not found!')

        for filename in path.glob('*.xml'):
            root = ET.ElementTree(file=str(filename.resolve()))
            self.filename = str(filename)
            self._handle_class(root.getroot(), [], [], [])

        if self.normalize:
            return self._normalized()
    
    def _normalized(self):
        self.files = {}
        
        for verb, verb_data in self.frames_for_verb.items():
            for vnframe in verb_data:
                filename = self.cnames[vnframe.vnclass][:-4]
                
                if not filename in self.files: self.files[filename] = {
                    "children": [], "roles": set(), "members": [],
                    "frames": [], "name":vnframe.vnclass.split("-")[0]}
                    
                current_class = self.files[filename]
                if "-" in vnframe.vnclass:
                    for subclass in vnframe.vnclass.split("-")[1:]:
                        new_name = current_class["name"]+"-"+subclass
                        
                        matching_class = None
                        for child_class in current_class["children"]:
                            if child_class["name"] == new_name:
                                matching_class = child_class
                        if matching_class == None:
                            new_class = {
                                "children": [], "roles": set(), "members": [],
                                "frames": [], "name":new_name}
                            current_class["children"].append(new_class)
                            matching_class = new_class
                            
                        current_class = matching_class
                
                current_class["members"].append(verb)
                current_class["frames"].append(vnframe)
                for role in vnframe.roles:
                    current_class["roles"].add(next(role.__iter__()))
    
    def _handle_class(self, xml_class, parent_frames, role_list, restrictions):
        """Parse one class of verbs and all its subclasses.
        
        :param xml_class: XML representation of the class of verbs.
        :type xml_class: xml.etree.ElementTree.Element.
        :param parent_frames: the frame inherited from the parent class.
        :type parent_frames: VerbnetOfficialFrame list.
        
        """
        frames = parent_frames[:]
        role_list = role_list[:]
        restrictions = restrictions[:]
        
        vnclass = xml_class.attrib["ID"]
        self.cnames[vnclass] = self.filename
        
        for xml_role in xml_class.find("THEMROLES"):
            role_list.append(xml_role.attrib["type"])
            restrictions.append(
                VNRestriction.build_from_xml(xml_role.find("SELRESTRS")))
        
        self.roles[vnclass] = role_list

        for xml_frame in xml_class.find("FRAMES"):
            # work around a bug in VerbNet 3.2
            if xml_frame.find('DESCRIPTION').get('primary') == 'Passive':
                continue

            frames += self._build_frame(xml_frame, vnclass, role_list, restrictions)
        
        for xml_verb in xml_class.find("MEMBERS"):
            verb = xml_verb.attrib["name"]
            if not verb in self.frames_for_verb:
                self.frames_for_verb[verb] = []
                self.classes[verb] = []
                
            self.frames_for_verb[verb] += frames
            self.classes[verb].append(vnclass)
            
        for subclass in xml_class.find("SUBCLASSES"):
            self._handle_class(subclass, frames, role_list, restrictions)
       
    def _build_frame(self, xml_frame, vnclass, role_list, restrictions):
        """Parse one frame
        
        :param xml_frame: XML representation of the frame.
        :type xml_frame: xml.etree.ElementTree.Element.
        :param vnclass: The VerbNet class to which the frame belongs.
        :type vnclass: str.
        
        """
        # Extract the structure
        base_structure = xml_frame.find("DESCRIPTION").attrib["primary"]
        # Transform it into a list
        #base_structure = [x.split(".")[0] for x in base_structure.split(" ")]
        base_structure = base_structure.split(" ")
        
        # Lexeme at the beginning of a structure are capitalized.
        # We need to them to be completely lowercase to match them against syntax item.
        element = base_structure[0]
        if element[0].isupper() and element.split(".")[0].upper() != element.split(".")[0]:
            base_structure[0] = element.lower()
            
        syntax_data = xml_frame.find("SYNTAX")
        
        roles, structures = self._build_structure(
            base_structure, syntax_data, vnclass, role_list)

        role_restr = [[restrictions[role_list.index(x)] for x in y] for y in roles]
        
        result = [VerbnetOfficialFrame(y, x, vnclass, role_restrictions=z)
            for x, y, z in zip(roles, structures, role_restr)]
        
        if self.normalize:
            example = xml_frame.find("EXAMPLES/EXAMPLE").text
            semantics = self._build_semantics(xml_frame.find("SEMANTICS"))
            syntax_roles = self._format_syntax_roles(xml_frame.find("SYNTAX"))
            
            for frame in result:
                frame.example = example
                frame.semantics = semantics
                frame.syntax = syntax_roles
        
        return result
  
    def _build_structure(self, base_structure, syntax_data, vnclass, role_list):
        """ Build the final structure from base_structure
        
        :param base_structure: The base structure
        :type base_structure: str List
        :param syntax_data: The XML "SYNTAX" node
        :type syntax_data: xml.etree.ElementTree.Element
        :param vnclass: The VerbNet class of the frame
        :type vnclass: str
        :returns: (str | str List) List -- the final structure
        
        """
        structure = []
        roles = []

        index_xml = -1
        num_slot = 0

        replacements = {
            "ADVP-Middle":[], "ADV-Middle":[],
            "NP-Fulfilling":["NP"], "NP-Dative":["NP"],
            "S-Quote":["S"], "S_INF":["to", "S"]
        }

        previous_was_pp = False

        for i, full_element in enumerate(base_structure):
            full_element = full_element.split(".")
            element = full_element[0]

            # see snooze-40.4 for instance (intransitive verbs)
            # We cannot use :replacements because lower/upper case
            # is used to detect keywords
            if element == "v": element = "V"

            # Handle "PP S_ING": we must ignore the PP
            if element == "S_ING" and previous_was_pp:
                del roles[-1]
                del structure[-1]
            previous_was_pp = (element == "PP")
            
            # Make "that" optionnal
            if element == "that": element = "(#that)"
            if element == "#that": element = "that"
            
            # Handle optionnal elements
            if len(element) > 0 and element[0] == "(":
                base_structure_1 = base_structure[:]
                del base_structure_1[i]
                base_structure_2 = base_structure[:]
                base_structure_2[i] = element[1:-1]

                roles1, structure1 = self._build_structure(
                    base_structure_1, syntax_data, vnclass, role_list)
                roles2, structure2 = self._build_structure(
                    base_structure_2, syntax_data, vnclass, role_list)
                return (roles1 + roles2), (structure1 + structure2)
            
            # Handle some syntax issues : see last entry of steal-10.5
            if element == "" or "\n" in element:
                continue
            # Handle simple replacements
            if element in replacements:
                structure = structure + replacements[element]
            # Handle the "a/b" syntax (which means "a" or "b")
            elif "/" in element:
                structure.append(set(element.split("/")))
            # Replace PP by "{preposition set} + NP"
            elif element == "PP":
                new_index, prep = self._read_syntax_data(
                    index_xml, syntax_data, "keyword", base_structure)
                if new_index == -1:
                    self.unhandled.append({
                        "file":self.filename,
                        "elem":"PP",
                        "data":"No syntax data found"
                    })
                    if len(full_element) > 1 and full_element[1] == "location":
                        structure += [verbnetprepclasses.prep["loc"], "NP"]
                    else:
                        structure += [verbnetprepclasses.all_preps, "NP"]
                else:
                    index_xml = new_index
                    structure += [prep, "NP"]
            # Everything else (NP, V, ...) is unmodified
            else:
                structure.append(element)

            search = element
            if search[0].islower(): search = "keyword"
            
            # Look for a matching element in SYNTAX
            # and check whether we can find an unexpected keyword to add,
            # between our current position and the matching element
            new_index, keyword = self._read_syntax_data(
                index_xml, syntax_data, search, base_structure)
            if keyword != "" and search != "keyword":
                structure.insert(-1, keyword)
            if new_index != -1:
                index_xml = new_index
            
            if VerbnetOfficialFrame._is_a_slot(element): roles.append(None)

            if len(full_element) > 1:
                potential_role = "-".join([x.title() for x in full_element[1].split('-')])
                if potential_role in role_list:
                    roles[num_slot - 1] = potential_role

        # Fill the role list
        i = 0
        for element in syntax_data:
            if ((not element.tag in ["VERB", "PREP", "LEX"]) and
                "value" in element.attrib
            ):
                if i >= len(roles):
                    roles.append(None)
                    self.unhandled.append({
                        "file":self.filename,
                        "elem":"\\",
                        "data":"Too many roles in the syntax"
                    })
                else:
                    if roles[i] != None and roles[i] != element.attrib["value"]:
                        self.unhandled.append({
                        "file":self.filename,
                        "elem":"\\",
                        "data":"Conflict between roles indicated in syntax and structure"
                        })
                    else:
                        roles[i] = element.attrib["value"]
                i += 1
             
        while len(roles) > 0 and roles[-1] == None: del roles[-1]
            
        return [roles], [structure]
    
    def _read_syntax_data(self, index_xml, syntax_data, elem, base_structure):
        """ Look for a node of SYNTAX that match the current element
        and tells whether a keyword was found between the old and new position
        
        :param index_xml: The current position
        :type index_ml: int
        :param syntax_data: The XML "SYNTAX" node
        :type syntax_data: xml.etree.ElementTree.Element
        :param elem: The element to look for (VerbNet syntax)
        :type elem: str
        :param base_structure: The frame base structure (for _handle_lex)
        :type base_structure: str List
        :returns: (int, str) -- the new position and a keyword if one is found
        
        """
        special_tags = {"V":["VERB"], "keyword":["PREP", "LEX"]}
        stop_tags = ["NP", "V"]
        
        expected_tags = ["NP"]
        if len(elem) >= 3 and elem[0:3] == "ADV": expected_tags = ["ADV"]
        if len(elem) >= 3 and elem[0:3] == "ADJ": expected_tags = ["ADJ", "NP"]
        if elem in special_tags: expected_tags = special_tags[elem]
        
        found = False
        keyword = ""
        index_xml += 1
        
        while index_xml < len(syntax_data):
            if syntax_data[index_xml].tag == "PREP":
                keyword = self._handle_prep(syntax_data[index_xml])
            if syntax_data[index_xml].tag == "LEX":
                keyword = self._handle_lex(syntax_data[index_xml], base_structure)
                
            if syntax_data[index_xml].tag in expected_tags:
                found = True
                break
            if syntax_data[index_xml].tag in stop_tags and elem != "V":
                break
            index_xml += 1
            
        if not found:
            return -1, ""
            
        return index_xml, keyword
        
    def _handle_lex(self, xml, base_structure):
        """Choose wether or not to keep a <LEX> entry
        
        :param xml: The <LEX> entry.
        :type xml:xml.etree.ElementTree.Element.
        :param base_structure: The VerbNet primary structure.
        :type base_structure: str List.
        :returns: String the lexeme value if accepted, "" otherwise

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
        :returns: String List - the list of acceptable prepositions

        """
        for restr_group in xml:
            if restr_group.tag == "SELRESTRS":
                for restr in restr_group:
                    if (restr.attrib["Value"] == "+"
                        and restr.attrib["type"] in verbnetprepclasses.prep
                    ):
                        return verbnetprepclasses.prep[restr.attrib["type"]]
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
            return set(xml.attrib["value"].split(" "))
        else:
            return ""
    
    def _format_syntax_roles(self, xml_syntax):
        result = []
        for node in xml_syntax:
            if node.tag == "NP":
                result.append(node.get("value"))
            elif node.tag == "VERB":
                result.append("V")
            elif node.tag == "LEX":
                result.append(node.get("value"))
            elif node.tag == "PREP":
                if node.get("value"):
                    result.append("{{{}}}".format(node.get("value")))
                else:
                    restr = node.find("SELRESTRS/SELRESTR")
                    result.append("{{{{{}{}}}}}".format(restr.get("Value"), restr.get("type")))

            if node.find("SYNRESTRS"):
                restr = node.find("SYNRESTRS/SYNRESTR")
                result.append("<{}{}>".format(restr.get("Value"), restr.get("type")))

        return " ".join(result)

    def _build_semantics(self, xml_semantics):
        pred_strings = []
        for pred in xml_semantics.findall("PRED"):
            pred_string = "{}({})".format(
                pred.get("value"),
                ", ".join([arg.get("value") for arg in pred.findall("ARGS/ARG")])
            )
            if pred.get("bool") == "!":
                pred_string = "not({})".format(pred_string)

            pred_strings.append(pred_string)

        return " ".join(pred_strings)
        
class VerbnetReaderTest(unittest.TestCase):
    """Unit test class"""
    
    def test_global(self):
        reader = VerbnetReader(paths.VERBNET_PATH)
        self.assertEqual(len(reader.frames_for_verb), 4402)

        test_verbs = ["sparkle", "employ", "break", "suggest", "snooze"]
        test_frames = [
            VerbnetOfficialFrame(
                ['there', 'V', 'NP', verbnetprepclasses.prep["loc"], 'NP'],
                ['Theme', 'Location'],
                "light_emission-43.1", []),
            VerbnetOfficialFrame(
                ["NP", "V", "NP", "ADV"],
                ["Agent", "Theme"],
                "use-105", []),
            VerbnetOfficialFrame(
                ["NP", "V"],
                ["Patient"],
                "break-45.1", []),
            VerbnetOfficialFrame(
                ["NP", "V", "how", "to", "S"],
                ["Agent", "Topic"],
                "say-37.7", []),
            VerbnetOfficialFrame(
                ["NP", "V"],
                ["Agent"],
                "snooze-40.4", [])
        ]
        restrictions_str = {
            "sparkle":["(NOT animate)", "NORESTR"],
            "employ":["(animate) OR (organization)", "NORESTR"],
            "break":["solid"],
            "suggest":["(animate) OR (organization)", "communication"],
            "snooze":["animate"]
        }
        
        for verb, frame in zip(test_verbs, test_frames):
            self.assertIn(verb, reader.frames_for_verb)
            self.assertIn(frame, reader.frames_for_verb[verb])
            vnframe = reader.frames_for_verb[verb][reader.frames_for_verb[verb].index(frame)]
            self.assertEqual(
                [str(x) for x in vnframe.role_restrictions], restrictions_str[verb])
        
        reader.frames_for_verb = {}
        root = ET.ElementTree(file=str(paths.VERBNET_PATH / "separate-23.1.xml"))
        reader._handle_class(root.getroot(), [], [], [])
        
        list1 = [
            VerbnetOfficialFrame(
                ['NP', 'V', 'NP', {'from'}, 'NP'],
                ['Agent', 'Patient', 'Co-Patient'],
                "separate-23.1", []),
            VerbnetOfficialFrame(
                ['NP', 'V', 'NP'],
                ['Agent', 'Patient'],
                "separate-23.1", []),
            VerbnetOfficialFrame(
                ['NP', 'V'],
                ['Patient'],
                "separate-23.1", []),
            VerbnetOfficialFrame(
                ['NP', 'V', {'from'}, 'NP'],
                ['Patient', 'Co-Patient'],
                "separate-23.1", []),
            VerbnetOfficialFrame(
                ['NP', 'V'],
                ['Patient'],
                "separate-23.1", [])]
        list2 = [VerbnetOfficialFrame(['NP', 'V', {'from'}, 'NP'], ['Patient', 'Co-Patient'], "separate-23.1-1", [])]
        list3 = [VerbnetOfficialFrame(['NP', 'V', {'with'}, 'NP'], ['Patient', 'Co-Patient'], "separate-23.1-2", [])]
        expected_result = {
            'dissociate': list1+list3,
            'disconnect': list1+list3,
            'divide': list1+list2,
            'disassociate': list1,
            'disentangle': list1+list2,
            'divorce': list1+list2,
            'separate': list1+list3,
            'segregate': list1+list2,
            'part': list1+list3,
            'differentiate': list1+list2,
            'uncoil': list1,
            'decouple': list1+list2,
            'sever': list1,
            'dissimilate': list1+list2
        }
        
        for verb in expected_result:
            if expected_result[verb] != reader.frames_for_verb[verb]:
                print("Error :")
                print(verb)
                for data in expected_result[verb]:
                    print(data)
                print("\n")
                for data in reader.frames_for_verb[verb]:
                    print(data)
                print("\n")
            
        self.assertEqual(reader.frames_for_verb, expected_result)

def init_verbnet(path):
    print("Loading VerbNet data...")
    reader = VerbnetReader(path)
    errors["vn_parsing"] = reader.unhandled
    return reader.frames_for_verb, reader.classes
