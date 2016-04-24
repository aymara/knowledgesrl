#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import optionsparsing
myoptions = optionsparsing.Options(sys.argv[1:])
import semanticrolelabeller
import options

if __name__ == "__main__":
    result = semanticrolelabeller.SemanticRoleLabeller(sys.argv).annotate()
    if options.conll_output is None:
        print(result)
