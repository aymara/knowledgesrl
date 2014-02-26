#!/usr/bin/env python3

from xml.etree import ElementTree as ET
from collections import UserDict

class RoleMapping(UserDict):
    def __init__(self, filename):
        super().__init__()
        tree = ET.ElementTree(file=filename)
        for lexie in tree.findall('LEXIE'):
            self.data[lexie.get('name')] = {}
            for role in lexie.findall('role'):
                self.data[lexie.get('name')][role.get('dico')] = role.get('vn')
