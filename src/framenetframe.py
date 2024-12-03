#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Frames definitions, frames instances, its arguments and predicates."""

class SemantiType:
    """ A semantic type as defined by FrameNet"""

    def __init__(self, name, id):
        # nothing
        self.name = name
        self.id = id

class FrameElement:
    """ A FrameNet frame element

    :var name: the name of the frame element, e.g.: Activity
    :var id: int. The frame element id
    :var abbreviation: the abbreviated frame element name
    :var coreType: express wether the frame element is a core element or not, etc.
    :var definition: the text difining the frame element semantics
    :var creator: (xml attribute cBy) creator id
    :var creationDate: (xml attribute cDate) creation date
    :var semanticType: name of the SemantiType of this frame. Can be None
    """

    def __init__(self, name, id):
        # nothing
        self.name = name
        self.id = id

class LexicalUnit:
    """
        <lexUnit nbocc="108" inhib_in_lexicon="false" lemma_is_annotated="true">
        <sentenceCount annotated="0"/>
        <otherlexUnit framename="FR_Purpose" ID="2224" annotatedsent="33"/>
        <otherlexUnit framename="Other_sense" ID="100809" annotatedsent="54"/>
        </lexUnit>
    """

    def __init__(self, pos, name, id):
        # nothing
        self.pos = pos
        self.name = name
        self.id = id


class FrameDefinition:
    """A frame structure as defined by FrameNet

    :var name: the name of the frame, e.g.: Ingestion
    :var id: int. The frame id
    :var definition: the text difining the frame semantics
    :var creator: (xml attribute cBy) creator id
    :var creationDate: (xml attribute cDate) creation date
    :var semanticType: name of the SemantiType of this frame. Can be None
    :var elements: a map associating frame element names to their
            definition
    :var relations: a map associating relation type names to a set of
    frame names (e.g. {"Has Subframe(s)" : [Activity_finish, Activity_ongoing, … ], … })
    :var lex_units: a map associating "lemma.pos_tag" to the details of this
            lexical unit (LexicalUnit)


"""

    def __init__(self, name, id):
        # nothing
        self.name = name
        self.id = id

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.id == other.id)

    def __str__(self):
        return "FrameDefinition({}, {})".format(
            self.name, self.id)

    def __repr__(self):
        return ("FrameDefinition(name={}, id={})".format(self.name, self.id))


class FrameInstance:
    """A frame directly extracted from the FrameNet corpus or another CoNLL
    file.

    :var sentence: Sentence in which the frame appears
    :var predicate: Predicate object representing the frame's predicate
    :var args: Arg list containing the predicate's arguments
    :var words:
    :var frame_name:
    :var headwords:
    :var sentence_id: id of thesentencewhere is this frame instance in the
            CONLL file
    :var filename:
    :var slot_type:
    :var arg_annotated:
    :var passive:
    :var tree:

    """

    def __init__(self, sentence, predicate, args, words, frame_name,
                 sentence_id=-1, filename="",
                 slot_type="", arg_annotated=False, tree=None,
                 headwords=None):

        self.sentence = sentence
        self.predicate = predicate
        self.args = sorted(args)
        self.words = words
        self.frame_name = frame_name
        if headwords is None:
            self.headwords = [None] * len(self.args)
        else:
            self.headwords = headwords
        self.sentence_id = sentence_id
        self.filename = filename
        self.slot_type = slot_type
        self.arg_annotated = arg_annotated
        self.passive = None  # as yet undecided
        self.tree = tree

    def get_word(self, word):
        return self.sentence[word.begin:word.end + 1]

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.sentence == other.sentence and
                self.predicate == other.predicate and
                self.args == other.args and
                self.words == other.words)

    def __lt__(self, other):
        if isinstance(other, FrameInstance):
            return (self.sentence < other.sentence or
                    self.predicate < other.predicate or
                    self.args < other.args or
                    self.words < other.words)
        return NotImplemented

    def __str__(self):
        return "FrameInstance({}, {}, {})".format(
            self.frame_name, self.predicate, self.args)

    def __repr__(self):
        return ("FrameInstance(frame_name={}, predicate={}, "
                "args={}, sentence={}, words={})".format(
                    self.frame_name, self.predicate, self.args,
                    self.sentence, self.words))


class Arg:
    """An argument of a frame

    :var begin: integer -- position of the argument's first character in the
            sentence
    :var end: integer -- position of the argument's last character in the
            sentence
    :var text: string -- the argument's chunk text
    :var role: string -- the argument's role
    :var instanciated: boolean -- marks wether the argument is instanciated
    :var phrase_type: string -- syntactic type of the argument chunk
    :var position: int -- position of the argument chunk head token in its
            sentence CONLL file
    :var annotated: boolean --

    """

    def __init__(self, begin, end, text, role, instanciated, phrase_type,
                 annotated=True, position=None):
        self.begin = begin
        self.end = end
        self.text = text
        self.role = role
        self.instanciated = instanciated
        self.phrase_type = phrase_type
        self.position = position

        # This can be false for extracted args which could not be matched with
        # annotated args from the fulltext corpus
        self.annotated = annotated

    def __repr__(self):
        return "Arg({}, {}, {}, {}, {}, {}, {}, {})".format(self.begin,
                                                            self.end,
                                                            self.text,
                                                            self.role,
                                                            self.instanciated,
                                                            self.phrase_type,
                                                            self.position,
                                                            self.annotated)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and ((self.begin == other.begin
                      and self.end == other.end)
                     or (self.instanciated is False
                         and other.instanciated is False))
                and self.role == other.role
                and self.phrase_type == other.phrase_type)

    def __cmp__(self, other):
        if not self.instanciated:
            if other.instanciated:
                return 1
            elif self.role < other.role:
                return -1
            elif self.role > other.role:
                return 1
            else:
                return 0
        elif not other.instanciated:
            return -1
        elif self.begin < other.begin:
            return -1
        elif self.begin > other.begin:
            return 1
        else:
            return 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0


class Predicate:
    """A frame's predicate

    :var begin: integer, position of the predicate's first character in the
            sentence
    :var end: integer, position of the predicate's last character in the
            sentence
    :var text: string containing the predicate's text
    :var lemma: string containing the predicate's lemma
    :var tokenid: integer the id of this predicate token in the CONLL input
    """

    def __init__(self, begin, end, text, lemma, tokenid=None):
        self.begin = begin
        self.end = end
        self.text = text
        self.lemma = lemma
        self.tokenid = tokenid

    def __repr__(self):
        return "Predicate({}, {}, {}, {}, {})".format(
            self.text, self.lemma, self.tokenid, self.begin, self.end)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.begin == other.begin and
                self.end == other.end and
                self.lemma == other.lemma)

    def __lt__(self, other):
        return (isinstance(other, self.__class__) and
                (self.begin < other.begin or
                 self.end < other.end or
                 self.lemma < other.lemma))


class Word:
    """A frame's word

    :var begin: integer, position of the predicate's first character in the
            sentence
    :var end: integer, position of the predicate's last character in the
            sentence
    :var pos: string containing the predicate's part-of-speech

    """

    def __init__(self, begin, end, pos):
        self.begin = begin
        self.end = end
        if pos == 'sent':
            pos = '.'
        self.pos = pos.upper()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.begin == other.begin and
                self.end == other.end and
                self.pos == other.pos)

    def __lt__(self, other):
        return (isinstance(other, self.__class__) and
                (self.begin < other.begin or
                 self.end < other.end or
                 self.pos < other.pos))

    def __repr__(self):
        return "Word({}, {}, \"{}\")".format(self.begin, self.end, self.pos)
