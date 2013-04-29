#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
..module:: framenetreader
    synopsis: This modules transform the XML of the FrameNet fulltext corpus
        in more usable Frame, Arg and Predicate objects.
"""

import unittest
import xml.etree.ElementTree as ET
import os
import sys
from framestructure import *

class FulltextReader:

    """Class used to parse one file of the FrameNet fulltext corpus

    Members:
    frames -- Frame list of every frame collected
    
    """
    
    def __init__(self, filename):
        """Read a file and update the collected frames list.
        
        :param filename: Path to the file to read.
        :type filename: str.
        
        """
        root = ET.parse(filename).getroot()
                
        # etree will add the xmlns string before every tag name
        self._xmlns = "{http://framenet.icsi.berkeley.edu}"

        self.frames = []
        
        for sentence in root.findall(self._xmlns+"sentence"):
            self._parse_sentence(sentence)
            
    def _parse_sentence(self, sentence):
        """ Handles the parsing of one sentence.
        
        :param sentence: XML representation of the sentence.
        :type sentence: str.
        
        """
        
        text = sentence.findall(self._xmlns+"text")[0].text
        for potential_frame in sentence.findall(self._xmlns+"annotationSet[@luName]"):
            frame_type = potential_frame.attrib["luName"].split(".")[1]
            annotated = potential_frame.attrib["status"]
            
            """We keep only annotated verbal frames"""
            if frame_type == "v" and annotated != "UNANN":
                self._parse_frame(text, potential_frame)
                
    def _parse_frame(self, sentence_text, frame):
        """ Handle the parsing of one frame.
        
        :param sentence_text: Sentence in which the frame occurs.
        :type sentence_text: str.
        :param frame: XML representation of the frame
        :type frame: str.
        
        """
        
        # Predicate object creation
        predicate_data = frame.findall(self._xmlns+"layer[@name='Target']")[0]
        
        # This test handles the only self-closed layer tag that exists in the corpus
        if len(predicate_data) == 0:
            sys.stderr.write("WARNING : frame ignored in \""+sentence_text+"\"\n")
            return
        else:
            predicate_data = predicate_data[0]
        
        predicate_start = int(predicate_data.attrib["start"])
        predicate_end = int(predicate_data.attrib["end"])
        predicate = Predicate(
            predicate_start, 
            predicate_end,
            sentence_text[predicate_start:(predicate_end + 1)])
            
        # Argument list creation
        args = []    
        for arg_data in frame.findall(self._xmlns+"layer[@name='FE']/*"):
            # Checks wether the argument is instanciated
            if "itype" in arg_data.attrib:
                arg_start, arg_end, arg_instanciated = 0, -1, False
            else:
                arg_start = int(arg_data.attrib["start"])
                arg_end = int(arg_data.attrib["end"])
                arg_instanciated = True
                    
            args.append(Arg(
                arg_start, 
                arg_end,
                sentence_text[arg_start:(arg_end + 1)],
                arg_data.attrib["name"],
                arg_instanciated))
                
        # Frame creation
        self.frames.append(Frame(sentence_text, predicate, args))

class FulltextReaderTest(unittest.TestCase):

    """Unit test class"""
    
    def setUp(self):
        self.expected_values = {
            "LUCorpus-v0.3__20000420_xin_eng-NEW.xml":(20,52),
            "NTI__Syria_NuclearOverview.xml":(101,282),
            "NTI__ChinaOverview.xml":(72,206),
            "Miscellaneous__Hijack.xml":(6,15),
            "NTI__SouthAfrica_Introduction.xml":(105,299),
            "QA__IranRelatedQuestions.xml":(439,1166),
            "NTI__Iran_Introduction.xml":(125,323),
            "ANC__110CYL072.xml":(20,52),
            "NTI__Russia_Introduction.xml":(62,161),
            "PropBank__LomaPrieta.xml":(164,399),
            "NTI__NorthKorea_Introduction.xml":(128,358),
            "LUCorpus-v0.3__AFGP-2002-600045-Trans.xml":(82,206),
            "NTI__NorthKorea_NuclearCapabilities.xml":(60,161),
            "LUCorpus-v0.3__IZ-060316-01-Trans-1.xml":(86,209),
            "LUCorpus-v0.3__20000415_apw_eng-NEW.xml":(37,99),
            "Miscellaneous__SadatAssassination.xml":(11,40),
            "NTI__Iran_Missile.xml":(242,667),
            "KBEval__parc.xml":(57,153),
            "KBEval__Brandeis.xml":(23,57),
            "SemAnno__Text1.xml":(14,49),
            "ANC__IntroJamaica.xml":(111,293),
            "PropBank__PolemicProgressiveEducation.xml":(144,369),
            "NTI__Kazakhstan.xml":(26,76),
            "PropBank__TicketSplitting.xml":(92,239),
            "ANC__IntroHongKong.xml":(44,105),
            "LUCorpus-v0.3__wsj_1640.mrg-NEW.xml":(41,97),
            "LUCorpus-v0.3__enron-thread-159550.xml":(67,197),
            "NTI__NorthKorea_ChemicalOverview.xml":(109,287),
            "LUCorpus-v0.3__ENRON-pearson-email-25jul02.xml":(6,12),
            "LUCorpus-v0.3__CNN_AARONBROWN_ENG_20051101_215800.partial-NEW.xml":(93,238),
            "C-4__C-4Text.xml":(24,67),
            "KBEval__atm.xml":(101,305),
            "NTI__workAdvances.xml":(45,127),
            "LUCorpus-v0.3__AFGP-2002-600002-Trans.xml":(192,506),
            "LUCorpus-v0.3__artb_004_A1_E1_NEW.xml":(14,40),
            "NTI__Iran_Biological.xml":(142,367),
            "Miscellaneous__Hound-Ch14.xml":(20,43),
            "LUCorpus-v0.3__20000410_nyt-NEW.xml":(24,71),
            "ANC__112C-L013.xml":(41,100),
            "ANC__110CYL200.xml":(34,83),
            "LUCorpus-v0.3__wsj_2465.xml":(70,183),
            "ANC__110CYL070.xml":(26,73),
            "LUCorpus-v0.3__20000424_nyt-NEW.xml":(5,14),
            "ANC__110CYL069.xml":(1,2),
            "ANC__HistoryOfJerusalem.xml":(183,502),
            "NTI__LibyaCountry1.xml":(81,242),
            "fullText.xsl":(0,0),
            "LUCorpus-v0.3__SNO-525.xml":(24,56),
            "ANC__StephanopoulosCrimes.xml":(60,164),
            "NTI__BWTutorial_chapter1.xml":(177,448),
            "KBEval__MIT.xml":(78,210),
            "LUCorpus-v0.3__602CZL285-1.xml":(24,64),
            "ANC__EntrepreneurAsMadonna.xml":(71,184),
            "ANC__WhereToHongKong.xml":(160,395),
            "LUCorpus-v0.3__sw2025-ms98-a-trans.ascii-1-NEW.xml":(148,320),
            "ANC__HistoryOfGreece.xml":(251,720),
            "LUCorpus-v0.3__AFGP-2002-602187-Trans.xml":(50,133),
            "LUCorpus-v0.3__20000419_apw_eng-NEW.xml":(25,61),
            "ANC__110CYL068.xml":(61,163),
            "NTI__WMDNews_042106.xml":(105,283),
            "PropBank__AetnaLifeAndCasualty.xml":(12,37),
            "PropBank__ElectionVictory.xml":(57,162),
            "NTI__NorthKorea_NuclearOverview.xml":(284,770),
            "KBEval__LCC-M.xml":(90,247),
            "LUCorpus-v0.3__artb_004_A1_E2_NEW.xml":(16,42),
            "NTI__Taiwan_Introduction.xml":(50,136),
            "PropBank__BellRinging.xml":(138,347),
            "KBEval__utd-icsi.xml":(107,259),
            "KBEval__lcch.xml":(185,517),
            "KBEval__Stanford.xml":(46,122),
            "LUCorpus-v0.3__CNN_ENG_20030614_173123.4-NEW-1.xml":(51,122),
            "NTI__WMDNews_062606.xml":(167,450),
            "NTI__Iran_Nuclear.xml":(215,616),
            "ANC__IntroOfDublin.xml":(84,209),
            "ANC__HistoryOfLasVegas.xml":(191,530),
            "ANC__110CYL067.xml":(30,68),
            "NTI__Iran_Chemical.xml":(229,657),
            "KBEval__cycorp.xml":(12,32),
            "LUCorpus-v0.3__20000416_xin_eng-NEW.xml":(40,108)}
        """Total : 18224 arguments in 6828 frames"""
    
        self.tested_frames = [
            Frame(
                "Rep . Tony Hall , D- Ohio , urges the United Nations to allow"+\
                " a freer flow of food and medicine into Iraq .", 
                Predicate(28, 32, "urges"),
                [
                    Arg(34, 51, "the United Nations", "Addressee", True),
                    Arg(53, 104,
                        "to allow a freer flow of food and medicine into Iraq", 
                        "Content", True),
                    Arg(0, 26, "Rep . Tony Hall , D- Ohio", "Speaker", True)
                ] ),
            Frame(
                "Rep . Tony Hall , D- Ohio , urges the United Nations to allow"+\
                " a freer flow of food and medicine into Iraq .", 
                 Predicate(56, 60, "allow"),
                 [
                    Arg(62, 104, 
                        "a freer flow of food and medicine into Iraq",
                        "Action", True),
                    Arg(34, 51, "the United Nations", "Grantee", True),
                    Arg(0, -1, "", "Grantor", False)
                 ] ) ]
            

    def test_global(self):
        """Checks that no exception is raised and that
        no obvious errors occurs while parsing the whole corpus
        
        """

        basepath = "../data/fndata-1.5/fulltext/"

        for filename in os.listdir(basepath):
            print("Parsing "+filename)
            reader = FulltextReader(basepath+filename)

            # Nothing is empty and begins/ends are coherents
            arg_num = 0
            for frame in reader.frames:
                self.assertNotEquals(frame.predicate.text, "")
                self.assertEquals(
                    frame.predicate.text, 
                    frame.sentence[frame.predicate.begin:(frame.predicate.end + 1)])
                arg_num += len(frame.args)
                for arg in frame.args:
                    self.assertTrue(arg.text != "" or arg.instanciated == False)
                    self.assertEquals(
                        arg.text, 
                        frame.sentence[arg.begin:(arg.end + 1)])     
                            
            # The total number of frames and args is correct
            (good_frame_num, good_arg_num) = self.expected_values[filename]
            self.assertEquals(len(reader.frames), good_frame_num)
            self.assertEquals(arg_num, good_arg_num)
            print("Found "+repr(len(reader.frames))+" frames and "+
                repr(arg_num)+" arguments : ok")

    def test_specific_frames(self):
        """Checks that some particular frames are correctly parsed"""
        path = "../data/fndata-1.5/fulltext/LUCorpus-v0.3__20000424_nyt-NEW.xml"
        reader = FulltextReader(path)
        self.assertEquals(reader.frames[0], self.tested_frames[0])
        self.assertEquals(reader.frames[1], self.tested_frames[1])
        
if __name__ == "__main__":
    unittest.main()

