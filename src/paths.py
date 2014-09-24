#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains all shared paths in one module for easy maintenance"""

from pathlib import Path


ROOT = Path(__file__).parent.parent / "data"

FRAMENET = ROOT / "fndata-1.5/"
FRAMENET_FULLTEXT = FRAMENET / "fulltext/"
FRAMENET_LU = FRAMENET / "lu/"
FRAMENET_FULLTEXT_EVALUATION = FRAMENET / "fulltext/evaluation/"
FRAMENET_FRAMES = FRAMENET / "frame/"
FRAMENET_PARSED = ROOT / "framenet_parsed/"
FRAMENET_LU_PARSED = ROOT / "lu_parsed/"
FRAMENET_PARSED_EVALUATION = ROOT / "framenet_parsed/evaluation/"

VERBNET_PATH = ROOT / "verbnet/"

VNFN_MATCHING = ROOT / "vn-fn-roles.xml"

_dicoenviro_xmlns = 'http://olst.ling.umontreal.ca/dicoenviro/'
_dicoinfo_xmlns = 'http://olst.ling.umontreal.ca/dicoinfo/'

DICOS = [
    {
        'name': 'enviro_en',
        'root': ROOT / 'domain/enviro',
        'xml': ROOT / 'domain/contextes_olst/dicoenviro_en.xml',
        'xmlns': _dicoenviro_xmlns,
        'mapping':  'enviro-vn-roles.xml',
        'train': 'train_enviro_en.pickle',
        'test': 'test_enviro_en.pickle',
    },
    {
        'name': 'info_en',
        'root': ROOT / 'domain/info/',
        'xml': ROOT / 'domain/contextes_olst/dicoinfo_en.xml',
        'xmlns': _dicoinfo_xmlns,
        'mapping': 'info-vn-roles.xml',
        'train': 'train_info_en.pickle',
        'test': 'test_info_en.pickle',
    },
    #{
    #    'name': 'enviro_fr',
    #    'root': ROOT / 'domain/enviro',
    #    'xml': ROOT / 'domain/contextes_olst/dicoenviro_fr.xml',
    #    'xmlns': _dicoenviro_xmlns,
    #    'mapping':  'enviro-vn-roles.xml',
    #    'train': 'train_enviro_fr.pickle',
    #    'test': 'test_enviro_fr.pickle',
    #},
    #{
    #    'name': 'info_fr',
    #    'root': ROOT / 'domain/info/',
    #    'xml': ROOT / 'domain/contextes_olst/dicoinfo_en.xml',
    #    'xmlns': _dicoinfo_xmlns,
    #    'mapping': 'info-vn-roles.xml',
    #    'train': 'train_info_fr.pickle',
    #    'test': 'test_info_fr.pickle',
    #},
]

ALL_LUS = ROOT / 'domain/kicktionary/All_LUs.xml'
KICKTIONARY_SETS = ROOT / 'domain/kicktionary/{}_kicktionary_{}.pickle'
KICKTIONARY_ROLES = ROOT / 'domain/kicktionary/kicktionary-vn-roles.xml'
