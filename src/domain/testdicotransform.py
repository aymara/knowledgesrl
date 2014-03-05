"""
Tests DicoInfo and DicoEnviro transforms

For example, the roles are changed, the syntax is changed (NP.Agent NP.Agent V -> NP.Agent V).
"""

import unittest
from xml.etree import ElementTree as ET

from .extract_syntactic_data import xmlcontext_to_frame

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

        hash, frame = xmlcontext_to_frame("http://olst.ling.umontreal.ca/dicoenviro/", 'compare', context)
        self.assertEqual(frame, [{'type': 'NP', 'role': 'Agent'}, {'type': 'V'}, {'type': 'NP', 'role': 'Theme'}])
