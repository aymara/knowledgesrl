#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
..module:: framestructure
    synopsis: This modules define the class used to represent
        frames, arguments and predicates
        
"""

class Frame:

    """A frame extracted from the corpus 
    
    Members :
    sentence -- string containing the sentence in which the frame appears
    predicate -- Predicate object representing the frame's predicate
    args -- Arg list containing the predicate's arguments
    
    """
    
    def __init__(self, sentence, predicate, args):
        self.sentence = sentence
        self.predicate = predicate
        self.args = args
        self.args.sort()
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.sentence == other.sentence and
            self.predicate == other.predicate and
            self.args == other.args)
        
class Arg:

    """An argument of a frame 
    
    Members:
    begin -- integer, position of the argument's first character in the sentence
    end -- integer, position of the argument's last character in the sentence
    text -- string containing the argument's text
    role -- string containing the argument's role
    instanciated -- boolean that marks wether the argument is instanciated
    
    """
    
    def __init__(self, begin, end, text, role, instanciated):
        self.begin = begin
        self.end = end
        self.text = text
        self.role = role
        self.instanciated = instanciated
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__)  and
            ((self.begin == other.begin and self.end == other.end) or
                (self.instanciated == False and other.instanciated == False)) and
            self.role == other.role)
            
    def __cmp__(self, other):
        if not self.instanciated:
            if other.instanciated: return 1
            if self.role < other.role: return -1
            if self.role > other.role: return 1
            return 0
        if not other.instanciated: return -1
        if self.begin < other.begin: return -1
        if self.begin > other.begin: return 1
        return 0
        
class Predicate:

    """A frame's predicate 
    
    Members:
    begin -- integer, position of the predicate's first character in the sentence
    end -- integer, position of the predicate's last character in the sentence
    text -- string containing the predicate's text
    
    """
    
    def __init__(self, begin, end, text):
        self.begin = begin
        self.end = end
        self.text = text
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
            self.begin == other.begin and
            self.end == other.end)

