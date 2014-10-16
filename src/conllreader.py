#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Build syntactic trees from CoNLL parser output"""


class ConllInvalidPositionError(Exception):
    """Trying to build a subtree from a node that does not exist
    
    :var bad_root: integer, the position from which we attempted to build a subtree
    :var max_root: integer, the last valid position
    
    """
    
    def __init__(self, bad_root, max_root):
        self.bad_root = bad_root
        self.max_root = max_root
        
    def __str__(self):
        return "Error : tried to build a subtree from position {} while"\
               " parsing CoNLL output (last valid position was {})".format(
                self.bad_root, self.max_root)

class SyntacticTreeNode:
    """A node (internal or terminal) of a syntactic tree
    
    :var word_id: int, the CoNLL word id (starts at 1)

    :var word: string, the word contained by the node
    :var pos: part-of-speech of the node

    :var deprel: string, function attributed by the parser to this word
    :var father: SyntacticTreeBuilder, the father of this node
    :var children: SyntacticTreeNode list, the children of this node

    :var begin: int, the character position this phrase starts at (root would be 0)
    :var end: int, the position this phrase ends at (root would be last character)
    :var begin_word: int, the position this *word* begins at
    
    """
    
    def __init__(self, word_id, word, pos, deprel, begin_word):
        self.word_id = word_id

        self.word = word
        self.pos = pos

        self.deprel = deprel
        self.father = None
        self.children = []

        self.begin_word = begin_word
        self.begin, self.end = None, None
                
    def __repr__(self):
        if self.children:
            children = " " + " ".join([str(t) for t in self.children])
        else:
            children = ""

        return "({}/{}/{}/{}/{} {}{})".format(self.pos, self.deprel, self.position, self.begin, self.end, self.word, children)

    def __iter__(self):
        for position, child in enumerate(self.children):
            if position == self.position:
                yield(self)
            for node in child:
                yield node
        if self.position == len(self.children):
            yield self
    
    def flat(self):
        """Return the tokenized sentence from the parse tree."""
        return " ".join([x.word for x in self])

    def contains(self, arg):
        """Search an exact argument in all subtrees"""
        return (self.flat() == arg or
            any((c.contains(arg) for c in self.children)))

    def closest_match(self, arg):
        """Search the closest match to arg"""
        return self.closest_match_as_node(arg).flat().split()

    def closest_match_as_node(self, arg):
        return self._closest_match_as_node_lcs(arg)[1]

    def _closest_match_as_node_lcs(self, arg):
        from distance import lcsubstrings as word_overlap

        root_match = self.flat().split()
        root_match_len = (
            len(word_overlap(tuple(root_match), tuple(arg.text.split()))) /
            (len(root_match) + len(arg.text.split())))
        children_results = [c._closest_match_as_node_lcs(arg) for c in self.children]
        return max([(root_match_len, self)] + children_results, key = lambda x: x[0])

class SyntacticTreeBuilder():
    """Wrapper class for the building of a syntactic tree

    :var node_dict: every SyntacticTreeNode available by CoNLL word id
    :var father_ids: every dependency relation: child id -> father id
    :var tree_list: every root node, that is every root subtree
    :var sentence: the "sentence" (words separated by spaces)

    """

    def __init__(self, conll_tree):
        """Extract the data provided
        
        :param conll_tree: The output of the CoNLL parser
        :type conll_tree: str
        
        """
        self.node_dict, self.father_ids = {}, {}
        self.tree_list = []
        
        begin = 0
        for l in conll_tree.splitlines():
            word_id, form, lemma, cpos, pos, feat, head, deprel, *junk = l.split("\t")
            
            word_id = int(word_id)
            head = int(head) if head != '-' else None
            deprel = deprel if deprel != '-' else 'ROOT'

            self.father_ids[word_id] = head

            self.node_dict[word_id] = SyntacticTreeNode(
                word_id=word_id,
                word=form, pos=cpos,
                deprel=deprel,
                begin_word=begin)

            begin += 1 + len(form)

        self.sentence = ' '.join([self.node_dict[word_id].word for word_id in sorted(self.node_dict.keys())])

        # Record father/child relationship
        for word_id, father_id in self.father_ids.items():
            if father_id is not None and father_id != 0:
                self.node_dict[word_id].father = self.node_dict[father_id]
                self.node_dict[father_id].children.append(self.node_dict[word_id])

        # Record position: where is father among child? Important to flatten tree
        for father in self.node_dict.values():
            father.position = 0
            for child_id, child in enumerate(father.children):
                if child.begin_word > father.begin_word:
                    father.position = child_id
                    break
                father.position = len(father.children)

        for node in self.node_dict.values():
            if node.father is None:
                # Fill begin/end info
                #import pudb; pu.db
                self.fill_begin_end(node)
                # Fill forest of tree
                self.tree_list.append(node)

    def fill_begin_end(self, node):
        """Fill begin/end values of very subtree"""
        begin_words = [node.begin_word]
        end_words = [node.begin_word + len(node.word) - 1]
        for child in node.children:
            self.fill_begin_end(child)
            begin_words.append(child.begin)
            end_words.append(child.end)
        node.begin = min(begin_words)
        node.end = max(end_words)


class ConllSemanticAppender():
    """Appends semantic information at the "right" of a ConLL file.

    The input is a syntactic ConLL file, and the output a so-called semantic
    CoNLL file.
    """

    def __init__(self, syntactic_conll_file):
        self.conll_matrix = []

        with open(syntactic_conll_file) as content:
            sentences_data = content.read().split("\n\n")

            for sentence in sentences_data:
                sentence_matrix = []
                for line in sentence.split('\n'):
                    if len(line.split('\t')) == 1:
                        continue
                    # Put current line plus a line for potential frame annotations
                    sentence_matrix.append(line.split('\t') + ['-'])
                self.conll_matrix.append(sentence_matrix)

    def add_new_column(self, sentence_id):
        for line in self.conll_matrix[sentence_id]:
            line.append('-')

    def add_frame_annotation(self, frame_annotation):
        # We could have multiple classes, so join them with |
        self.conll_matrix[frame_annotation.sentence_id][frame_annotation.predicate_position-1][10] = '|'.join(frame_annotation.best_classes)
        # Add new column to place the new roles
        self.add_new_column(frame_annotation.sentence_id)

        for roleset, arg in zip(frame_annotation.roles, frame_annotation.args):
            roleset_str = '|'.join(roleset) if roleset else '_EMPTYROLE_'
            self.conll_matrix[frame_annotation.sentence_id][arg.position-1][-1] = roleset_str

    def dump_semantic_file(self, filename):
        with open(filename, 'w') as semantic_file:
            for i, sentence in enumerate(self.conll_matrix):
                for line in sentence:
                    print('\t'.join(line), file=semantic_file)
                if i < len(self.conll_matrix) - 1:
                    print(end='\n', file=semantic_file)
