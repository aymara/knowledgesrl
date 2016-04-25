#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import options
import semanticrolelabeler

if __name__ == "__main__":
    result = semanticrolelabeler.SemanticRoleLabeller(sys.argv[1:]).annotate()
    if options.Options.conll_output is None:
        print(result)
