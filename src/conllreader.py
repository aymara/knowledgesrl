#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Build syntactic trees from CoNLL parser output

    Define the following  classes:
    * SyntacticTreeNode
    * SyntacticTreeBuilder
    * ConllSemanticAppender
"""

from collections import defaultdict
import framenetframe
import options
import logging


class SyntacticTreeNode:
    """A node (internal or terminal) of a syntactic tree

    :var word_id: int, the CoNLL word id (starts at 1)

    :var word: string, the word contained by the node
    :var lemma: string, the lemma of the word contained by the node
    :var pos: part-of-speech of the node

    :var deprel: string, function attributed by the parser to this word
    :var father: SyntacticTreeBuilder, the father of this node
    :var children: SyntacticTreeNode list, the children of this node

    :var begin: int, the character position this phrase starts at (root would
                be 0)
    :var end: int, the position this phrase ends at (root would be last
              character)
    :var begin_word: int, the position this *word* begins at

    """

    def __init__(self, word_id, word, lemma, cpos, pos, namedEntityType,
                 features, head, deprel, phead, pdeprel, begin_word):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(options.Options.loglevel)

        # self.logger.debug('SyntacticTreeNode({})'.format(deprel))
        self.word_id = word_id

        self.word = word
        self.lemma = lemma
        self.cpos = cpos
        self.pos = pos
        self.namedEntityType = namedEntityType
        self.features = features
        self.head = head
        self.deprel = deprel
        self.phead = phead
        self.pdeprel = pdeprel
        self.begin_word = begin_word

        self.father = None
        self.children = []

        self.begin, self.end = None, None

    def __repr__(self):
        children = " ".join([str(t.word_id) for t in self.children])

        if self.father:
            father = self.father.word_id
        else:
            father = ""

        return "({}/{}/{}/{}/{}/{}/{}/{}/{} {})".format(
            self.word_id,
            father,
            children,
            self.pos,
            self.deprel,
            self.begin_word,
            self.position,
            self.begin,
            self.end,
            self.word) #, children)

    def __eq__(self, other):
        if isinstance(other, SyntacticTreeNode):
            return ((self.word_id == other.word_id))
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    def __hash__(self):
        return self.word_id

    def __iter__(self):
        for position, child in enumerate(self.children):
            if child.word_id == self.word_id:
                yield(self)
            for node in child:
                if node in self.fathers():
                    yield self
                else:
                    yield node
        if self.position == len(self.children):
            yield self

    def fathers(self, previous=set()):
        if self.father is not None and self.father not in previous:
            result = previous
            #import ipdb; ipdb.set_trace()
            result.add(self.father)
            return self.father.fathers(result)
        return previous

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
        import distance
        from distance import lcsubstrings as word_overlap

        current_word_list = self.flat().split()
        wanted_word_list = arg.text.split()

        overlap = word_overlap(tuple(current_word_list),
                               tuple(wanted_word_list))
        if not overlap:
            overlap_words = []
        else:
            overlap_words = list(next(iter(overlap)))

        mean_length = (len(current_word_list) + len(wanted_word_list)) / 2
        score = len(overlap_words) / mean_length

        children_results = [c._closest_match_as_node_lcs(arg)
                            for c in self.children]
        return max([(score, self)] + children_results, key=lambda x: x[0])


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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(options.Options.loglevel)

        self.node_dict, self.father_ids = {}, {}
        self.tree_list = []

        begin = 0
        linenum = 0
        for l in conll_tree.splitlines():
            try:
                linenum += 1
                """Columns from
                https://github.com/aymara/lima/wiki/LIMA-User-Manual"""
                word_id, form, lemma, cpos, pos, namedEntityType, features,\
                    head, deprel, phead, pdeprel = l.split("\t")
            except ValueError:
                self.logger.warn('Wrong number of columns (expected 11) in '
                                 'line {}: "{}"\n'.format(linenum, l))
                continue
            word_id = int(word_id)
            head = int(head) if head != '_' else None
            deprel = deprel if deprel != '_' else 'ROOT'

            self.father_ids[word_id] = head

            self.node_dict[word_id] = SyntacticTreeNode(
                word_id=word_id,
                word=form,
                lemma=lemma,
                cpos=cpos,
                pos=pos,
                namedEntityType=namedEntityType,
                features=features,
                head=head,
                deprel=deprel,
                phead=phead,
                pdeprel=pdeprel,
                begin_word=begin)

            begin += 1 + len(form)

        self.sentence = ' '.join([self.node_dict[w_id].word
                                  for w_id in sorted(self.node_dict.keys())])

        # Record father/child relationship
        for word_id, father_id in self.father_ids.items():
            if father_id is not None and father_id != 0:
                try:
                    self.node_dict[word_id].father = self.node_dict[father_id]
                    self.node_dict[father_id].children.append(self.node_dict[word_id])  # noqa
                except KeyError:
                    self.logger.error('father id {} and/or word_id {} not found in CoNLL tree {}'
                                      ''.format(
                                          father_id,
                                          word_id,
                                          conll_tree))

        # Record position: where is father among child?
        # Important to flatten tree
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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(options.Options.loglevel)

        self.conll_matrix = []

        with open(syntactic_conll_file) as content:
            sentences_data = content.read().split("\n\n")

            for sentence in sentences_data:
                sentence_matrix = []
                for line in sentence.split('\n'):
                    if len(line.split('\t')) == 1:
                        continue
                    # Put current line with a new column appended for predicate
                    sentence_matrix.append(line.split('\t') + ['_'])
                self.conll_matrix.append(sentence_matrix)

    def __str__(self):
        result = ""
        for i, sentence in enumerate(self.conll_matrix):
            for line in sentence:
                result += '\t'.join(line) + '\n'
            if i < len(self.conll_matrix) - 1:
                result += '\n'
        return result

    def add_new_column(self, sentence_id):
        for line in self.conll_matrix[sentence_id]:
            line.append('_')

    def add_verbnet_frame_annotation(self, frame_annotation):
        # We could have multiple classes, so join them with |
        self.conll_matrix[frame_annotation.sentence_id][frame_annotation.tokenid-1][11] = '|'.join(sorted(frame_annotation.best_classes()))  # noqa
        # Add new column to place the new roles
        self.add_new_column(frame_annotation.sentence_id)

        for roleset, arg in zip(frame_annotation.roles, frame_annotation.args):
            roleset_str = '|'.join(sorted(roleset)) if roleset else '_EMPTYROLE_'  # noqa
            self.logger.debug('add_verbnet_frame_annotation roleset: {}'
                              .format(roleset_str))
            self.conll_matrix[frame_annotation.sentence_id][arg.position-1][-1] = roleset_str  # noqa

    def add_framenet_frame_annotation(self, frame_annotations):
        """ Add columns corresponding to the given frame instances.

        :var frame_annotations: FrameInstance list

        All frame instances are supposed to be from the same sentence.
        """
        self.logger.info("add_framenet_frame_annotation frame instance list: [{}]".format(','.join(str(x) for x in frame_annotations)))  # noqa
        if len(frame_annotations) is 0:
            return

        # Must shift annotations one line up on first sentence because
        # there is no previous sentence punctuation.
        notFirstSentenceShift = 0
        if frame_annotations[0].sentence_id is 0:
            notFirstSentenceShift = -1

        # compute the predicates string, concatenation of the possible
        # frames names
        if frame_annotations[0].predicate.tokenid+notFirstSentenceShift < len(self.conll_matrix[frame_annotations[0].sentence_id]):
            self.conll_matrix[frame_annotations[0].sentence_id][frame_annotations[0].predicate.tokenid+notFirstSentenceShift][11] = '|'.join([frame_instance.frame_name for frame_instance in frame_annotations])  # noqa
        else:
            self.logger.error("add_framenet_frame_annotation got token number "
                              "larger than conll_matrix for current sentence")
            return

        # Add new column to place the new roles
        self.add_new_column(frame_annotations[0].sentence_id)

        # join all frame instance argument that are at the same position
        arguments_for_ids = defaultdict(list)
        for frame_instance in frame_annotations:
            for arg in frame_instance.args:
                arguments_for_ids[arg.position].append(arg.role)

        # place the arguments at the correct place in the matrix
        for position in arguments_for_ids:
            roleset_str = '|'.join(arguments_for_ids[position])
            self.logger.debug(
                'add_framenet_frame_annotation roleset: {}'.format(
                    roleset_str))
            if position+notFirstSentenceShift < len(self.conll_matrix[frame_annotations[0].sentence_id]):
                self.conll_matrix[frame_annotations[0].sentence_id][position+notFirstSentenceShift][-1] = roleset_str  # noqa

    def dump_semantic_file(self, filename):
        with open(filename, 'w') as semantic_file:
            for i, sentence in enumerate(self.conll_matrix):
                for line in sentence:
                    self.logger.debug('\t'.join(line))
                    print('\t'.join(line), file=semantic_file)
                if i < len(self.conll_matrix) - 1:
                    self.logger.debug('\n')
                    print(end='\n', file=semantic_file)
