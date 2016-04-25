#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Contains all shared paths in one module for easy maintenance"""

from pathlib import Path
import optionsparsing

class Paths:
    
    ROOT = Path(__file__).parent.parent / "data"

    FRAMENET_PARSED = ROOT / "framenet_parsed/"
    FRAMENET_LU_PARSED = ROOT / "lu_parsed/"

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

    @staticmethod
    def framenet_path(language):
        if language == 'fre':
            return Paths.ROOT / "fndata-asfalda/"
        elif language == 'eng':
            return Paths.ROOT / "fndata-1.5/"
        else:
            print("Unhandled language {}".format(value))
            exit(1)

    @staticmethod
    def verbnet_path(language):
        if language == 'fre':
            return Paths.ROOT / "verbenet/verbenet/"
        elif language == 'eng':
            return Paths.ROOT / "verbnet/"
        else:
            print("Unhandled language {}".format(language))
            exit(1)

    @staticmethod
    def framenet_fulltext(language):
        return Paths.framenet_path(language) / "fulltext/"
    
    @staticmethod
    def framenet_lu(language):
        return Paths.framenet_path(language) / "lu/"
    
    @staticmethod
    def framenet_frames(language):
        return Paths.framenet_path(language) / "frame/"
    