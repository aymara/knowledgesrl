"""
Tests DicoInfo and DicoEnviro transforms

For example, the roles are changed, the syntax is changed (NP.Agent NP.Agent V -> NP.Agent V).
"""

import unittest
from xml.etree import ElementTree as ET

import verbnet
from .extract_syntactic_data import xmlcontext_to_frame, remove_before_v

class RemoveDoubleRoleFillers(unittest.TestCase):
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

        sentence_text, frame = xmlcontext_to_frame("http://olst.ling.umontreal.ca/dicoenviro/", 'compare', context)
        self.assertEqual(frame, [{'type': 'NP', 'role': 'Agent'}, {'type': 'V'}, {'type': 'NP', 'role': 'Theme'}])

class RemoveRolesBeforeVerb(unittest.TestCase):
    def test_remove_before_verb(self):
        """
        Whenever we detect that the sentence starts with a verb, we'll remove it from
        the VerbNet syntax
        """

        buy_first_frame = verbnet.classes_for_predicate['buy'][0].frames[0]
        self.assertEqual(remove_before_v(buy_first_frame).syntax, [{'type': 'V'}, {'type': 'NP', 'role': 'Theme'}])
