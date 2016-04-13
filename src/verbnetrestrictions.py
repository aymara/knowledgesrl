#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# List of possible thematic role restrictions
possible_types = {
        "abstract": 'abstraction.n.06',
        "animal": 'animal.n.01',
        "animate": 'animate_thing.n.01',
        "body_part": 'body_part.n.01',
        "comestible": 'comestible.n.01',
        "communication": 'communication.n.02',
        "concrete": 'physical_entity.n.01',
        "currency": 'currency.n.01',
        "garment": 'clothing.n.01',
        "human": 'human.n.01',
        "int_control": 'animate_thing.n.01',
        "location": 'location.n.01',
        "machine": 'device.n.01',
        "organization": 'organization.n.01',

        # Those really properties, eg. in pour-9.5 we can pour either a
        # subtance or various concrete things, hence the +concrete & +plural
        # restriction.
        "force": None,
        "plural": None,
        "pointy": None,
        "refl": None,  # reflexive object, eg. himself

        "region": 'region.n.01',
        "scalar": 'quantity.n.01',
        "solid": 'matter.n.03',
        "sound": 'sound.n.01',
        "substance": 'substance.n.01',
        "time": 'time_period.n.01',
        "vehicle": 'transport.n.01',

        # Only used in coil-9.6
        "elongated": None,
        "nonrigid": None,
}

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

    def __init__(self, restr_type=None, children=[], logical_rel=None):
        """Private constructor. Use the build* static methods to instanciate
        VNRestricitons.
        Takes care of deleting children that could occurs several time in the
        list given as argument.

        """

        if restr_type is not None and restr_type not in possible_types.keys():
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
        if self.logical_rel is None:
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

        if not isinstance(other, self.__class__):
            return False
        elif self.type is not None or other.type is not None:
            return self.type == other.type
        elif self.logical_rel != other.logical_rel:
            return False

        # We cannot use Python's builtin unordered sets, since
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
        if self._is_empty_restr():
            return 1 / 100

        base_score = 0
        if word in data[self]:
            base_score = data[self][word]

        if self.logical_rel is None:
            children_score = 0
        elif self.logical_rel == "NOT":
            children_score = (-1) * self.children[0].match_score(word, data)

            # Attribute a score of 1 for finding no match
            if children_score == 0:
                children_score = 1
        elif self.logical_rel == "OR":
            children_score = max(
                [x.match_score(word, data) for x in self.children])
        elif self.logical_rel == "AND":
            children_score = min(
                [x.match_score(word, data) for x in self.children])
        else:
            raise Exception("VNRestriction.match_score : invalid logical relation")

        return base_score + children_score

    def matches_to_headword(self, headword):
        from nltk.corpus import wordnet as wn
        
        if self._is_empty_restr():
            return True

        pos, word = headword
        if pos not in ['NN', 'NNS', 'JJ', 'RB']:
            return True
        morphy_pos = {'NN': wn.NOUN, 'NNS': wn.NOUN, 'RB': wn.ADV, 'JJ': wn.ADJ}

        if self.logical_rel is None:
            if possible_types[self.type] is None:
                return True

            try:
                lemma = wn.morphy(word, morphy_pos.get(pos, None))
                lemma = lemma if lemma is not None else word
                selrestr_wordnet = wn.synset(possible_types[self.type])
                headword_wordnet = wn.synsets(lemma)[0]
                #print(selrestr_wordnet, headword_wordnet.hypernym_paths(), end='')
                return selrestr_wordnet in headword_wordnet.hypernym_paths()[0]
            except IndexError:
                # lemma not found
                return True
        elif self.logical_rel == "NOT":
            return not self.children[0].matches_to_headword(headword)
        elif self.logical_rel == "OR":
            result = False
            for c in self.children:
                result = result or c.matches_to_headword(headword)
            return result
        elif self.logical_rel == "AND":
            result = True
            for c in self.children:
                result = result and c.matches_to_headword(headword)
            return result
        else:
            print('WTF!')
            exit()

    @staticmethod
    def _build_keyword(r1, r2, kw):
        if r1._is_empty_restr():
            return r2
        elif r2._is_empty_restr():
            return r1
        elif r1 == r2:
            return r1
        elif r1.logical_rel == kw and r2.logical_rel == kw:
            return VNRestriction(children=r1.children + r2.children, logical_rel=kw)
        elif r1.logical_rel == kw:
            return VNRestriction(children=r1.children + [r2], logical_rel=kw)
        elif r2.logical_rel == kw:
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
