#!/usr/bin/env python3

from xml.etree import ElementTree as ET
import glob
import collections
from distutils.version import LooseVersion
import paths


classes_for_predicate = collections.defaultdict(list)


class VerbNetXMLException(Exception):
    def __init__(self, err):
        self.err = err

    def __str__(self):
        return self.err


class Class:
    """A VerbNet class, including members, roles and frames"""

    def __init__(self, vnclass_xml, parent=None):
        self.parent = parent
        self.vn_id = vnclass_xml.get('ID')
        self.members = [m.get('name') for m in vnclass_xml.findall('MEMBERS/MEMBER')]

        for m in self.members: classes_for_predicate[m].append(self)

        self.frames = []
        for vnframe_xml in vnclass_xml.findall('FRAMES/FRAME'):
            self.frames.append(Frame(vnframe_xml))

        self.subclasses = []
        for subclass in vnclass_xml.findall('SUBCLASSES/VNSUBCLASS'):
            self.subclasses.append(Class(subclass, parent=self))

    def __repr__(self):
        return 'verbnet.Class({})'.format(self.vn_id)

    def all_frames(self):
        """Returns all Frames which apply to this subclass"""
        if self.parent == None:
            return self.frames
        else:
            return self.frames + self.parent.all_frames()


class Frame:
    """A representation of a frame syntactic structure

    :var syntax:
    :var semantics: str -- The semantic as it appears in VerbNet
    :var example: str -- An example sentence that illustrates the frame
    """

    def __init__(self, vnframe_xml):
        self.example = ' '.join([
            e.text for e in vnframe_xml.findall('EXAMPLES/EXAMPLE')])

        self.semantics = self._build_semantics(vnframe_xml.find('SEMANTICS'))

        self.syntax = self._build_syntax(vnframe_xml.find('SYNTAX'))

    def __repr__(self):
        return str(self.syntax)

    def __str__(self):
        result_lines = []
        result_lines.append(str(self.syntax))
        result_lines.append('    {}'.format(self.example))
        result_lines.append('    {}'.format(self.semantics))
        return '\n'.join(result_lines)

    def _build_semantics(self, vnsemantics_xml):
        """
        Given VerbNet semantics in XML, return a text string containing those
        predicates and their arguments
        """

        pred_string_list = []
        for vnpred_xml in vnsemantics_xml.findall('PRED'):
            predicate = vnpred_xml.get('value')
            args = [arg.get('value') for arg in vnpred_xml.findall('ARGS/ARG')]
            pred_string = '{}({})'.format(predicate, args)

            if vnpred_xml.get('bool') == '!':
                pred_string = 'not({})'.format(pred_string)

            pred_string_list.append(pred_string)

        return ' '.join(pred_string_list)

    def _build_syntax(self, vnsyntax_xml):
        syntax = Syntax()
        for elem in vnsyntax_xml:
            if elem.tag == 'NP':
                assert elem.get('value') is not None
                syntax.append({
                    'type': elem.tag,
                    'role': elem.get('value'),
                })
            elif elem.tag in ['PREP', 'LEX']:
                if elem.tag == 'PREP' and elem.find('SELRESTRS/SELRESTR') is not None:
                    syntax.append(self._build_prep_selrestrs(elem))
                else:
                    if not elem.get('value'):
                        raise VerbNetXMLException('No value attribute for \'PREP\'')
                    syntax.append({
                        'type': elem.tag,
                        'value': elem.get('value'),
                    })
            elif elem.tag == 'VERB':
                syntax.append({'type': 'V'})
            elif elem.tag in ['ADV', 'ADJ']:
                syntax.append({'type': elem.tag})
            else:
                raise Exception('Impossible SYNTAX child {}.'.format(elem.tag))

        return syntax

    def _build_prep_selrestrs(self, vnprep_xml):
        selrestr_parts = []
        for selrestr in vnprep_xml.findall('SELRESTRS/SELRESTR'):
            selrestr_parts.append('{{{{{}{}}}}}'.format(
                selrestr.get('Value'), selrestr.get('type')))

        return {'type': 'PREP', 'value': ' | '.join(selrestr_parts)}


class Syntax(collections.UserList):
    """
    A representation of a SYNTAX element in Verbnet

    Each item of this list can be NP (in which cas it has a role, a PRED or LEX
    (in which case it has a value), and a ADV, ADJ or V (no value).

    This is basically a list + __str__
    """

    def _string_of_syntax(self, s):
        if s['type'] == 'NP':
            return '{}.{}'.format(s['type'], s['role'])
        elif s['type'] in ['PREP', 'LEX']:
            return s['value']
        elif s['type'] in ['ADV', 'ADJ', 'V']:
            return s['type']
        else:
            raise Exception('Unknown type {}!'.format(s['type']))

    def __str__(self):
        return ' '.join([self._string_of_syntax(part) for part in self.data])

    def __repr__(self):
        return str(self)

# If we're loading this module, this is because we want to load VerbNet
for filename in sorted(glob.glob(paths.VERBNET_PATH + '/*.xml'),
                       key=lambda v: LooseVersion(v.split('-')[1][:-4])):
    vnclass_xml = ET.ElementTree(file=filename).getroot()
    Class(vnclass_xml)
