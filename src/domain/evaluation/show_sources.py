#!/usr/bin/env python3
"""
Print every source as many times as they appear

Applies to a dico context file such as dicoinfo_en.xml
"""

import sys
from xml.etree import ElementTree as ET

dico = ET.ElementTree(file=sys.argv[1])

_dicoinfo_xmlns = 'http://olst.ling.umontreal.ca/dicoinfo/'
_dicoenviro_xmlns = 'http://olst.ling.umontreal.ca/dicoenviro/'

if 'info' in sys.argv[1]:
    xmlns = _dicoinfo_xmlns
else:
    xmlns = _dicoenviro_xmlns

for contexte in dico.findall('lexie/contextes/{{{0}}}contexte'.format(xmlns)):
    print(contexte.get('source'))
