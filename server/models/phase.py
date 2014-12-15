#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

from girder.constants import AccessType
from girder.models.model_base import AccessControlledModel


class Phase(AccessControlledModel):
    def initialize(self):
        self.name = 'challenge_phase'
        self.ensureIndices(('challengeId', 'name'))

    def list(self, challenge, user=None, limit=50, offset=0, sort=None):
        """
        List phases for a challenge.
        """
        cursor = self.find(
            {'challengeId': challenge['_id']}, limit=0, sort=sort)

        for r in self.filterResultsByPermission(cursor=cursor, user=user,
                                                level=AccessType.READ,
                                                limit=limit, offset=offset):
            yield r

    def validate(self, doc):
        return doc

    def remove(self, phase):
        # TODO remove all submissions, etc
        AccessControlledModel.remove(self, phase)

    def createPhase(self, name, challenge, creator, description='',
                    instructions='', active=False, public=True,
                    participantGroup=None, groundTruthFolder=None):
        """
        Create a new phase for a challenge. Will create a top-level folder under
        the challenge's collection. Will also create a new group for the
        participants of this phase unless an existing group is passed as the
        participantGroup parameter.

        :param name: The name of this phase. Do not include the challenge name
        in the phase name as that will cause redundant names to be displayed.
        :type name: str
        :param challenge: The challenge to which this phase belongs.
        :type challenge: dict
        :param creator: The user creating this phase.
        :type creator: dict
        :param participantGroup: If you wish to use an existing group for the
        phase's participants, pass that document as this param. If set to None,
        will make a new group based on the challenge and phase name.
        :type participantGroup: dict or None
        :param active: Whether this phase is active (i.e. accepting
        submissions).
        :type active: bool
        :param description: A description for this phase.
        :type description: str
        :param instructions: Instructions to participants for this phase.
        :type instructions: str
        :param public: Whether this phase is publicly visible.
        :type public: bool
        :param groundTruthFolder: The folder containing ground truth data
        for this challenge phase. If set to None, will create one under this
        phase's folder.
        """
        collection = self.model('collection').load(challenge['collectionId'],
                                                   force=True)
        folder = self.model('folder').createFolder(
            collection, name, parentType='collection', public=public,
            creator=creator)

        if groundTruthFolder is None:
            groundTruthFolder = self.model('folder').createFolder(
                folder, 'Ground truth', parentType='folder', public=False,
                creator=creator)

        if participantGroup is None:
            groupName = '{} {} participants'.format(challenge['name'], name)
            participantGroup = self.model('group').createGroup(
                groupName, creator, public=public)

        phase = {
            'name': name,
            'description': description,
            'instructions': instructions,
            'active': active,
            'challengeId': challenge['_id'],
            'folderId': folder['_id'],
            'participantGroupId': participantGroup['_id'],
            'groundTruthFolderId': groundTruthFolder['_id']
        }

        self.setPublic(phase, public=public)
        self.setUserAccess(phase, user=creator, level=AccessType.ADMIN)
        self.setGroupAccess(phase, participantGroup, level=AccessType.READ)

        return self.save(phase)

    def filter(self, phase, user=None):
        # TODO filter
        return phase
