#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from framenetreader import FulltextReader
from conllreader import SyntacticTreeBuilder, SyntacticTreeNode
import glob
import os


def get_trees(filename):
    # get data from parse trees
    trees = []
    with open("framenet_parsed/{}.conll".format(filename)) as conll_file:
        conll_tree = ""
        for l in conll_file.readlines():
            if l != "\n":
                conll_tree += l
            else:
                trees.append(SyntacticTreeBuilder(conll_tree).build_syntactic_tree())
                conll_tree = ""

    return trees

if __name__ == '__main__':
    correct, partial_credit, total = 0, 0, 0

    # get data from FrameNet arguments
    for fulltext_file in glob.glob("{}/*.xml".format(FulltextReader.FN_BASEPATH)):
        reader = FulltextReader(fulltext_file)
        trees = get_trees(".".join(os.path.basename(fulltext_file).split(".")[:-1]))

        # for each argument, see if it is in a parse tree. if yes +1
        for frame in reader.frames:
            frame_text = " ".join([frame.get_word(w) for w in frame.words])
            for t in trees:
                if t.flat() == frame_text:
                    for arg in frame.args:
                        if arg.text != "":
                            total += 1
                            arg_len = len(arg.text.split())
                            match_len = len(t.closest_match(arg.text))
                            partial_credit += 1 - abs(arg_len - match_len) / max(arg_len, match_len)
                            if t.contains(arg.text):
                                correct += 1
                    break
        
    print("{}/{} = {}".format(correct, total, correct/total))
    print("{}/{} = {}".format(partial_credit, total, partial_credit/total))
