#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""FrameNet structure and tools"""

import xml.etree.ElementTree as ET
from collections import defaultdict
import options
import logging

namespaces = {'fn': 'http://framenet.icsi.berkeley.edu'} 

class FrameNet:
    """ The structure giving access to all FrameNet data

    Attributes:
    
    frames : dict ( string : FrameDefinition )
        a map frame name to FrameDefinition
    """

    def __init__(self):
        # nothing
        self.frames = {}

    def __eq__(self, other):
        return (isinstance(other, self.__class__))


class FrameDefinition:
    """A frame structure as defined by FrameNet

    Attributes:

    name : string
        the name of the frame, e.g.: Ingestion
    id : int
        The frame id
    definition : string
        the text difining the frame semantics
    creator: string
        (xml attribute cBy) creator id
    creationDate : string
        (xml attribute cDate) creation date
    semanticType : string
        name of the SemanticType of this frame. Can be None
    elements: dict ( string : FrameElement )
        a map associating frame element names to their definition
    relations: dict( string : list( string ) )
        a map associating relation type names to a set of
        frame names (e.g. {"Has Subframe(s)" : 
        [Activity_finish, Activity_ongoing, … ], … })
    lexicalUnits : dict( string : LexicalUnit )
        a map associating "lemma.pos_tag" to the details of this 
        lexical unit (LexicalUnit)
    """
    
    def __init__(self, name, id, definition, creator, creationDate, semanticType):
        # nothing
        self.name = name
        self.id = id
        self.definition = definition
        self.creator = creator
        self.creationDate = creationDate
        self.semanticType = semanticType
        self.elements = {}
        self.relations = {}
        self.lexicalUnits = {}
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.id == other.id)
    
    def __str__(self):
        return "FrameDefinition({}, {})".format(
            self.name, self.id)
    
    def __repr__(self):
        return ("FrameDefinition(name={}, id={})".format(self.name, self.id))


class SemanticType:
    """ A semantic type as defined by FrameNet"""

    def __init__(self, name, id):
        # nothing
        self.name = name
        self.id = id

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.id == other.id)


class FrameElement:
    """ A FrameNet frame element

    :var name: the name of the frame element, e.g.: Activity
    :var id: int. The frame element id
    :var abbreviation: the abbreviated frame element name
    :var coreType: express wether the frame element is a core element or not, etc.
    :var definition: the text difining the frame element semantics
    :var creator: (xml attribute cBy) creator id
    :var creationDate: (xml attribute cDate) creation date
    :var semanticType: name of the SemanticType of this frame. Can be None
    """

    def __init__(self, name, id, abbreviation, coreType, definition, 
                 creator, creationDate):
        self.name = name
        self.id = id
        self.abbreviation = abbreviation
        self.coreType = coreType
        self.definition = definition
        self.creator = creator
        self.creationDate = creationDate

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.id == other.id)


class LexicalUnit:
    """
    <lexUnit POS="v" name="découvrir.v" ID="108" nbocc="41" inhib_in_lexicon="false" lemma_is_annotated="true">
    <sentenceCount annotated="38"/>
    <otherlexUnit framename="Other_sense" ID="100664" annotatedsent="2"/>
    </lexUnit>
    <lexUnit status="Finished_Initial" incorporatedFE="Accoutrement" POS="N" name="bangle.n" ID="3364" lemmaID="2814" cBy="599" cDate="07/30/2001 02:07:47 PDT Mon">
    <definition>COD: a rigid ornamental band worn around the arm. </definition>
    <sentenceCount annotated="7" total="44"/>
    <lexeme order="1" headword="false" breakBefore="false" POS="N" name="bangle"/>
    </lexUnit>
    """

    def __init__(self, pos, name, id, nbOcc, inhibited, annotated, status, incorporatedFE, lemmaId, creator, creationDate, definition):
        # nothing
        self.pos = pos
        self.name = name
        self.id = id
        self.nbOcc = nbOcc
        self.inhibited = inhibited
        self.annotated = annotated
        self.lemmaId = lemmaId

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.id == other.id)


class FrameNetReader:
    """Class used to parse FrameNet and build its representation in memory.

    :var path: Path to FrameNet
    :var frameNet: the FrameNet instance to fill
    """
    
    def __init__(self, path, frameNet):
        """Read FrameNet and fill its content.
        
        :param path: Path to FrameNet
        :type path: pathlib.Path
        :param frameNet: the FrameNet instance to fill
        :type frameNet: FrameNet
        """

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(options.Options.loglevel)
        self.frameNet = frameNet

        if not list(path.glob('frame/*.xml')):
            raise Exception('FrameNet not found in {}! Did you clone with submodules?'.format(path))

        for filename in path.glob('frame/*.xml'):
            frame = self.loadFrame(filename)
            self.frameNet.frames[frame.name] = frame

    def loadFrame(self, filename):
        """Parse one frame.

        :param filename: the name of the file defining the frame
        :type filename: string
        """
        self.logger.debug("loadFrame {}".format(filename))
        root = ET.ElementTree(file=str(filename.resolve()))
        frameNode = root.getroot()
        if frameNode.tag.split('}')[1] != 'frame':
            raise Exception('File {} is not a frame xml representation. '
                            'Root tag is "{}" instead of "frame".'.format(
                                filename, 
                                frameNode.tag.split('}')[1]))
        semanticTypeNode = frameNode.find('fn:semType',namespaces)
        semanticType = None
        if semanticTypeNode: 
            semanticType = SemanticType(semanticTypeNode.attrib['name'],
                                        semanticTypeNode.attrib['ID'])
        frame = FrameDefinition(frameNode.attrib['name'], 
                                frameNode.attrib['ID'], 
                                self.loadDefinition(frameNode), 
                                frameNode.attrib['cBy'] if 'cBy' in frameNode.attrib else '',
                                frameNode.attrib['cDate'] if 'cDate' in frameNode.attrib else '',
                                semanticType)
        for feNode in frameNode.findall('fn:FE',namespaces):
            fe = self.loadFrameElement(feNode)
            frame.elements[fe.name] = fe
        
        for frameRelationNode in frameNode.findall('fn:frameRelation',namespaces):
            frame.relations = defaultdict(set)
            for relatedFrameNode in frameRelationNode.findall('fn:relatedFrame',namespaces):
                frame.relations[frameRelationNode.attrib['type']].add(relatedFrameNode.text)

        for lexUnitNode in frameNode.findall('fn:lexUnit',namespaces):
            lexUnit = self.loadLexUnit(lexUnitNode)
            frame.lexicalUnits[lexUnit.name] = lexUnit
            
        return frame

    def loadDefinition(self, node):
        definition = ''
        definitionNode = node.find('fn:definition',namespaces)
        if definitionNode:
            definition = definitionNode.text
        return definition
        
    def loadAttrib(self, node, attrib):
        result = ''
        if attrib in node.attrib:
            result = node.attrib[attrib]
        return result

    def loadFrameElement(self, feNode):
        """ Builds a Frame Element from the given xml element

        :arg feNode: the xml element from which to load the FE
        :return the new FrameElement
        """
        
        fe = FrameElement(self.loadAttrib(feNode, 'name'), 
                          self.loadAttrib(feNode,'ID'), 
                          self.loadAttrib(feNode,  'abbrev'), 
                          self.loadAttrib(feNode, 'coreType'), 
                          self.loadDefinition(feNode), 
                          self.loadAttrib(feNode, 'cBy'), 
                          self.loadAttrib(feNode,  'cDate'))
        return fe

    def loadLexUnit(self, lexUnitNode):
        """ Builds a Lexical Unit from the given xml element

        :arg lexUnitNode: the xml element from which to load the lexical unit
        :return the new LexicalUnit
        """

        lu = LexicalUnit(
            self.loadAttrib(lexUnitNode, 'POS'), 
            self.loadAttrib(lexUnitNode, 'name'), 
            self.loadAttrib(lexUnitNode, 'ID'), 
            self.loadAttrib(lexUnitNode, 'nbocc'), 
            self.loadAttrib(lexUnitNode, 'inhib_in_lexicon'), 
            self.loadAttrib(lexUnitNode, 'lemma_is_annotated'), 
            self.loadAttrib(lexUnitNode, 'status'), 
            self.loadAttrib(lexUnitNode, 'incorporatedFE'), 
            self.loadAttrib(lexUnitNode, 'lemmaID'), 
            self.loadAttrib(lexUnitNode, 'cBy'), 
            self.loadAttrib(lexUnitNode, 'cDate'), 
            self.loadDefinition(lexUnitNode))
        return lu
