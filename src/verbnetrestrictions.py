#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

class VNRestriction:

    """ A semantic condition associated to a role in VerbNet
    
    :var type: str | None -- The semantic class associated with the restriction
    :var children: VNRestriction List -- For compound condition, the list of children
    :var logical_rel: str -- The logical relation between the children
    
    """
    
    # List of possible values for :type
    possible_types = {
        "abstract", "animal", "animate", "body_part", "comestible",
        "communication", "concrete", "currency", "elongated", "force",
        "garment", "human", "int_control", "location", "machine", "nonrigid",
        "organization", "plural", "pointy", "refl", "region", "scalar", "solid",
        "sound", "substance", "time", "vehicle"
    }
    
    def __init__(self, restr_type=None, children=[],
        logical_rel=None
    ):
        if restr_type != None and not restr_type in VNRestriction.possible_types:
            raise Exception("VNRestriction : unhandled restriction "+restr_type)
        
        for child in children:
            if not isinstance(child, self.__class__):
                raise Exception("VNRestriction : invalid child")
            
        self.type = restr_type
        self.children = children
        self.logical_rel = logical_rel
    
    def __str__(self):
        if self._is_empty_restr():
            return "NORESTR"
        if self.logical_rel == None:
            return self.type
        if self.logical_rel == "NOT":
            return "(NOT "+str(self.children[0])+")"
        return "("+(") "+self.logical_rel+" (").join([str(x) for x in self.children])+")"
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        # Technically, this does not return True for any couple of equivalent
        # restrictions, such as (NOT(NOT a AND NOT b)), (a OR b), but this
        # does not matter since VerbNet logic statements are very simple
        
        if not isinstance(other, self.__class__): return False
        if self.type != None or other.type != None: return self.type == other.type
        if self.logical_rel != other.logical_rel: return False
        
        # We cannot use Python's buildin unordered sets, since
        # VNRestriction are not hashable
        return (all([x in other.children for x in self.children]) and
                all([x in self.children for x in other.children]))
    
    def _is_empty_restr(self):
        return self.logical_rel == "AND" and len(self.children) == 0
    
    def _simple_match(self, word):
        """ Not implemented """
        pass
    
    def match(self, word):
        if self.logical_rel == None:
            return self._simple_match(word)
        elif self.logical_rel == "NOT":
            return not self.children[0].match(word)
        elif self.logical_rel == "AND":
            return all([x.match(word) for x in self.children])
        elif self.logical_rel == "OR":
            return any([x.match(word) for x in self.children])
        else:
            raise Exception("VNRestriction.match : invalid logical relation")

    def get_atomic_restrictions(self):
        """ Return the list of basic restrictions needed to compute this restriction """
        if self._is_empty_restr(): return set()
        if len(self.children) == 0: return {self.type}
        
        result = set()
        for child in self.children:
            result |= child.get_atomic_restrictions()
        return result
    
    @staticmethod
    def _build_keyword(r1, r2, kw):
        if r1._is_empty_restr(): return r2
        if r2._is_empty_restr(): return r1
        
        if r1.logical_rel == kw and r2.logical_rel == kw:
            return VNRestriction(children=r1.children + r2.children, logical_rel=kw)
        if r1.logical_rel == kw:
            return VNRestriction(children=r1.children + [r2], logical_rel=kw)
        if r2.logical_rel == kw:
            return VNRestriction(children=[r1] + r2.children, logical_rel=kw)
        else:
            return VNRestriction(children=[r1, r2], logical_rel=kw)
        
    @staticmethod
    def build(restr_type):
        return VNRestriction(restr_type=restr_type)

    @staticmethod
    def build_and(r1, r2):
        return VNRestriction._build_keyword(r1, r2, "AND")
    
    @staticmethod
    def build_or(r1, r2):
        return VNRestriction._build_keyword(r1, r2, "OR")
    
    @staticmethod
    def build_not(r):
        return VNRestriction(children=[r], logical_rel="NOT")
        
    @staticmethod
    def build_empty():
        return VNRestriction(children=[], logical_rel="AND")
    
    @staticmethod 
    def build_from_xml(xml):
        disjunction = "logic" in xml.attrib and xml.attrib["logic"] == "or"
        
        restr_list = []
        for xml_restr in xml:
            if xml_restr.tag == "SELRESTRS":
                restr_list.append(VNRestriction.build_from_xml(xml_restr))
            elif xml_restr.tag == "SELRESTR":
                restr = VNRestriction.build(xml_restr.attrib["type"])
                if xml_restr.attrib["Value"] == "-":
                    restr_list.append(VNRestriction.build_not(restr))
                else:
                    restr_list.append(restr)
            else:
                raise Exception("Unknown tag in restrictions : "+xml_restr.tag)
        
        result = VNRestriction.build_empty()
        for i, restr in enumerate(restr_list):
            if i == 0:
                result = restr
            elif disjunction:
                result = VNRestriction.build_or(result, restr)
            else:
                result = VNRestriction.build_and(result, restr)
        return result


class VNRestrictionTest(unittest.TestCase):

    """Unit test class"""

    def test_restrictions(self):
        restr1 = VNRestriction.build("human")
        restr2 = VNRestriction.build("animal")
        restr3 = VNRestriction.build("solid")
        
        restr4 = VNRestriction.build_and(restr1, restr2)
        restr5 = VNRestriction.build_and(restr2, restr3)
        restr6 = VNRestriction.build_and(restr4, restr3)
        restr7 = VNRestriction.build_and(restr5, restr1)
        restr8 = VNRestriction.build_empty()
        restr8 = VNRestriction.build_or(restr8, restr7)
        
        self.assertEqual(restr6, restr7)
        self.assertNotEqual(restr4, restr5)
        subrestr = restr6.get_atomic_restrictions()
        self.assertEqual(subrestr, set(["human", "animal", "solid"]))
        self.assertTrue(str(restr8) == str(restr7))
        
if __name__ == "__main__":
    unittest.main()
