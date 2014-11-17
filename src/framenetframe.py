#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Frames instances, its arguments and predicates."""


class FrameInstance:
    """A frame directly extracted from the FrameNet corpus or another CoNLL
    file.

    :var sentence: Sentence in which the frame appears
    :var predicate: Predicate object representing the frame's predicate
    :var args: Arg list containing the predicate's arguments

    """

    def __init__(self, sentence, predicate, args, words, frame_name,
                 sentence_id=-1, filename="",
                 slot_type="", arg_annotated=False, tree=None,
                 headwords=None):

        self.frame_name = frame_name
        self.sentence = sentence
        self.predicate = predicate
        self.args = sorted(args)
        if headwords is None:
            self.headwords = [None] * len(self.args)
        else:
            self.headwords = headwords
        self.words = words
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

    def __repr__(self):
        return "FrameInstance({}, {}, {})".format(
            self.predicate, self.args, self.frame_name)


class Arg:

    """An argument of a frame

    :var begin: integer, position of the argument's first character in the sentence
    :var end: integer, position of the argument's last character in the sentence
    :var text: string containing the argument's text
    :var role: string containing the argument's role
    :var instanciated: boolean that marks wether the argument is instanciated

    """

    def __init__(self, begin, end, text, role, instanciated, phrase_type, annotated=True, position=None):
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
        return "Arg({}, {}, {})".format(self.text, self.phrase_type, self.role)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            ((self.begin == other.begin and self.end == other.end) or
                (self.instanciated is False and other.instanciated is False)) and
            self.role == other.role and
            self.phrase_type == other.phrase_type)

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

    :var begin: integer, position of the predicate's first character in the sentence
    :var end: integer, position of the predicate's last character in the sentence
    :var text: string containing the predicate's text
    :var lemma: string containing the predicate's lemma

    """

    def __init__(self, begin, end, text, lemma, position=None):
        self.begin = begin
        self.end = end
        self.text = text
        self.lemma = lemma
        self.position = position

    def __repr__(self):
        return "Predicate({}, {})".format(self.text, self.lemma)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.begin == other.begin and
            self.end == other.end and
            self.lemma == other.lemma)


class Word:
    """A frame's word

    :var begin: integer, position of the predicate's first character in the sentence
    :var end: integer, position of the predicate's last character in the sentence
    :var text: string containing the predicate's text
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

    def __repr__(self):
        return "Word({}, {}, \"{}\")".format(self.begin, self.end, self.pos)
