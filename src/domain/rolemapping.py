#!/usr/bin/env python3

from xml.etree import ElementTree as ET
from collections import UserDict


class RoleMapping(UserDict):
    def __init__(self, filename):
        super().__init__()
        tree = ET.ElementTree(file=str(filename))
        for lexie in tree.findall('lexie'):
            self.data[lexie.get('name')] = {lexie.get('vn'): {}}
            for role in lexie.findall('role'):
                self.data[lexie.get('name')][lexie.get('vn')][role.get('name')] = role.get('vn')
