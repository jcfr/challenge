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
                    active=False, public=True):
        collection = self.model('collection').load(challenge['collectionId'],
                                                   force=True)
        folder = self.model('folder').createFolder(
            collection, name, parentType='collection', public=public,
            creator=creator)

        phase = {
            'name': name,
            'description': description,
            'active': active,
            'challengeId': challenge['_id'],
            'folderId': folder['_id']
        }

        self.setPublic(phase, public=public)
        self.setUserAccess(phase, user=creator, level=AccessType.ADMIN)

        return self.save(phase)

    def filter(self, phase, user=None):
        # TODO filter
        return phase
