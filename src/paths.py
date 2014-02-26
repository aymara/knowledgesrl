#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Regrouping all shared paths in one module to make maintenance easier"""

ROOT = "../data/"

FRAMENET = ROOT + "fndata-1.5/"
FRAMENET_FULLTEXT = FRAMENET + "fulltext/"
FRAMENET_LU = FRAMENET + "lu/"
FRAMENET_FULLTEXT_EVALUATION = FRAMENET + "fulltext/evaluation/"
FRAMENET_FRAMES = FRAMENET + "frame/"
FRAMENET_PARSED = ROOT + "framenet_parsed/"
FRAMENET_LU_PARSED = ROOT + "lu_parsed/"
FRAMENET_PARSED_EVALUATION = ROOT + "framenet_parsed/evaluation/"

VERBNET_PATH = ROOT + "verbnet/"

VNFN_MATCHING = ROOT + "vn-fn-roles.xml"

_dicoenviro_xmlns = 'http://olst.ling.umontreal.ca/dicoenviro/'
_dicoinfo_xmlns = 'http://olst.ling.umontreal.ca/dicoinfo/'

DICOS = [
    (ROOT + 'domain/info/dicoinfo_en.xml', _dicoinfo_xmlns, ROOT + 'domain/info/info-vn-roles.xml'),
    #(ROOT + 'domain/info/dicoinfo_fr.xml', _dicoinfo_xmlns),
    (ROOT + 'domain/enviro/dicoenviro_en.xml', _dicoenviro_xmlns, ROOT + 'domain/enviro/enviro-vn-roles.xml'),
    #(ROOT + 'domain/enviro/' + 'dicoenviro_fr.xml', _dicoenviro_xmlns),
]
