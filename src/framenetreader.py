#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Parse FrameNet fulltext annotation into FrameInstance, Arg and Predicate objects.

Notes:

 * Currently, when a role is not instantiated in FrameNet, we simply store it
   as empty arg in framenetreader. Should we take advantage of the fact that we
   know the type of non instanciation?
 * Argument of a trigger can be the trigger itself, which doesn't allow to
   represent our frame as "NP V NP...". Currently, it's considered as a case of
   null instanciation, but this could change if needed.
 * FrameNet sometimes has two layers of annotations, with the second layer
   having roles that overlap with the first one, but without PT (Phrase Type).
   Those layers are ignored.
 * Fourteen other cases (out of 18000+) of an argument (or predicate ?) not
   matching with any word in the sentence. Also ignored right now.


"""

import unittest
import xml.etree.ElementTree as ET
import os
import sys
import glob

from framestructure import FrameInstance, Predicate, Word, Arg
from verbnetprepclasses import rel_pronouns
import framenetcoreargs
import paths
import options


class FulltextReader:

    """Class used to parse one file of the FrameNet fulltext corpus

    :var frames: FrameInstance list of every frame collected
    
    """
    
    core_arg_finder = None
    predicate_pos = ["md", "MD", 
        "VB", "VBD", "VBG", "VBN", "VBP", "VBZ", 
        "VV", "VVD", "VVG", "VVN", "VVP", "VVZ",
        "VH", "VHD", "VHG", "VHN", "VHP", "VHZ"]
    
    pos_mapping = {
        # Nouns
        "NP": "NNP", "NPS": "NNPS",
        # Preposition
        "PP": "PRP", "PP$": "PRP$",
        # Verbs
        "VH": "VB", "VHD": "VBD", "VHG": "VBG", "VHP": "VBP", "VHN": "VBN",
        "VHZ": "VBZ", "VV": "VB", "VVD": "VBD", "VVG": "VBG", "VVN": "VBN",
        "VVP": "VBP", "VVZ": "VBZ"
    }
    
    # etree will add the xmlns string before every tag name
    framenet_xmlns = "{http://framenet.icsi.berkeley.edu}"
    
    def __init__(self, filename, core_args_only = False, keep_unannotated = False,
        trees = None, keep_nonverbal = False, pos_file = None):
        """Read a file and update the collected frames list.
        
        :param filename: Path to the file to read.
        :type filename: str.
        :param core_args_only: Whether we should discard non core args.
        :type core_args_only: boolean.
        :param keep_unannotated: Whether we should keep frames without annotated args.
        :type keep_unannotated: boolean.
        :param trees: Syntactic trees for the frames (must be same order as in the corpus)
        :type trees: None | SyntacticTreeNode List
        """
        
        if FulltextReader.core_arg_finder == None and core_args_only:
            print("Loading core arguments list for FrameNet frames... ", end="", file=sys.stderr)
            FulltextReader.core_arg_finder = framenetcoreargs.CoreArgsFinder()
            FulltextReader.core_arg_finder.load_data_from_xml(paths.FRAMENET_FRAMES)
            print("done!", file=sys.stderr)
        
        self.frames = []
        
        self.core_args_only = core_args_only
        self.keep_unannotated = keep_unannotated
        self.keep_nonverbal = keep_nonverbal
        
        self.pos_file = pos_file
        self.pos_data = None
        if self.pos_file != None:
            pos_file_content = open(pos_file).read()
            self.pos_data = pos_file_content.split("\n\n")

        # Debug data
        self.filename = filename
        self.ignored_layers = []
        self.predicate_is_arg = []
        self.phrase_not_found = []
        self.missing_predicate_data = []
        self.non_existing_frame_name = []
        
        root = ET.ElementTree(file=filename)
        if not self._init_file_data(root): return
        self._parse_xml(root, trees)
    
    def _init_file_data(self, root):
        if root.getroot().tag == "corpus":
            self._init_semafor_data()
        elif root.find(FulltextReader.framenet_xmlns+"valences") == None:
            self._init_fulltext_data()
        else:
            return self._init_lu_data(root)
        return True
    
    def _init_fulltext_data(self):
        self.corpus = "fulltext"
        self._xmlns = FulltextReader.framenet_xmlns
        self.all_annotated = False
        self.constant_predicate = ""
        self.constant_frame = ""
        self.patterns = {
            "sentence":self._xmlns + "sentence",
            "frame":self._xmlns + "annotationSet[@luName]",
            "predicate":self._xmlns+"layer[@name='Target']",
            "arg":"{}layer[@name='FE'][@rank='{}']/*",
            "pt":"{}layer[@name='PT'][@rank='{}']/*"
        }
 
    def _init_lu_data(self, root):
        self.corpus = "lu"
        self._xmlns = FulltextReader.framenet_xmlns
        self.all_annotated = False
            
        # keep_unannotated has no sense for LUCorpus
        self.keep_unannotated = False
            
        predicate_data = root.getroot().attrib["name"].split(".")
        if predicate_data[1] != "v":
            return False
        self.constant_predicate = predicate_data[0]
        self.constant_frame = root.getroot().attrib["frame"]
        
        self.patterns = {
            "sentence":(self._xmlns + "subCorpus/" +
            self._xmlns + "sentence"),
            "frame":self._xmlns + "annotationSet",
            "predicate":self._xmlns+"layer[@name='Target']",
            "arg":"{}layer[@name='FE'][@rank='{}']/*",
            "pt":"{}layer[@name='PT'][@rank='{}']/*"
        }
        
        return True
 
    def _init_semafor_data(self):
        self.corpus = "semafor"
        self._xmlns = ""
        self.all_annotated = True
        self.constant_predicate = ""
        self.constant_frame = ""
        
        self.patterns = {
            "sentence":("documents/document/paragraphs/paragraph"
                "/sentences/sentence"),
            "frame":"annotationSets/annotationSet",
            "predicate":"layers/layer[@name='Target']/labels",
            "arg":"layers/layer[@name='FE']/labels/*"
        }
        
    def _parse_xml(self, root, trees):
        for i, sentence in enumerate(root.findall(self.patterns["sentence"])):
            for frame in self._parse_sentence(sentence, i):
                frame.sentence_id = i
                if trees != None:
                    frame.tree = trees[i]
                
                self.frames.append(frame)
    
    def _parse_sentence(self, sentence, sentence_number):
        """Handle the parsing of one sentence.
        
        :param sentence: XML representation of the sentence.
        :type sentence: xml.etree.ElementTree.Element.
        
        """

        text = sentence.find(self._xmlns + "text").text.lower()

        words = []
        predicate_starts = []
        pos_data = []
        if self.pos_data == None:
            pos_annotation = "{0}annotationSet/{0}layer[@name='PENN']/" \
                         "{0}label".format(self._xmlns)
            for label in sentence.findall(pos_annotation):
                pos_data.append({
                    "start":label.attrib["start"],
                    "end":label.attrib["end"],
                    "pos":label.attrib["name"]
                })
        else:
            # We can use the existing automatic SEMAFOR part-of-speech annotation
            start = 0
            for line in self.pos_data[sentence_number].split("\n"):
                if line == "": continue
                line = line.split("\t")
                pos_data.append({
                    "start":start,
                    "end":start+len(line[1]) - 1,
                    "pos":line[3]
                })
                start += len(line[1]) + 1
        
        for word in pos_data:
            if (word["pos"] in FulltextReader.predicate_pos
                or self.keep_nonverbal
            ):
                predicate_starts.append(int(word["start"]))
            
            words.append(Word(int(word["start"]), int(word["end"]), word["pos"]))
        
        already_annotated = []
        for potential_frame in sentence.findall(self.patterns["frame"]):
            # We keep only annotated verbal frames
            
            annotated = ("status" in potential_frame.attrib and
                potential_frame.attrib["status"] != "UNANN")
            annotated = annotated or self.all_annotated
            
            if not (annotated or self.keep_unannotated): continue
            frame = self._parse_frame(
                text, words, potential_frame, annotated, predicate_starts)
            if frame and not frame.predicate.begin in already_annotated:
                already_annotated.append(frame.predicate.begin)
                yield frame
                  
    def _parse_frame(self, sentence_text, words, frame, annotated, predicate_starts):
        """Handle the parsing of one frame.
        
        :param sentence_text: Sentence in which the frame occurs.
        :type sentence_text: str.
        :param frame: XML representation of the frame
        :type frame: xml.etree.ElementTree.Element.
        
        """

        predicate = self._build_predicate(sentence_text, frame)
        
        if (predicate == None or
            (self.corpus in ["fulltext", "semafor"] and not predicate.begin in predicate_starts)
        ):
            return
        
        if self.constant_frame == "":
            frame_name = frame.attrib["frameName"]
        else:
            frame_name = self.constant_frame
        
                        
        if frame_name == "Test35":
            self.non_existing_frame_name.append({
                "file":self.filename,
                "frame_name":frame_name,
                "sentence":sentence_text,
            })
            return
        
        if annotated:
            args, relative = self._build_args_list(
                sentence_text, frame, frame_name, predicate)
        else:
            args, relative = [], False
        
        return FrameInstance(sentence_text, predicate, args, words, frame_name,
            filename=self.filename, arg_annotated=annotated,
            relative=relative)
    
    def _build_args_list(self, sentence_text, frame, frame_name, predicate):
        """Handle the collection of argument list.
        
        :param sentence_text: Sentence in which the frame occurs.
        :type sentence_text: str.
        :param frame: XML representation of the frame
        :type frame: xml.etree.ElementTree.Element.
        :param frame_name: The name of the FrameNet frame.
        :type frame_name: str.
        :param predicate: The predicate of the frame
        :type predicate: Predicate
        :returns: Argument list, Boolean -- the built argument list, whether this is a relative clause
        """
        
        args = []
        rank = 1
        stop = False
        is_relative = False
        phrase_data = None
        while not stop:
            arg_search_str = self.patterns["arg"].format(self._xmlns, rank)
            arg_data = frame.findall(arg_search_str)
            
            if not self.corpus == "semafor":
                phrase_search_str = self.patterns["pt"].format(self._xmlns, rank)
                phrase_data = frame.findall(phrase_search_str)
            
            # Stop if we have reached a non argument-annotated layer
            if len(arg_data) == 0: break

            for arg in arg_data:
                stop, new_arg = self._build_arg(
                    sentence_text, frame, predicate, arg, phrase_data, rank)
                    
                if new_arg == None: continue
                
                if (self.core_args_only and not
                    FulltextReader.core_arg_finder.is_core_role(
                        new_arg.role, frame_name)
                ):
                    continue
                    
                add = True
                for arg in args[:]:
                    if (arg.role == new_arg.role and
                        arg.phrase_type == new_arg.phrase_type):
                        if arg.text in rel_pronouns:
                            is_relative = True
                            add = False
                        if new_arg.text in rel_pronouns:
                            is_relative = True
                            args.remove(arg)
                
                if add:
                    args.append(new_arg)
                
            rank += 1
            
            # We need to "bypass" the argument layer system for Semafor output
            # because there is always only one layer
            if self.corpus == "semafor": stop = True

        return args, is_relative
    
    def _build_arg(self, sentence_text, frame, predicate, arg, phrase_data, rank):
        # Checks wether the argument is instanciated
        if "itype" in arg.attrib:
            return False, Arg(0, -1, "", arg.attrib["name"], False, "")
        else:          
            arg_start = int(arg.attrib["start"])
            arg_end = int(arg.attrib["end"])
            
            if self.corpus == "semafor":
                phrase_found, phrase_type = True, ""
            else:
                # Stop if we have reached a non phrase-type-annotated layer
                # with at least one instanciated argument
                if len(phrase_data) == 0:
                    self.ignored_layers.append({
                        "file":self.filename,
                        "predicate":predicate.lemma,
                        "sentence": sentence_text,
                        "layer":rank
                    })
                    return True, None
                
                phrase_found, phrase_type = False, ""
                for phrase in phrase_data:
                    phrase_found = (
                        int(phrase.attrib["start"]) == arg_start and
                        int(phrase.attrib["end"]) == arg_end)
                    if phrase_found:
                        phrase_type = phrase.attrib["name"]
                        break
            
            # If the argument and the predicate overlap, mark the argument as NI
            if arg_start <= predicate.end and arg_end >= predicate.begin:
                self.predicate_is_arg.append({
                        "file":self.filename,
                        "predicate":predicate.lemma,
                        "sentence": sentence_text
                    })
                return False, Arg(0, -1, "",  arg.attrib["name"], False, "")
            
            if phrase_found:
                return False, Arg(
                    arg_start, arg_end,
                    sentence_text[arg_start:(arg_end + 1)],
                    arg.attrib["name"], True, phrase_type)
            else:
                self.phrase_not_found.append({
                    "file":self.filename,
                    "predicate":predicate.lemma,
                    "argument":sentence_text[arg_start:(arg_end + 1)],
                    "sentence": sentence_text
                })
                return False, None
    
    def _build_predicate(self, sentence_text, frame):
        """Handle the collection of the predicate data.
        
        :param sentence_text: Sentence in which the frame occurs.
        :type sentence_text: str.
        :param frame: XML representation of the frame
        :type frame: xml.etree.ElementTree.Element.
        :returns: Predicate -- the built predicate
        """
        
        predicate_lemma = None
        if self.constant_predicate == "" and "luName" in frame.attrib:
            predicate_lemma = frame.attrib["luName"].split(".")[0]
        else:
            predicate_lemma = self.constant_predicate
            
        predicate_data = frame.findall(self.patterns["predicate"])[0]
        
        # This test handles the only self-closed layer tag that exists in the corpus
        if len(predicate_data) == 0:
            self.missing_predicate_data.append({
                "file":self.filename,
                "predicate":predicate_lemma,
                "sentence":sentence_text
            })
            return
        else:
            predicate_data = predicate_data[0]
        
        predicate_start = int(predicate_data.attrib["start"])
        predicate_end = int(predicate_data.attrib["end"])
        return Predicate(
            predicate_start,
            predicate_end,
            sentence_text[predicate_start:(predicate_end + 1)],
            predicate_lemma)

    def to_conll_format(self):
        """Outputs all frames to the CoNLL format

        :returns: string, the content of the MST file
        """

        last_sentence = ""

        for frame in self.frames:
            if frame.sentence != last_sentence:
                frame_conll = ""
                i = 0
                for w in frame.words:
                    i += 1
                    frame_conll += "{0}\t{1}\t{1}\t{2}\t{2}\t_\t0\t \t\n".format(
                            i, frame.get_word(w), self.pos_mapping.get(w.pos, w.pos))

                yield frame_conll + "\n"

            last_sentence = frame.sentence
            
class FulltextReaderTest(unittest.TestCase):

    """Unit test class"""
    
    def setUp(self):

        self.expected_values = {
            "NTI__Iran_Introduction.xml":(136,336),
            "ANC__HistoryOfLasVegas.xml":(194,511),
            "NTI__WMDNews_062606.xml":(170,443),
            "NTI__Iran_Missile.xml":(249,662),
            "NTI__NorthKorea_Introduction.xml":(133,358),
            "LUCorpus-v0.3__enron-thread-159550.xml":(67,193),
            "ANC__110CYL069.xml":(1,2),
            "NTI__NorthKorea_NuclearCapabilities.xml":(61,158),
            "NTI__Iran_Nuclear.xml":(220,609),
            "ANC__IntroJamaica.xml":(113,283),
            "ANC__110CYL072.xml":(18,45),
            "LUCorpus-v0.3__wsj_2465.xml":(71,183),
            "LUCorpus-v0.3__sw2025-ms98-a-trans.ascii-1-NEW.xml":(136,288),
            "ANC__110CYL200.xml":(34,82),
            "NTI__Syria_NuclearOverview.xml":(103,282),
            "LUCorpus-v0.3__AFGP-2002-602187-Trans.xml":(50,129),
            "LUCorpus-v0.3__CNN_ENG_20030614_173123.4-NEW-1.xml":(52,124),
            "ANC__StephanopoulosCrimes.xml":(60,159),
            "Miscellaneous__Hijack.xml":(5,12),
            "LUCorpus-v0.3__AFGP-2002-600002-Trans.xml":(185,464),
            "LUCorpus-v0.3__artb_004_A1_E2_NEW.xml":(17,45),
            "Miscellaneous__SadatAssassination.xml":(12,38),
            "NTI__WMDNews_042106.xml":(106,277),
            "ANC__112C-L013.xml":(36,90),
            "LUCorpus-v0.3__20000419_apw_eng-NEW.xml":(25,63),
            "PropBank__LomaPrieta.xml":(162,389),
            "KBEval__atm.xml":(101,267),
            "KBEval__Brandeis.xml":(22,55),
            "NTI__Russia_Introduction.xml":(66,167),
            "LUCorpus-v0.3__artb_004_A1_E1_NEW.xml":(16,43),
            "NTI__LibyaCountry1.xml":(82,239),
            "NTI__BWTutorial_chapter1.xml":(184,448),
            "KBEval__parc.xml":(57,150),
            "LUCorpus-v0.3__ENRON-pearson-email-25jul02.xml":(4,9),
            "KBEval__cycorp.xml":(16,38),
            "Miscellaneous__Hound-Ch14.xml":(19,41),
            "PropBank__BellRinging.xml":(144,348),
            "NTI__NorthKorea_NuclearOverview.xml":(299,781),
            "LUCorpus-v0.3__20000420_xin_eng-NEW.xml":(20,52),
            "NTI__Iran_Chemical.xml":(246,682),
            "NTI__Taiwan_Introduction.xml":(48,127),
            "LUCorpus-v0.3__wsj_1640.mrg-NEW.xml":(43,100),
            "QA__IranRelatedQuestions.xml":(460,1172),
            "ANC__EntrepreneurAsMadonna.xml":(67,175),
            "KBEval__LCC-M.xml":(81,217),
            "LUCorpus-v0.3__20000424_nyt-NEW.xml":(5,13),
            "LUCorpus-v0.3__602CZL285-1.xml":(22,59),
            "LUCorpus-v0.3__CNN_AARONBROWN_ENG_20051101_215800.partial-NEW.xml":(89,219),
            "KBEval__MIT.xml":(77,204),
            "KBEval__utd-icsi.xml":(107,245),
            "ANC__IntroHongKong.xml":(40,97),
            "LUCorpus-v0.3__20000416_xin_eng-NEW.xml":(38,106),
            "NTI__Iran_Biological.xml":(154,385),
            "PropBank__TicketSplitting.xml":(87,217),
            "PropBank__AetnaLifeAndCasualty.xml":(13,37),
            "ANC__110CYL070.xml":(24,66),
            "C-4__C-4Text.xml":(25,69),
            "NTI__SouthAfrica_Introduction.xml":(117,321),
            "KBEval__lcch.xml":(183,500),
            "LUCorpus-v0.3__SNO-525.xml":(23,52),
            "SemAnno__Text1.xml":(12,43),
            "NTI__Kazakhstan.xml":(33,90),
            "KBEval__Stanford.xml":(46,119),
            "NTI__NorthKorea_ChemicalOverview.xml":(108,285),
            "ANC__WhereToHongKong.xml":(163,388),
            "ANC__HistoryOfJerusalem.xml":(190,497),
            "ANC__110CYL067.xml":(28,63),
            "ANC__110CYL068.xml":(60,157),
            "PropBank__ElectionVictory.xml":(58,151),
            "LUCorpus-v0.3__AFGP-2002-600045-Trans.xml":(80,190),
            "LUCorpus-v0.3__20000410_nyt-NEW.xml":(27,69),
            "LUCorpus-v0.3__IZ-060316-01-Trans-1.xml":(78,186)
        }
        
        self.tested_frames = [
            FrameInstance(
                ("Rep . Tony Hall , D- Ohio , urges the United Nations to allow"
                " a freer flow of food and medicine into Iraq .").lower(),
                Predicate(28, 32, "urges", "urge"),
                [
                    Arg(34, 51, "the United Nations", "Addressee", True, "NP"),
                    Arg(53, 104,
                        "to allow a freer flow of food and medicine into Iraq",
                        "Content", True, "VPto"),
                    Arg(0, 26, "Rep . Tony Hall , D- Ohio", "Speaker", True, "NP")
                ],
                [
                    Word(0, 2, "NN"), Word(4, 4, "."), Word(6, 9, "NP"),
                    Word(11, 14, "NP"), Word(16, 16, ","), Word(18, 19, "NN"),
                    Word(21, 24, "NP"), Word(26, 26, ","), Word(28, 32, "VVZ"),
                    Word(34, 36, "DT"), Word(38, 43, "NP"), Word(45, 51, "NPS"),
                    Word(53, 54, "TO"), Word(56, 60, "VV"), Word(62, 62, "DT"),
                    Word(64, 68, "JJR"), Word(70, 73, "NN"), Word(75, 76, "IN"),
                    Word(78, 81, "NN"), Word(83, 85, "CC"), Word(87, 94, "NN"),
                    Word(96, 99, "IN"), Word(101, 104, "NP"), Word(106, 106, ".")
                ],
                "Attempt_suasion" ),
            FrameInstance(
                ("Rep . Tony Hall , D- Ohio , urges the United Nations to allow"
                " a freer flow of food and medicine into Iraq .").lower(),
                 Predicate(56, 60, "allow", "allow"),
                 [
                    Arg(62, 104,
                        "a freer flow of food and medicine into Iraq",
                        "Action", True, "NP"),
                    Arg(34, 51, "the United Nations", "Grantee", True, "NP"),
                    Arg(0, -1, "", "Grantor", False, "")
                 ],
                 [
                    Word(0, 2, "NN"), Word(4, 4, "."), Word(6, 9, "NP"),
                    Word(11, 14, "NP"), Word(16, 16, ","), Word(18, 19, "NN"),
                    Word(21, 24, "NP"), Word(26, 26, ","), Word(28, 32, "VVZ"),
                    Word(34, 36, "DT"), Word(38, 43, "NP"),
                    Word(45, 51, "NPS"), Word(53, 54, "TO"),
                    Word(56, 60, "VV"), Word(62, 62, "DT"),
                    Word(64, 68, "JJR"), Word(70, 73, "NN"),
                    Word(75, 76, "IN"), Word(78, 81, "NN"), Word(83, 85, "CC"),
                    Word(87, 94, "NN"), Word(96, 99, "IN"),
                    Word(101, 104, "NP"), Word(106, 106, ".")
                 ],
                "Grant_permission" ) ]
            

    def test_global(self):
        """Checks that no exception is raised and that
        no obvious errors occurs while parsing the whole corpus
        
        """
        
        for filename in self.expected_values:
            print("Parsing " + filename)
            reader = FulltextReader(options.fulltext_corpus + filename)

            # Nothing is empty and begins/ends are coherents
            arg_num = 0
            for frame in reader.frames:
                self.assertNotEqual(frame.predicate.text, "")
                self.assertEqual(
                    frame.predicate.text,
                    frame.sentence[frame.predicate.begin:(frame.predicate.end + 1)])
                    
                arg_num += len(frame.args)
                last_arg = None
                for arg in frame.args:
                    # Instanciated arguments must contain something
                    self.assertTrue(arg.text != "" or arg.instanciated == False)
                    # Begin, end and text must be coherent
                    self.assertEqual(
                        arg.text,
                        frame.sentence[arg.begin:(arg.end + 1)])
                    # The argument order must be correct (uninstanciated args last)
                    self.assertTrue(
                        last_arg == None or # Nothing to test or
                        (
                            # begin after the previous arg's begin (or not instanciated) and
                            (last_arg.begin <= arg.begin or arg.instanciated == False) and
                            # no instanciated args allowed after an uninstanciated arg
                            (arg.instanciated == False or last_arg.instanciated == True)
                        )
                    )
                    last_arg = arg
                            
            # The total number of frames and args is correct
            good_frame_num, good_arg_num = self.expected_values[filename]
            
            self.assertEqual(len(reader.frames), good_frame_num)
            self.assertEqual(arg_num, good_arg_num)
            print("Found {} frames and {} arguments: ok".format(
                len(reader.frames), arg_num))
    def test_specific_frames(self):
        """Checks that some particular frames are correctly parsed"""
        path = options.fulltext_corpus + "LUCorpus-v0.3__20000424_nyt-NEW.xml"
        reader = FulltextReader(path)
        self.assertEqual(reader.frames[0], self.tested_frames[0])
        self.assertEqual(reader.frames[1], self.tested_frames[1])

    def test_conll_output(self):
        path = options.fulltext_corpus + "LUCorpus-v0.3__20000424_nyt-NEW.xml"
        reader = FulltextReader(path)
        conll_sentence = next(reader.to_conll_format()).splitlines()
        self.assertEqual(conll_sentence[2], "3\ttony\ttony\tNNP\tNNP\t_\t0\t \t")
        self.assertEqual(conll_sentence[23], "24\t.\t.\t.\t.\t_\t0\t \t")

if __name__ == "__main__":
    if 'conll' in sys.argv:
        for p in glob.glob(paths.FRAMENET + "/*.xml"):
            name = os.path.basename(p)[:-4]
            with open('framenet_conll/{}.conll'.format(name), 'w') as conll_file:
                for conll_sentence in FulltextReader(p).to_conll_format():
                    conll_file.write(conll_sentence)
    else:
        unittest.main()

