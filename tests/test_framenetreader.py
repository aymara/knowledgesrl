#!/usr/bin/env python3

import unittest

from framenetreader import FulltextReader
from framenetframe import FrameInstance, Predicate, Word, Arg
import options
import paths
            
class FulltextReaderTest(unittest.TestCase):

    """Unit test class"""
    
    def setUp(self):

        self.expected_values = {
            "ANC__110CYL069.xml":(1,2),
            "ANC__110CYL070.xml":(24,66),
            "ANC__110CYL072.xml":(18,45),
            "ANC__110CYL200.xml":(34,82),
            "ANC__EntrepreneurAsMadonna.xml":(67,175),
            "ANC__HistoryOfGreece.xml":(249,693),
            "ANC__HistoryOfJerusalem.xml":(190,497),
            "ANC__HistoryOfLasVegas.xml":(194,511),
            "ANC__IntroJamaica.xml":(113,283),
            "ANC__IntroOfDublin.xml": (80, 200),
            "C-4__C-4Text.xml":(25,69),
            "KBEval__lcch.xml":(183,500),
            "KBEval__LCC-M.xml":(81,217),
            "KBEval__MIT.xml":(77,204),
            "LUCorpus-v0.3__20000415_apw_eng-NEW.xml":(38,101),
            "LUCorpus-v0.3__20000416_xin_eng-NEW.xml":(38,106),
            "LUCorpus-v0.3__20000419_apw_eng-NEW.xml":(25,63),
            "LUCorpus-v0.3__20000420_xin_eng-NEW.xml":(20,52),
            "LUCorpus-v0.3__20000424_nyt-NEW.xml":(5,13),
            "LUCorpus-v0.3__602CZL285-1.xml":(22,59),
            "LUCorpus-v0.3__AFGP-2002-600002-Trans.xml":(185,464),
            "LUCorpus-v0.3__AFGP-2002-600045-Trans.xml":(80,190),
            "LUCorpus-v0.3__artb_004_A1_E1_NEW.xml":(16,43),
            "LUCorpus-v0.3__artb_004_A1_E2_NEW.xml":(17,45),
            "LUCorpus-v0.3__CNN_AARONBROWN_ENG_20051101_215800.partial-NEW.xml":(89,219),
            "LUCorpus-v0.3__CNN_ENG_20030614_173123.4-NEW-1.xml":(52,124),
            "LUCorpus-v0.3__ENRON-pearson-email-25jul02.xml":(4,9),
            "LUCorpus-v0.3__wsj_1640.mrg-NEW.xml":(43,100),
            "LUCorpus-v0.3__wsj_2465.xml":(71,183),
            "Miscellaneous__Hijack.xml":(5,12),
            "NTI__BWTutorial_chapter1.xml":(184,448),
            "NTI__ChinaOverview.xml":(80,211),
            "NTI__Iran_Biological.xml":(154,385),
            "NTI__Iran_Chemical.xml":(246,682),
            "NTI__Iran_Introduction.xml":(136,336),
            "NTI__Iran_Missile.xml":(249,662),
            "NTI__Iran_Nuclear.xml":(220,609),
            "NTI__Kazakhstan.xml":(33,90),
            "NTI__LibyaCountry1.xml":(82,239),
            "NTI__NorthKorea_ChemicalOverview.xml":(108,285),
            "NTI__NorthKorea_NuclearCapabilities.xml":(61,158),
            "NTI__NorthKorea_NuclearOverview.xml":(299,781),
            "NTI__Russia_Introduction.xml":(66,167),
            "NTI__SouthAfrica_Introduction.xml":(117,321),
            "NTI__Taiwan_Introduction.xml":(48,127),
            "NTI__WMDNews_042106.xml":(106,277),
            "NTI__WMDNews_062606.xml":(170,443),
            "NTI__workAdvances.xml":(46,124),
            "PropBank__BellRinging.xml":(144,348),
            "PropBank__ElectionVictory.xml":(58,151),
            "PropBank__LomaPrieta.xml":(162,389),
            "PropBank__PolemicProgressiveEducation.xml":(138,353),
            "PropBank__TicketSplitting.xml":(87,217),
            "QA__IranRelatedQuestions.xml":(460,1172),
            "SemAnno__Text1.xml":(12,43),
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

        for filename in sorted(self.expected_values):
            reader = FulltextReader(paths.Paths.framenet_fulltext("eng") / filename)

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
    def test_specific_frames(self):
        """Checks that some particular frames are correctly parsed"""
        path = paths.Paths.framenet_fulltext("eng") / "LUCorpus-v0.3__20000424_nyt-NEW.xml"
        reader = FulltextReader(path)
        self.assertEqual(reader.frames[0], self.tested_frames[0])
        self.assertEqual(reader.frames[1], self.tested_frames[1])

    def test_conll_output(self):
        path = paths.Paths.framenet_fulltext("eng") / "LUCorpus-v0.3__20000424_nyt-NEW.xml"
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
