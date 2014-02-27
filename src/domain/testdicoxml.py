"""Tests the dicoxml functions"""

import unittest
from xml.etree import ElementTree as ET

from domain.dicoxml import deindent_text, get_all_text

class ParseDicoText(unittest.TestCase):
    maxDiff = None

    def test_getalltext(self):
        ab_text = ET.fromstring("<a>text1 <b>text2</b> text3 <b>text4</b> text5</a>")
        self.assertEqual(get_all_text(ab_text), "text1 text2 text3 text4 text5")

        dico_text = ET.fromstring("""
                <participant type="Act" role="Patient">
                    <fonction-syntaxique nom="Object">
                        <groupe-syntaxique nom="NP">
                a
                            <realisation>file</realisation>
                        </groupe-syntaxique>
                    </fonction-syntaxique>
                </participant>
        """)
        self.assertEqual(get_all_text(dico_text), "a file")

    def test_deindent(self):
        indented_sentence = """Anyone who downloaded the document and
                    opened it would trigger the virus."""
        self.assertEqual(deindent_text(indented_sentence), "Anyone who downloaded the document and opened it would trigger the virus.")

        indented_sentence = """La protection et le renforcement des puits et
                des réservoirs de gaz à effet de serre figure parmi les méthodes recensées par
                le Protocole de Kyoto pour lutter contre les émissions de gaz à effet de serre,
                ainsi que la promotion des méthodes durables de gestion forestière, de
                boisement et de reboisement."""

        self.assertEqual(
            deindent_text(indented_sentence),
            "La protection et le renforcement des puits et des"
            " réservoirs de gaz à effet de serre figure parmi les méthodes recensées par le"
            " Protocole de Kyoto pour lutter contre les émissions de gaz à effet de serre,"
            " ainsi que la promotion des méthodes durables de gestion forestière, de"
            " boisement et de reboisement.")

        indented_sentence = "This is short\tsentence."
        self.assertEqual(deindent_text(indented_sentence), indented_sentence)

        indented_sentence = """
                    Starts with a newline"""
        self.assertEqual(deindent_text(indented_sentence), "Starts with a newline")

