#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Parse FrameNet fulltext annotation into FrameInstance, Arg and Predicate objects.

Notes:

 * Currently, when a role is not instantiated in FrameNet, we simply store it
   as empty arg in framenetreader. Should we take advantage of the fact that we
   know the type of non instanciation?
 * Argument of a trigger can be the trigger itself, which doesn't allow to
   represent our frame as "NP V NP...". Currently, it's considered as a case of
   null instanciation, but this could change if needed.
 * FrameNet sometimes has two layers of annotations, with the second layer
   having roles that overlap with the first one, but without PT (Phrase Type).
   Those layers are ignored.
 * Fourteen other cases (out of 18000+) of an argument (or predicate ?) not
   matching with any word in the sentence. Also ignored right now.


"""

import xml.etree.ElementTree as ET

from framenetframe import FrameInstance, Predicate, Word, Arg
from verbnetprepclasses import rel_pronouns
import framenetcoreargs
import paths


class FulltextReader:

    """Class used to parse one file of the FrameNet fulltext corpus

    :var frames: FrameInstance list of every frame collected

    """

    core_arg_finder = None
    predicate_pos = [
        "md", "MD",
        "VB", "VBD", "VBG", "VBN", "VBP", "VBZ",
        "VV", "VVD", "VVG", "VVN", "VVP", "VVZ",
        "VH", "VHD", "VHG", "VHN", "VHP", "VHZ"]

    pos_mapping = {
        # Nouns
        "NP": "NNP", "NPS": "NNPS",
        # Preposition
        "PP": "PRP", "PP$": "PRP$",
        # Verbs
        "VH": "VB", "VHD": "VBD", "VHG": "VBG", "VHP": "VBP", "VHN": "VBN",
        "VHZ": "VBZ", "VV": "VB", "VVD": "VBD", "VVG": "VBG", "VVN": "VBN",
        "VVP": "VBP", "VVZ": "VBZ"
    }

    # etree will add the xmlns string before every tag name
    framenet_xmlns = "{http://framenet.icsi.berkeley.edu}"

    def __init__(self, filename, add_non_core_args=True, keep_unannotated=False,
                 tree_dict=None, keep_nonverbal=False, pos_file=None):
        """Read a file and update the collected frames list.

        :param filename: Path to the file to read.
        :type filename: str.
        :param add_non_core_args: Whether we should include non core args.
        :type add_non_core_args: boolean.
        :param keep_unannotated: Whether we should keep frames without annotated args.
        :type keep_unannotated: boolean.
        :param tree_dict: Syntactic trees for the frames (grouped by sentence in dict)
        :type trees: None | SyntacticTreeNode Dict
        """

        if FulltextReader.core_arg_finder == None and not add_non_core_args:
            FulltextReader.core_arg_finder = framenetcoreargs.CoreArgsFinder()
            FulltextReader.core_arg_finder.load_data_from_xml(paths.FRAMENET_FRAMES)

        self.frames = []

        self.add_non_core_args = add_non_core_args
        self.keep_unannotated = keep_unannotated
        self.keep_nonverbal = keep_nonverbal

        self.pos_file = pos_file
        self.pos_data = None
        if self.pos_file != None:
            pos_file_content = open(str(pos_file)).read()
            self.pos_data = pos_file_content.split("\n\n")

        # Debug data
        self.filename = filename
        self.ignored_layers = []
        self.predicate_is_arg = []
        self.phrase_not_found = []
        self.missing_predicate_data = []
        self.non_existing_frame_name = []

        # TODO Remove condition and reorganize caller code instead
        if filename is not None:
            root = ET.ElementTree(file=str(filename))
            self._init_file_data(root)
            self._parse_xml(root, tree_dict)

    def _init_file_data(self, root):
        if root.getroot().tag == "corpus":
            self._init_semafor_data()
        elif root.find(FulltextReader.framenet_xmlns+"valences") == None:
            self._init_fulltext_data()
        else:
            return self._init_lu_data(root)
        return True

    def _init_fulltext_data(self):
        self.corpus = "fulltext"
        self._xmlns = FulltextReader.framenet_xmlns
        self.all_annotated = False
        self.constant_predicate = ""
        self.constant_frame = ""
        self.patterns = {
            "sentence": self._xmlns + "sentence",
            "frame": self._xmlns + "annotationSet[@luName]",
            "predicate": self._xmlns+"layer[@name='Target']",
            "arg": "{}layer[@name='FE'][@rank='{}']/*",
            "pt": "{}layer[@name='PT'][@rank='{}']/*"
        }

    def _init_lu_data(self, root):
        self.corpus = "lu"
        self._xmlns = FulltextReader.framenet_xmlns
        self.all_annotated = False

        # keep_unannotated has no sense for LUCorpus
        self.keep_unannotated = False

        predicate_data = root.getroot().attrib["name"].split(".")
        if predicate_data[1] != "v":
            return False
        self.constant_predicate = predicate_data[0]
        self.constant_frame = root.getroot().attrib["frame"]

        self.patterns = {
            "sentence": (self._xmlns + "subCorpus/" +
            self._xmlns + "sentence"),
            "frame": self._xmlns + "annotationSet",
            "predicate": self._xmlns+"layer[@name='Target']",
            "arg": "{}layer[@name='FE'][@rank='{}']/*",
            "pt": "{}layer[@name='PT'][@rank='{}']/*"
        }

        return True

    def _init_semafor_data(self):
        self.corpus = "semafor"
        self._xmlns = ""
        self.all_annotated = True
        self.constant_predicate = ""
        self.constant_frame = ""

        self.patterns = {
            "sentence": ("documents/document/paragraphs/paragraph"
                "/sentences/sentence"),
            "frame": "annotationSets/annotationSet",
            "predicate": "layers/layer[@name='Target']/labels",
            "arg": "layers/layer[@name='FE']/labels/*"
        }

    def _parse_xml(self, root, tree_dict):
        for i, sentence in enumerate(root.findall(self.patterns["sentence"])):
            for frame in self._parse_sentence(sentence, i):
                frame.sentence_id = i
                if tree_dict is not None:
                    # TODO don't use the first tree, but the correct one?
                    frame.tree = tree_dict[i][0]

                self.frames.append(frame)

    def _parse_sentence(self, sentence, sentence_number):
        """Handle the parsing of one sentence.

        :param sentence: XML representation of the sentence.
        :type sentence: xml.etree.ElementTree.Element.

        """

        text = sentence.find(self._xmlns + "text").text.lower()

        words = []
        predicate_starts = []
        pos_data = []
        if self.pos_data == None:
            pos_annotation = "{0}annotationSet/{0}layer[@name='PENN']/" \
                             "{0}label".format(self._xmlns)
            for label in sentence.findall(pos_annotation):
                pos_data.append({
                    "start": label.attrib["start"],
                    "end": label.attrib["end"],
                    "pos": label.attrib["name"]
                })
        else:
            # We can use the existing automatic SEMAFOR part-of-speech annotation
            start = 0
            for line in self.pos_data[sentence_number].split("\n"):
                if line == "": continue
                line = line.split("\t")
                pos_data.append({
                    "start": start,
                    "end": start+len(line[1]) - 1,
                    "pos": line[3]
                })
                start += len(line[1]) + 1

        for word in pos_data:
            if word["pos"] in FulltextReader.predicate_pos or self.keep_nonverbal:
                predicate_starts.append(int(word["start"]))

            words.append(Word(int(word["start"]), int(word["end"]), word["pos"]))

        already_annotated = []
        for potential_frame in sentence.findall(self.patterns["frame"]):
            # We keep only annotated verbal frames

            annotated = ("status" in potential_frame.attrib and
                potential_frame.attrib["status"] != "UNANN")
            annotated = annotated or self.all_annotated

            if not (annotated or self.keep_unannotated): continue
            frame = self._parse_frame(
                text, words, potential_frame, annotated, predicate_starts)
            if frame and not frame.predicate.begin in already_annotated:
                already_annotated.append(frame.predicate.begin)
                yield frame

    def _parse_frame(self, sentence_text, words, frame, annotated, predicate_starts):
        """Handle the parsing of one frame.

        :param sentence_text: Sentence in which the frame occurs.
        :type sentence_text: str.
        :param frame: XML representation of the frame
        :type frame: xml.etree.ElementTree.Element.

        """

        predicate = self._build_predicate(sentence_text, frame)

        if predicate == None:
            return
        elif self.corpus in ["fulltext", "semafor"] and not predicate.begin in predicate_starts:
            return

        if self.constant_frame == "":
            frame_name = frame.attrib["frameName"]
        else:
            frame_name = self.constant_frame


        if frame_name == "Test35":
            self.non_existing_frame_name.append({
                "file": self.filename,
                "frame_name": frame_name,
                "sentence": sentence_text,
            })
            return

        if annotated:
            args = self._build_args_list(
                sentence_text, frame, frame_name, predicate)
        else:
            args = []

        return FrameInstance(sentence_text, predicate, args, words, frame_name,
            filename=self.filename, arg_annotated=annotated)

    def _build_args_list(self, sentence_text, frame, frame_name, predicate):
        """Handle the collection of argument list.

        :param sentence_text: Sentence in which the frame occurs.
        :type sentence_text: str.
        :param frame: XML representation of the frame
        :type frame: xml.etree.ElementTree.Element.
        :param frame_name: The name of the FrameNet frame.
        :type frame_name: str.
        :param predicate: The predicate of the frame
        :type predicate: Predicate
        :returns: Argument list -- the built argument list
        """

        args = []
        rank = 1
        stop = False
        phrase_data = None
        while not stop:
            arg_search_str = self.patterns["arg"].format(self._xmlns, rank)
            arg_data = frame.findall(arg_search_str)

            if not self.corpus == "semafor":
                phrase_search_str = self.patterns["pt"].format(self._xmlns, rank)
                phrase_data = frame.findall(phrase_search_str)

            # Stop if we have reached a non argument-annotated layer
            if len(arg_data) == 0: break

            for arg in arg_data:
                stop, new_arg = self._build_arg(
                    sentence_text, frame, predicate, arg, phrase_data, rank)

                if new_arg == None: continue

                if (not self.add_non_core_args and not
                    FulltextReader.core_arg_finder.is_core_role(
                        new_arg.role, frame_name)):
                    continue

                add = True
                for arg in args[:]:
                    if (arg.role == new_arg.role and
                            arg.phrase_type == new_arg.phrase_type):

                        if arg.text in rel_pronouns:
                            add = False
                        if new_arg.text in rel_pronouns:
                            args.remove(arg)

                if add:
                    args.append(new_arg)

            rank += 1

            # We need to "bypass" the argument layer system for Semafor output
            # because there is always only one layer
            if self.corpus == "semafor": stop = True

        return args

    def _build_arg(self, sentence_text, frame, predicate, arg, phrase_data, rank):
        # Checks wether the argument is instanciated
        if "itype" in arg.attrib:
            return False, Arg(0, -1, "", arg.attrib["name"], False, "")
        else:
            arg_start = int(arg.attrib["start"])
            arg_end = int(arg.attrib["end"])

            if self.corpus == "semafor":
                phrase_found, phrase_type = True, ""
            else:
                # Stop if we have reached a non phrase-type-annotated layer
                # with at least one instanciated argument
                if len(phrase_data) == 0:
                    self.ignored_layers.append({
                        "file": self.filename,
                        "predicate": predicate.lemma,
                        "sentence": sentence_text,
                        "layer": rank
                    })
                    return True, None

                phrase_found, phrase_type = False, ""
                for phrase in phrase_data:
                    phrase_found = (
                        int(phrase.attrib["start"]) == arg_start and
                        int(phrase.attrib["end"]) == arg_end)
                    if phrase_found:
                        phrase_type = phrase.attrib["name"]
                        break

            # If the argument and the predicate overlap, mark the argument as NI
            if arg_start <= predicate.end and arg_end >= predicate.begin:
                self.predicate_is_arg.append({
                    "file": self.filename,
                    "predicate": predicate.lemma,
                    "sentence": sentence_text
                })
                return False, Arg(0, -1, "",  arg.attrib["name"], False, "")

            if phrase_found:
                return False, Arg(
                    arg_start, arg_end,
                    sentence_text[arg_start:(arg_end + 1)],
                    arg.attrib["name"], True, phrase_type)
            else:
                self.phrase_not_found.append({
                    "file": self.filename,
                    "predicate": predicate.lemma,
                    "argument": sentence_text[arg_start:(arg_end + 1)],
                    "sentence": sentence_text
                })
                return False, None

    def _build_predicate(self, sentence_text, frame):
        """Handle the collection of the predicate data.

        :param sentence_text: Sentence in which the frame occurs.
        :type sentence_text: str.
        :param frame: XML representation of the frame
        :type frame: xml.etree.ElementTree.Element.
        :returns: Predicate -- the built predicate
        """

        predicate_lemma = None
        if self.constant_predicate == "" and "luName" in frame.attrib:
            predicate_lemma = frame.attrib["luName"].split(".")[0]
        else:
            predicate_lemma = self.constant_predicate

        predicate_data = frame.findall(self.patterns["predicate"])[0]

        # This test handles the only self-closed layer tag that exists in the corpus
        if len(predicate_data) == 0:
            self.missing_predicate_data.append({
                "file": self.filename,
                "predicate": predicate_lemma,
                "sentence": sentence_text
            })
            return
        else:
            predicate_data = predicate_data[0]

        predicate_start = int(predicate_data.attrib["start"])
        predicate_end = int(predicate_data.attrib["end"])
        return Predicate(
            predicate_start,
            predicate_end,
            sentence_text[predicate_start:(predicate_end + 1)],
            predicate_lemma)

    def to_conll_format(self):
        """Outputs all frames to the CoNLL format

        :returns: string, the content of the MST file
        """

        last_sentence = ""

        for frame in self.frames:
            if frame.sentence != last_sentence:
                frame_conll = ""
                i = 0
                for w in frame.words:
                    i += 1
                    frame_conll += "{0}\t{1}\t{1}\t{2}\t{2}\t_\t0\t \t\n".format(
                        i, frame.get_word(w), self.pos_mapping.get(w.pos, w.pos))

                yield frame_conll + "\n"

            last_sentence = frame.sentence
