#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Read VerbNet and build a list of allowed VerbNet frame for each verb"""

import xml.etree.ElementTree as ET

from errorslog import errors
from verbnetframe import VerbnetOfficialFrame
from verbnetrestrictions import VNRestriction
import verbnetprepclasses

import options
import logging
logger = logging.getLogger(__name__)
logger.setLevel(options.Options.loglevel)


class VerbnetReader:

    """Class used to parse VerbNet and build its representation in memory.

    :var verbs: Dictionary of VerbnetOfficialFrame lists representing VerbNet.
    """

    def __init__(self, path):
        """Read VerbNet and fill verbs with its content.

        :param path: Path to VerbNet.
        :type path: pathlib.Path.
        """

        self.frames_for_verb = {}
        self.classes = {}
        self.roles = {}
        self.cnames = {}

        # Debug data
        self.filename = ""
        self.unhandled = []

        if not list(path.glob('*-[0-9]*.xml')):
            raise Exception('VerbNet not found in {}! Did you clone with submodules?'.format(path))

        for filename in path.glob('*.xml'):
            root = ET.ElementTree(file=str(filename.resolve()))
            self.filename = str(filename)
            self._handle_class(root.getroot(), [], [], [])

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
            if xml_role.find("SELRESTRS"):
                restrictions.append(
                    VNRestriction.build_from_xml(xml_role.find("SELRESTRS")))

        self.roles[vnclass] = role_list

        for xml_frame in xml_class.find("FRAMES"):
            # work around a bug in VerbNet 3.2
            if xml_frame.find('DESCRIPTION').get('primary') == 'Passive':
                continue
            #logger.debug("VerbnetReader._handle_class {} {}".format(xml_frame, vnclass))
            frames.append(self._build_frame(xml_frame, vnclass, role_list, restrictions))

        for xml_verb in xml_class.find("MEMBERS"):
            verb = xml_verb.attrib["name"]
            if verb not in self.frames_for_verb:
                #logger.debug("_handle_class add member {}".format(verb))
                self.frames_for_verb[verb] = []
                self.classes[verb] = []

            self.frames_for_verb[verb] += frames
            self.classes[verb].append(vnclass)

        if xml_class.find("SUBCLASSES"):
            for subclass in xml_class.find("SUBCLASSES"):
                self._handle_class(subclass, frames, role_list, restrictions)

    def _merge_syntax(self, primary_structure, roles, role_restrictions):
        #logger.debug('_merge_syntax {}, {}, {}'.format(primary_structure,roles,role_restrictions))
        new_syntax = []
        role_index = 0
        for elem in primary_structure:
            if role_index >= len(roles):
                new_syntax.append({'elem': elem})
            elif elem in ['NP', 'ADJP', 'ADVP', 'S', 'S_ING']:
                try:
                    if role_index < len(role_restrictions):
                        new_syntax.append({
                            'elem': elem,
                            'role': roles[role_index],
                            'restr': role_restrictions[role_index]})
                    else:
                        new_syntax.append({
                            'elem': elem,
                            'role': roles[role_index],
                            'restr': None})
                    role_index += 1
                    continue
                except:
                    logger.error("Exception on role_index {}".format(role_index))
            else:
                new_syntax.append({'elem': elem})

        #logger.debug('_merge_syntax result: {}'.format(new_syntax))
        return new_syntax

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
        base_structure = base_structure.split(" ")

        # Lexeme at the beginning of a structure are capitalized.
        # We need to them to be completely lowercase to match them against syntax item.
        element = base_structure[0]
        if element[0].isupper() and element.split(".")[0].upper() != element.split(".")[0]:
            base_structure[0] = element.lower()

        syntax_data = xml_frame.find("SYNTAX")

        roles, structure = self._build_structure(
            base_structure, syntax_data, vnclass, role_list)
        role_restr = []
        #logger.debug('_build_frame {}, {}, {}, {}'.format(vnclass,roles,role_list,restrictions))
        for x in roles:
            if x in role_list and len(restrictions) > role_list.index(x):
                role_restr.append(restrictions[role_list.index(x)])

        syntax = self._merge_syntax(structure, roles, role_restr)
        result = VerbnetOfficialFrame(vnclass, syntax)

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

        for i, full_element in enumerate(base_structure):
            full_element = full_element.split(".")
            element = full_element[0]

            for end in ['-Middle', '-Dative', '-dative', '-Result',
                        '-Conative', '-Fulfilling', '-Quote']:
                if element.endswith(end):
                    element = element[:-len(end)]

            #if '-' in element:
                #raise Exception('Unexpected {} in {}'.format(element, vnclass))

            # TODO handle adverbial phrases and adverbs?
            if element in ['ADV', 'ADVP']:
                pass
            # S_INF -> to S
            elif element == 'S_INF':
                structure = structure + ['to', 'S']
            # Handle the "whether/if" syntax (which means "whether" or "if")
            elif "/" in element:
                structure.append(set(element.split("/")))
            # Replace PP by "{preposition set} + NP"
            elif element == "PP":
                new_index, prep = self._read_syntax_data(
                    index_xml, syntax_data, "keyword", base_structure)
                if new_index == -1:
                    self.unhandled.append({
                        "file": self.filename,
                        "elem": "PP",
                        "data": "No syntax data found"
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
            if len(search) > 0 and search[0].islower():
                search = "keyword"

            # Look for a matching element in SYNTAX
            # and check whether we can find an unexpected keyword to add,
            # between our current position and the matching element
            new_index, keyword = self._read_syntax_data(
                index_xml, syntax_data, search, base_structure)
            if keyword != "" and search != "keyword":
                structure.insert(-1, keyword)
            if new_index != -1:
                index_xml = new_index

            if VerbnetOfficialFrame._is_a_slot({'elem': element}):
                roles.append(None)

            if len(full_element) > 1:
                potential_role = "-".join([x.title() for x in full_element[1].split('-')])
                if potential_role in role_list:
                    roles[num_slot - 1] = potential_role

        # Fill the role list
        i = 0
        for element in syntax_data:
            if ((element.tag not in ["VERB", "PREP", "LEX"]) and
                    "value" in element.attrib):

                if i >= len(roles):
                    roles.append(None)
                    self.unhandled.append({
                        "file": self.filename,
                        "elem": "\\",
                        "data": "Too many roles in the syntax"
                    })
                else:
                    if roles[i] is not None and roles[i] != element.attrib["value"]:
                        self.unhandled.append({
                        "file": self.filename,
                        "elem": "\\",
                        "data": "Conflict between roles indicated in syntax and structure"
                        })
                    else:
                        roles[i] = element.attrib["value"]
                i += 1

        while len(roles) > 0 and roles[-1] is None:
            del roles[-1]

        return roles, structure

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
        special_tags = {"V": ["VERB"], "keyword": ["PREP", "LEX"]}
        stop_tags = ["NP", "V"]

        expected_tags = ["NP"]
        if len(elem) >= 3 and elem[0:3] == "ADV":
            expected_tags = ["ADV"]
        elif len(elem) >= 3 and elem[0:3] == "ADJ":
            expected_tags = ["ADJ", "NP"]
        elif elem in special_tags:
            expected_tags = special_tags[elem]

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

        if xml.attrib["value"] in verbnetprepclasses.keywords:
            return xml.attrib["value"]

        self.unhandled.append({
            "file": self.filename,
            "elem": "LEX",
            "data": "Unhandled lexeme : {}".format(xml.attrib["value"])
        })

        return ""

    def _handle_prep(self, xml):
        """Generate the list of acceptable preposition from a <PREP> entry

        :param xml: The <PREP> entry.
        :type xml:xml.etree.ElementTree.Element.
        :returns: String List - the list of acceptable prepositions

        """
        #logger.debug('_handle_prep {}'.format(xml))
        for restr_group in xml:
            if restr_group.tag == "SELRESTRS":
                for restr in restr_group:
                    #logger.debug('restriction {}'.format(restr))
                    if (restr.attrib["Value"] == "+"
                            and restr.attrib["type"] in verbnetprepclasses.prep):
                        return verbnetprepclasses.prep[restr.attrib["type"]]
                    else:
                        self.unhandled.append({
                            "file": self.filename,
                            "elem": "PREP",
                            "data": "SELRESTR {}={}".format(
                                restr.attrib.get("type"), restr.attrib["Value"])
                        })
            else:
                self.unhandled.append({
                    "file": self.filename,
                    "elem": "PREP",
                    "data": "Unknown restriction : {}".format(restr_group.tag)
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


def init_verbnet(path):
    logger = logging.getLogger(__name__)
    logger.setLevel(options.Options.loglevel)
    logger.info("Loading VerbNet data from {}...".format(path))
    reader = VerbnetReader(path)
    errors["vn_parsing"] = reader.unhandled
    return reader.frames_for_verb, reader.classes
