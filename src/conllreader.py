#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Build syntactic trees from CoNLL parser output

    Define the following  classes:
    * SyntacticTreeNode
    * SyntacticTreeBuilder
    * ConllSemanticAppender
"""
import sys
from collections import defaultdict
from distance import lcsubstrings as word_overlap # type: ignore
import framenetframe
import options
import logging
import re

logging.basicConfig(level=logging.DEBUG)
logging.root.setLevel(logging.DEBUG)

class SyntacticTreeNode:
    """A node (internal or terminal) of a syntactic tree

    :var word_id: int, the CoNLL word id (starts at 1)

    :var word: string, the word contained by the node
    :var lemma: string, the lemma of the word contained by the node
    :var cpos: string, part-of-speech of the node
    :var pos: string, part-of-speech of the node

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
        self.pos = pos if pos != "_" else cpos
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
        return (f"node(id: {self.word_id}; father: {father}; "
                f"children: {children}; cpos: {self.cpos}; pos: {self.pos}; "
                f"deprel: {self.deprel}; begin_word: {self.begin_word}; "
                f"position: {self.position}; begin: {self.begin}; "
                f"end: {self.end}; word: {self.word})")  # children'''

    def __str__(self):
        result = f"({self.pos}/{self.deprel}/{self.position}/{self.begin}/{self.end} {self.lemma}"
        # If the node has childre we add them recursively
        for child_node in self.children:
            result += " " + str(child_node)
        result += ")"  # To end the representation
        return result

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
        # GC20171122: commented out below because the root predicate was not
        # yielded. Is it an error in building the position attribute ?
        # if self.position == len(self.children):
        yield self

    def fathers(self, previous=set()):
        if self.father is not None and self.father not in previous:
            result = previous
            result.add(self.father)
            return self.father.fathers(result)
        return previous

    #def flat(self):
        #"""Return the tokenized sentence from the parse tree."""
        #return " ".join([x.word for x in self])
        # result = f"({self.pos}/{self.deprel}/{self.position}/{self.begin}/{self.end} {self.lemma}"
        # If the node has childre we add them recursively
        # for child_node in self.children:

            # result += " " + str(child_node)
        # result += ")"  # To end the representation
        # return result
    def str2(self):

        result = f"({self.pos}/{self.deprel}/{self.position}/{self.begin}/{self.end}/{self.begin_word} {self.word}"
        # If the node has childre we add them recursively
        for child_node in self.children:

            result += " " + child_node.str2()
        result += " )"  # To end the representation a space was added to ease the retrieval of the words in parse_dependency_tree
        return result

    # Fonction pour extraire les mots et les informations à partir de l'arbre de dépendances
    def parse_dependency_tree(self):
        # Regex pour extraire les mots et leurs informations
        pattern = re.compile(r'\(([^()\s]+(?:/\w+/\d+/\d+/\d+)\s+.*?\s(?=\(|\)))') ## now includes the parentheses
        #matches = pattern.findall(str(tree))
        tree_str2 = self.str2()
        matches = pattern.findall(tree_str2)
        # breakpoint()

        # Liste pour stocker les informations extraites
        words_info = []

        for match in matches:
            # Extraire les informations de chaque mot
            self.logger.debug(f"match: {match}")
            parts = match.split()
            tag_info = parts[0].split('/')
            word = parts[1]

            # Structure des informations pour chaque mot
            word_info = {
                'pos_tag': tag_info[0],  # Étiquette grammaticale (par exemple, VBD, NN)
                'dep_rel': tag_info[1],  # Relation de dépendance (par exemple, ROOT, SUB)
                'word_order': int(tag_info[5]),  # Position du mot dans la phrase
                'word': word  # Le mot lui-même
            }
            words_info.append(word_info)

        return words_info


    # Fonction pour reconstruire la phrase
    def flat(self):

        # tree = str(self)
        # Parse l'arbre de dépendances
        words_info = self.parse_dependency_tree()
        # breakpoint()
        # Trier les mots en fonction de leur ordre dans la phrase
        sorted_words = sorted(words_info, key=lambda x: x['word_order'])

        # Récupérer les mots dans l'ordre
        sentence = ' '.join([word['word'] for word in sorted_words])

        return sentence




    def contains(self, arg):
        """Search an exact argument in all subtrees"""
        return (self.flat() == arg or
                any((c.contains(arg) for c in self.children)))
        #return (self.reconstruct_sentence() == arg or any((c.contains(arg) for c in self.children)))

    def closest_match(self, arg):
        """Search the closest match to arg"""
        return self.closest_match_as_node(arg).flat().split()

    def closest_match_as_node(self, arg):
        return self._closest_match_as_node_lcs(arg)[1]

    def _closest_match_as_node_lcs(self, arg):
        
        current_word_list = self.flat().split()
        wanted_word_list = arg.text.split()

        overlap = word_overlap(tuple(current_word_list),
                               tuple(wanted_word_list))
        if not overlap:
            overlap_words = []
        else:
            overlap_words = list(next(iter(overlap)))

        mean_length = (len(current_word_list) + len(wanted_word_list)) / 2
        score = -1 if mean_length == 0 else len(overlap_words) / mean_length

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
            linenum += 1
            """Columns from
            https://github.com/aymara/lima/wiki/LIMA-User-Manual"""
            split_line = l.split("\t")
            if len(split_line) == 11:
                (word_id, form, lemma, cpos, pos, namedEntityType, features,
                 head, deprel, phead, pdeprel) = l.split("\t")
            elif len(split_line) == 10:
                (word_id, form, lemma, cpos, pos, features,
                 head, deprel, phead, pdeprel) = l.split("\t")
                namedEntityType = '_'
            else:
                self.logger.warn(f'Wrong number of columns (expected 10 or '
                                 f'11) in line {linenum}: "{l}"\n')
                continue
            word_id = int(word_id)
            deprel = deprel if deprel not in ['-', '_'] else 'ROOT'
            if deprel == 'root':
                deprel = 'ROOT'
            head = int(head) if head not in ['-', '_'] else None
            if head is None and deprel == 'ROOT':
                head = 0

            self.father_ids[word_id] = head ## on remplit fathers_ids en y mettant la valuer head pour chaque word_id
            self.logger.debug(f'Add node: {word_id}, {form}, {cpos}, {deprel}')
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
        self.logger.debug('rebuilt sentence: {}'.format(self.sentence))
        self.logger.debug(self.sentence)

        # Record father/child relationship
        for word_id, father_id in self.father_ids.items():

            if father_id is not None and father_id != 0:
                try:
                    self.node_dict[word_id].father = self.node_dict[father_id]
                    self.node_dict[father_id].children.append(self.node_dict[word_id])  # noqa
                except KeyError:
                    self.logger.error(
                        f'father id {father_id} and/or word_id {word_id} not '
                        f'found in CoNLL tree {conll_tree}')

        # Record position: where is father among child?
        # Important to flatten tree
        for father in self.node_dict.values():
            father.position = 0

            for child_id, child in enumerate(father.children):
                if child.begin_word > father.begin_word:
                    father.position = child_id
                    break


                father.position = len(father.children)


        #for father in self.node_dict.values():
            #self.logger.debug(f"Final position for father: {father.position}", file=sys.stderr)

        # Dictionnaire de nœuds par ID
        self.nodes = [node for node in self.node_dict.values()]
        #self.logger.debug(self.nodes)

        for node in self.node_dict.values():
            if node.father is None:
                # Fill begin/end info
                # self.logger.debug(f"node: {node}", file=sys.stderr)
                # self.logger.debug(self.node_dict)
                self.fill_begin_end(node)
                # self.logger.debug(f"node: {node}", file=sys.stderr)
                # Fill forest of tree
                self.logger.debug('add to tree_list: {}'.format(node))

                self.tree_list.append(node)

                # #### NEW ######
                # Generate the whole tree
                # self.tree_list = self.build_tree_representation(node)
                # self.logger.debug(f"tree_representation: {tree_representation}")
        # self.tree_list = self.extract_words(tree_representation)
        self.logger.debug(f"tree_list: {self.tree_list[0]}")

    # Fills the begin and end for every child
    def fill_begin_end(self, node):
        """Fill begin/end values of every subtree"""

        begin_words = [node.begin_word]
        #self.logger.debug(f"begin_words: {begin_words}", file=sys.stderr)
        end_words = [node.begin_word + len(node.word) - 1]
        #self.logger.debug(f"end_words: {end_words}", file=sys.stderr)

        for child in node.children:
            self.fill_begin_end(child)
            #self.logger.debug(f"child: {child}", file=sys.stderr)

            begin_words.append(child.begin)
            end_words.append(child.end)
        node.begin = min(begin_words)
        node.end = max(end_words)



    # Generates the tree representation
    def build_tree_representation(self, node):
        # ROOT node
        result = f"({node.pos}/{node.deprel}/{node.position}/{node.begin}/{node.end} {node.lemma}"
        self.logger.debug(result)
        # If the node has childre we add them recursively
        for child_node in node.children:

            result += " " + self.build_tree_representation(child_node)

        result += ")"  # To end the representation
        return result

    # Retrieve a list of words from the treee representation
    def extract_words(self, tree_representation):
        # Extracts every word followed by a parentheses
        words = re.findall(r'\b\w+\b(?=\))|(?<=\()', tree_representation)
        return words


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
        self.conll_matrix[frame_annotation.sentence_id][frame_annotation.tokenid-1][-1] = '|'.join(sorted(frame_annotation.best_classes()))  # noqa
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
        if len(frame_annotations) == 0:
            return

        # Must shift annotations one line up on first sentence because
        # there is no previous sentence punctuation.
        notFirstSentenceShift = 0
        if frame_annotations[0].sentence_id == 0:
            notFirstSentenceShift = -1

        # compute the predicates string, concatenation of the possible
        # frames names
        if frame_annotations[0].predicate.tokenid+notFirstSentenceShift < len(self.conll_matrix[frame_annotations[0].sentence_id]):
            # self.logger.debug(len(self.conll_matrix[frame_annotations[0].sentence_id][frame_annotations[0].predicate.tokenid+notFirstSentenceShift]))
            self.conll_matrix[frame_annotations[0].sentence_id][frame_annotations[0].predicate.tokenid+notFirstSentenceShift][-1] = '|'.join([frame_instance.frame_name for frame_instance in frame_annotations])  # noqa
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
            if (position+notFirstSentenceShift <
                    len(self.conll_matrix[frame_annotations[0].sentence_id])):
                self.conll_matrix[frame_annotations[0].sentence_id][
                    position+notFirstSentenceShift][-1] = roleset_str  # noqa

    def dump_semantic_file(self, filename):
        with open(filename, 'w') as semantic_file:
            for i, sentence in enumerate(self.conll_matrix):
                for line in sentence:
                    self.logger.debug('\t'.join(line))
                    self.logger.debug('\t'.join(line), file=semantic_file)
                if i < len(self.conll_matrix) - 1:
                    self.logger.debug('\n')
                    self.logger.debug(end='\n', file=semantic_file)
