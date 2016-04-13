#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains all shared paths in one module for easy maintenance"""

from pathlib import Path


ROOT = Path(__file__).parent.parent / "data"

#FRAMENET = ROOT / "fndata-1.5/"
FRAMENET = ROOT / "fndata-asfalda/"
FRAMENET_FULLTEXT = FRAMENET / "fulltext/"
FRAMENET_LU = FRAMENET / "lu/"
FRAMENET_FRAMES = FRAMENET / "frame/"
FRAMENET_PARSED = ROOT / "framenet_parsed/"
FRAMENET_LU_PARSED = ROOT / "lu_parsed/"

#VERBNET_PATH = ROOT / "verbnet/"
VERBNET_PATH = ROOT / "verbenet/verbenet/"

VNFN_MATCHING = ROOT / "vn-fn-roles.xml"

# Domain
DICO_XML = 'domain/contextes_olst/dico{domain}_{lang}.xml'
DICO_XMLNS = {
    'enviro': 'http://olst.ling.umontreal.ca/dicoenviro/',
    'info': 'http://olst.ling.umontreal.ca/dicoinfo/'
}
DICO_MAPPING = 'domain/{domain}/vnroles_{domain}_{lang}.xml'
DICO_TRAIN = 'domain/{domain}/train_{domain}_{lang}.json'
DICO_TEST = 'domain/{domain}/test_{domain}_{lang}.json'

ALL_LUS = ROOT / 'domain/kicktionary/All_LUs.xml'
KICKTIONARY_SETS = 'domain/kicktionary/{}_kicktionary_{}.json'
KICKTIONARY_ROLES = ROOT / 'domain/kicktionary/vnroles_kicktionary_{}.xml'
