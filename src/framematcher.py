#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Match Frame to appropriate VerbNet structures"""

from framestructure import *
import unittest

class EmptyFrameError(Exception):
    """Trying to use an empty frame in a match
    
    :var frame1: VerbnetFrame, first frame
    :var frame2: VerbnetFrame, second frame
    
    """
    
    def __init__(self, frame1, frame2):
        self.frame1 = frame1
        self.frame2 = frame2
        
    def __str__(self):
        return ("Error : tried to use a frame without any slot in frame matching\n"
               "frame 1 : {}\nframe 2 : {}".format(self.frame1, self.frame2))
                
def match_score(frame, model):
    """Compute the matching score between two frames
        
    :param frame: real frame to test.
    :type frame: VerbnetFrame.
    :param model: VerbNet model with which to compare it.
    :type mode: VerbnetFrame.
        
    """
    num_match = 0
    frame_size = 0
    model_size = 0
    stop_matching = False
    
    for i,elem in enumerate(frame.structure):
        if is_a_slot(elem): frame_size += 1
        
        if i >= len(model.structure): stop_matching = True
        if not stop_matching:
            if is_a_match(elem, model.structure[i]): 
                if is_a_slot(elem): num_match += 1
            else: stop_matching = True
  
    for elem in model.structure:
        if is_a_slot(elem): model_size += 1
       
    if frame_size == 0 or model_size == 0:
        raise EmptyFrameError(frame,     model)
   
    return int(100 * (num_match / frame_size + num_match / model_size))

def is_a_slot(elem):
    return elem.isupper() and elem != "V"
    
def is_a_match(elem1, elem2):
    return elem1 in elem2.split("/")
        
class frameMatcherTest(unittest.TestCase):
     def test_1(self):
        frame1 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], [])
        frame2 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], [])
        
        score = match_score(frame1, frame2)
        self.assertEqual(score, 200)
        print(score)
        
     def test_2(self):
        frame1 = VerbnetFrame(["to", "be"], [])
        frame2 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], [])

        with self.assertRaises(EmptyFrameError):
            match_score(frame1, frame2)
            
     def test_3(self):
        frame1 = VerbnetFrame(["NP", "V", "with", "NP"], [])
        frame2 = VerbnetFrame(["NP", "V", "NP", "with", "NP"], [])

        score = match_score(frame1, frame2)
        self.assertEqual(score, int(100*1/2+100*1/3))
        print(score)
            
if __name__ == "__main__":
    unittest.main()

