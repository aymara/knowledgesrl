#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Map FrameNet and VerbNet roles """

import xml.etree.ElementTree as ET

import verbnetframe
import framenetframe
import options
import logging

from collections import defaultdict
import itertools
import copy

# VN roles given by table 2 of
# http://verbs.colorado.edu/~mpalmer/projects/verbnet.html
vn_roles_list = [
    "Actor", "Agent", "Asset", "Attribute", "Beneficiary", "Cause",
    "Co-Agent", "Co-Patient", "Co-Theme",  # Not in the original list
    "Location", "Destination", "Source", "Experiencer", "Extent",
    "Instrument", "Material", "Product", "Patient", "Predicate",
    "Recipient", "Stimulus", "Theme", "Time", "Topic"]

# Added roles
vn_roles_additionnal = ["Goal", "Initial_Location", "Pivot", "Result",
                        "Trajectory", "Value"]

# List of VN roles that won't trigger an error in unit tests
authorised_roles = vn_roles_list + vn_roles_additionnal


class RoleMatchingError(Exception):
    """ Missing data to compare a vn and a fn role

    :var msg: str, a message detailing what is missing
    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return ("Error : {}".format(self.msg))


class VnFnRoleMatcher():
    """Reads the mapping between VN and FN roles, and can then be used to
        compare them

    :var fn_roles: data structure used to store the mapping between FrameNet
                    and VerbNet roles
    :var fn_frames: maps FrameNet frame names to VerbNet class names
    :var framenetframe_to_verbnetclasses: FrameNet frame -> VerbNet class
                                            mapping
    :var verbnetclass_to_framenetframes: VerbNet class -> FrameNet frame
                                            mapping
    :var issues: used to store statistics about the problem encoutered
    """

    def __init__(self, path, frameNet):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(options.Options.loglevel)
        self.logger.debug('VnFnRoleMatcher({})'.format(path))

        self.frameNet = frameNet

        # 4-dimensions matrix :
        # self.fn_roles[fn_role][fn_frame][vn_class][i] is the
        # i-th possible VN role associated to fn_role for the frame fn_frame
        # and a verb in vn_class.
        self.fn_roles = {}

        # 4-dimensions matrix :
        # self.vn_roles[vn_role][vn_class][fn_class][i] is the
        # i-th possible FN role associated to vn_role for the class vn_class
        # and a verb in fn_frame.
        self.vn_roles = {}

        # FrameNet frame -> VerbNet class mapping
        self.framenetframe_to_verbnetclasses = defaultdict(list)

        # VerbNet class -> FrameNet frame mapping
        self.verbnetclass_to_framenetframes = defaultdict(list)

        root = ET.ElementTree(file=str(path))

        for mapping in root.getroot():
            vn_class = mapping.attrib["class"]
            fn_frame = mapping.attrib["fnframe"]

            self.framenetframe_to_verbnetclasses[fn_frame].append(vn_class)
            self.verbnetclass_to_framenetframes[vn_class].append(fn_frame)

            for role in mapping.findall("roles/role"):
                vn_role = role.attrib["vnrole"]
                fn_role = role.attrib["fnrole"]

                vn_role = self._handle_co_roles(vn_role)

                self._add_relation(
                    fn_role, vn_role,
                    fn_frame, vn_class)
        self._build_frames_vnclasses_mapping()

    def _handle_co_roles(self, vn_role):
        if vn_role[-1] == "1":
            return vn_role[0:-1]
        if vn_role[-1] == "2":
            return "Co-"+vn_role[0:-1]
        return vn_role

    def _add_relation(self, fn_role, vn_role, fn_frame, vn_class):
        if fn_role not in self.fn_roles:
            self.fn_roles[fn_role] = {"all": set()}
        if fn_frame not in self.fn_roles[fn_role]:
            self.fn_roles[fn_role][fn_frame] = {"all": set()}
        if vn_class not in self.fn_roles[fn_role][fn_frame]:
            self.fn_roles[fn_role][fn_frame][vn_class] = set()

        self.fn_roles[fn_role]["all"].add(vn_role)
        self.fn_roles[fn_role][fn_frame]["all"].add(vn_role)
        self.fn_roles[fn_role][fn_frame][vn_class].add(vn_role)

        if vn_role not in self.vn_roles:
            self.vn_roles[vn_role] = {"all": set()}
        if vn_class not in self.vn_roles[vn_role]:
            self.vn_roles[vn_role][vn_class] = {"all": set()}
        if fn_frame not in self.vn_roles[vn_role][vn_class]:
            self.vn_roles[vn_role][vn_class][fn_frame] = set()

        self.vn_roles[vn_role]["all"].add(fn_role)
        self.vn_roles[vn_role][vn_class]["all"].add(fn_role)
        self.vn_roles[vn_role][vn_class][fn_frame].add(fn_role)

    def _build_frames_vnclasses_mapping(self):
        """ Builds a mapping between framenet frames and associated verbnet
            classes """
        self.logger.debug("_build_frames_vnclasses_mapping")
        self.fn_frames = defaultdict(lambda: set())
        for fn_role in self.fn_roles:
            if fn_role == "all":
                continue
            for fn_frame in self.fn_roles[fn_role]:
                if fn_frame == "all":
                    continue
                for vn_class in self.fn_roles[fn_role][fn_frame]:
                    if vn_class == "all":
                        continue
                    self.fn_frames[fn_frame].add(vn_class)

    def possible_vn_roles(self, fn_role, fn_frame=None, vn_classes=None):
        """Returns the set of VN roles that can be mapped to a FN role in a
            given context

        :param fn_role: The FrameNet role.
        :type fn_role: str.
        :parma vn_role: The VerbNet role.
        :type vn_role: str.
        :param fn_frame: The FrameNet frame in which the roles have to be
                            mapped.
        :type fn_frame: str.
        :param vn_classes: A list of VerbNet classes for which the roles have
                            to be mapped.
        :type vn_classes: str List.
        :returns: str List -- The list of VN roles
        """

        if fn_role not in self.fn_roles:
            raise RoleMatchingError(
                "{} role does not seem"
                " to exist".format(fn_role))
        if fn_frame is None and vn_classes is None:
            return self.fn_roles[fn_role]["all"]

        if fn_frame is not None and fn_frame not in self.fn_roles[fn_role]:
            raise RoleMatchingError(
                "{} role does not seem"
                " to belong to frame {}".format(fn_role, fn_frame))
        if vn_classes is None:
            return self.fn_roles[fn_role][fn_frame]["all"]

        if fn_frame is None:
            frames = list(self.fn_roles[fn_role].keys())
            frames.remove("all")
        else:
            frames = [fn_frame]

        vnroles = set()

        for vn_class in vn_classes:
            # Use the format of the vn/fn mapping
            vn_class = "-".join(vn_class.split('-')[1:])
            for frame in frames:
                while True:
                    if vn_class in self.fn_roles[fn_role][frame]:
                        vnroles = vnroles.union(self.fn_roles
                                                [fn_role]
                                                [frame]
                                                [vn_class])
                        break

                    position = max(vn_class.rfind("-"), vn_class.rfind("."))
                    if position == -1:
                        break

                    vn_class = vn_class[0:position]

        if vnroles == set():
            # We don't have the mapping for any of the VN class provided in
            # vn_classes
            raise RoleMatchingError(
                "None of the given VerbNet classes ({}) were corresponding to"
                " {} role and frame {}".format(vn_class, fn_role, fn_frame))

        return vnroles

    def possible_framenet_mappings(self, verbnet_frame_occurrence):
        """ Computes the possible FrameNet frame instances given
            a given VerbNet frame occurrence

        :var verbnet_frame_occurrence: VerbnetFrameOccurrence
        return a FrameInstance list
        """
        result = []
        allframenames = set()
        self.logger.debug('possible_framenet_mappings {}'
                          .format(verbnet_frame_occurrence))
        for match in verbnet_frame_occurrence.best_matches:
            verbnetclassname = match['vnframe'].vnclass
            verbnetclassid = verbnetclassname.split('-', 1)[1]
            framenames = self.verbnetclass_to_framenetframes[
                match['vnframe'].vnclass.split('-', 1)[1]]
            framenames = self.filter_frame_names(framenames, verbnet_frame_occurrence.predicate)
            for framename in framenames:
                if framename not in allframenames:
                    allframenames.add(framename)
                    self.logger.debug('FrameNet frames: {} {}'
                                      .format(match['vnframe'].vnclass,
                                              framename))
                    rolesarrays = []
                    for possibleroles in verbnet_frame_occurrence.roles:
                        rolesarrays.append([])
                        for possiblerole in possibleroles:
                            if (possiblerole in self.vn_roles
                                    and (verbnetclassid
                                         in self.vn_roles[possiblerole])
                                    and (framename
                                         in self.vn_roles[possiblerole][verbnetclassid])):  # noqa
                                self.logger.debug('self.vn_roles[{}][{}][{}] = {}'  # noqa
                                                  .format(possiblerole,
                                                          verbnetclassid,
                                                          framename,
                                                          self.vn_roles[possiblerole]  # noqa
                                                                       [verbnetclassid]  # noqa
                                                                       [framename]))  # noqa
                                rolesarrays[-1].extend(self.vn_roles
                                                       [possiblerole]
                                                       [verbnetclassid]
                                                       [framename])
                            else:
                                self.logger.debug('self.vn_roles[{}][{}][{}] '
                                                  'is empty'
                                                  .format(possiblerole,
                                                          verbnetclassid,
                                                          framename))
                    for rolearray in rolesarrays:
                        if not rolearray:
                            rolearray.append('')
                    predicate = framenetframe.Predicate(
                        0, 0, verbnet_frame_occurrence.predicate,
                        verbnet_frame_occurrence.predicate,
                        verbnet_frame_occurrence.tokenid)
                    rolestuples = list(itertools.product(*rolesarrays))
                    self.logger.debug('rolesarrays: {}'.format(rolesarrays))
                    self.logger.debug('rolestuples: {}'.format(rolestuples))
                    for rolestuple in rolestuples:
                        # copy the VerbNet class args
                        framenetframeargs = copy.deepcopy(verbnet_frame_occurrence.args)  # noqa
                        for role, arg in zip(rolestuple, framenetframeargs):
                            arg.role = role
                        frameinstance = framenetframe.FrameInstance(
                            "",
                            predicate,
                            framenetframeargs,
                            [],
                            framename,
                            verbnet_frame_occurrence.sentence_id)
                        result.append(frameinstance)
        return result

    def filter_frame_names(self, framenames, predicate):
        self.logger.debug("filter_frame_names filtering predicate {} from frames {}".format(predicate, framenames))
        result = set()
        #print("frameNet frames: {}".format(self.frameNet.frames))
        for framename in framenames:
            self.logger.debug("filter_frame_names frame {} lexical units: {}".format(framename, self.frameNet.frames[framename].lexicalUnits))
            if "{}.v".format(predicate) in self.frameNet.frames[framename].lexicalUnits:
                result.add(framename)
            else:
                self.logger.debug("filter_frame_names filtering out {} for predicate {}".format(framename, predicate))
        if (result):
            return result
        else:
            self.logger.debug("filter_frame_names everything is filtered out. returning all frame names: {}".format(framenames))
            return framenames
