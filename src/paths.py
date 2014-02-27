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
    {
        'root': ROOT + 'domain/info/',
        'xml': 'dicoinfo_en.xml',
        'xmlns': _dicoinfo_xmlns,
        'mapping': 'info-vn-roles.xml',
        'train': 'train_info_en.pickle',
        'dev': 'test_info_en.pickle',
        'test': 'test_info_en.pickle',
    },

    # TODO french info

    {
        'root': ROOT + 'domain/enviro',
        'xml': 'dicoenviro_en.xml',
        'xmlns': _dicoenviro_xmlns,
        'mapping':  'enviro-vn-roles.xml',
        'train': 'train_enviro_en.pickle',
        'dev': 'test_enviro_en.pickle',
        'test': 'test_enviro_en.pickle',
    },

    # TODO french enviro
]
