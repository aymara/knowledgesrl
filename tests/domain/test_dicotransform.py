"""
Tests DicoInfo and DicoEnviro transforms

For example, the roles are changed, the syntax is changed (NP.Agent NP.Agent V -> NP.Agent V).
"""

from xml.etree import ElementTree as ET
import unittest

from domain.extract_syntactic_data import xmlcontext_to_frame, remove_before_v, syntax_to_str, map_gold_frame
from domain.rolemapping import RoleMapping
import paths

class DicoTransforms(unittest.TestCase):
    def test_remove_doubletheme(self):
        context = ET.fromstring("""
            <contexte xmlns="http://olst.ling.umontreal.ca/dicoenviro/">
                <contexte-texte>I compare apples and oranges</contexte-texte>
                <participant type="Act" role="Agent">
                    <fonction-syntaxique nom="Subject">
                        <groupe-syntaxique nom="NP">I</groupe-syntaxique>
                    </fonction-syntaxique>
                </participant>
                 <lexie-att>compare</lexie-att> 
                <participant type="Act" role="Theme">
                    <fonction-syntaxique nom="Object">
                        <groupe-syntaxique nom="NP">apples</groupe-syntaxique>
                    </fonction-syntaxique>
                </participant>
                 and 
                <participant type="Act" role="Theme">
                    <fonction-syntaxique nom="Object">
                        <groupe-syntaxique nom="NP">oranges</groupe-syntaxique>
                    </fonction-syntaxique>
                </participant>
            </contexte>
            """)
        sentence_text, frame = xmlcontext_to_frame(
            "http://olst.ling.umontreal.ca/dicoenviro/", 'compare', context)

        vn_frame = ET.fromstring(
            """<SYNTAX><NP value="Agent" /><VERB /><NP value="Theme" /></SYNTAX>""")
        self.assertEqual(syntax_to_str(frame), syntax_to_str(vn_frame))

    def test_remove_before_verb(self):
        """
        Whenever we detect that the sentence starts with a verb, we'll remove it from
        the VerbNet syntax
        """
        from nltk.corpus import verbnet

        buy_first_classid = verbnet.classids('buy')[0]
        buy_first_syntax = verbnet.vnclass(buy_first_classid).find('FRAMES/FRAME/SYNTAX')

        altered_syntax = remove_before_v(buy_first_syntax)
        wanted_syntax = ET.fromstring("""<SYNTAX><VERB /><NP value="Theme" /></SYNTAX>""")

        self.assertEqual(syntax_to_str(altered_syntax), syntax_to_str(wanted_syntax))

    def test_map_dico_gold_frame(self):
        """Map DiCo roles to VerbNet roles"""
        # scribble / print

        dico = {'domain': 'info', 'lang': 'en'}
        role_mapping = RoleMapping(str(paths.ROOT / paths.DICO_MAPPING.format(**dico)))

        gold_syntax = ET.fromstring(
            """<SYNTAX><NP value="Instrument" /><VERB /><NP value="Patient" /></SYNTAX>""")
        mapped_gold_syntax = map_gold_frame('scribble-25.2', gold_syntax, role_mapping['print.1a'])
        self.assertEqual(syntax_to_str(mapped_gold_syntax), 'NP.Agent V NP.Theme')
