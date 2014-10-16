#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class NoHashDefaultDict:

    """Basic reimplementation of defaultdict objects that tolerate indexation
    by non-hashable objects.
    """

    def __init__(self, builder):
        """ Same constructor as collections.defaultdict """
        
        self.keys = []
        self.values = []
        self.builder = builder
        
    def __getitem__(self, key):
        try:
            return self.values[self.keys.index(key)]
        except Exception:
            self.keys.append(key)
            self.values.append(self.builder())
            return self.values[-1]
    
    def __iter__(self):
        return self.keys.__iter__()

class VNRestriction:

    """A semantic condition associated to a role in VerbNet
    
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
        """Private constructor. Use the build* static methods to instanciate 
        VNRestricitons.
        Takes care of deleting children that could occurs several time in the
        list given as argument.
        
        """
        
        if restr_type != None and not restr_type in VNRestriction.possible_types:
            raise Exception("VNRestriction : unhandled restriction "+restr_type)
        
        # See what children can be discarded (because they occur several times)
        keep = [True] * len(children)
        for i, child in enumerate(children):
            if not isinstance(child, self.__class__):
                raise Exception("VNRestriction : invalid child")
            keep[i] = (children.index(child) == i)
        
        self.type = restr_type
        self.children = [children[i] for i in range(len(children)) if keep[i]]
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
        """ Tell whether this is the empty restriciotn """
        return self.logical_rel == "AND" and len(self.children) == 0
    
    def match_score(self, word, data):
        """Compute an affinity score between a given word and this restriction.
        
        :param word: The word
        :type word: str
        :param data: The gathered relations between restrictions and words
        :type data: (VNRestriction -> (str Counter)) NoHashDefaultDict
        
        """
        
        # Give a very small score for matching NORESTR
        if self._is_empty_restr(): return 1 / 100
    
        base_score = 0
        if word in data[self]: base_score = data[self][word]
        
        if self.logical_rel == None:
            children_score = 0
        elif self.logical_rel == "NOT":
            children_score = (-1) * self.children[0].match_score(word, data)
            
            # Attribute a score of 1 for finding no match
            if children_score == 0: children_score = 1
        elif self.logical_rel == "OR":
            children_score = max(
                [x.match_score(word, data) for x in self.children])
        elif self.logical_rel == "AND":
            children_score = min(
                [x.match_score(word, data) for x in self.children])
        else:
            raise Exception("VNRestriction.match_score : invalid logical relation")
        
        return base_score + children_score

    def get_atomic_restrictions(self):
        """Return the list of basic (one keyword without logical relations)
        restrictions needed to compute this restriction.
        
        This function is no longer used.
        """
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
        if r1 == r2: return r1
        
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
        """Returns a restriction with only a keyword 
        
        :returns: VNRestriction -- the resulting restriction
        """
        
        return VNRestriction(restr_type=restr_type)

    @staticmethod
    def build_and(r1, r2):
        """Link two restrictions with an AND relation 
        
        :returns: VNRestriction -- the resulting restriction
        """
        
        return VNRestriction._build_keyword(r1, r2, "AND")
    
    @staticmethod
    def build_or(r1, r2):
        """Link two restrictions with an OR relation 
         
        :returns: VNRestriction -- the resulting restriction
        """
         
        return VNRestriction._build_keyword(r1, r2, "OR")
    
    @staticmethod
    def build_not(r):
        """Apply a NOT operator to a restriction 
         
        :returns: VNRestriction -- the resulting restriction
        """
         
        return VNRestriction(children=[r], logical_rel="NOT")
        
    @staticmethod
    def build_empty():
        """Return NORESTR 
        
        :returns: VNRestriction -- the resulting empty restriction
        """
        
        return VNRestriction(children=[], logical_rel="AND")
    
    @staticmethod 
    def build_from_xml(xml):
        """Build a restriction matching an XML representation of VerbNet
        
        :param xml: The XML representing the restriction in VerbNet
        :type xml: xml.etree.ElementTree.Element
        :returns: VNRestriction -- the resulting restriction
        """
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
