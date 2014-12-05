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


class Challenge(AccessControlledModel):
    def initialize(self):
        self.name = 'challenge_challenge'
        self.ensureIndices(('collectionId', 'name'))

    def list(self, user=None, limit=50, offset=0, sort=None):
        """
        List a page of challenges.
        """
        cursor = self.find({}, limit=0, sort=sort)

        for r in self.filterResultsByPermission(cursor=cursor, user=user,
                                                level=AccessType.READ,
                                                limit=limit, offset=offset):
            yield r

    def validate(self, doc):
        return doc

    def remove(self, challenge):
        # TODO remove all phases
        AccessControlledModel.remove(self, challenge)

    def createChallenge(self, name, creator, description='', instructions='',
                        public=True):
        collection = self.model('collection').createCollection(
            name, creator=creator, public=public)
        challenge = {
            'name': name,
            'creatorId': creator['_id'],
            'collectionId': collection['_id'],
            'description': description,
            'instructions': instructions
        }

        self.setPublic(challenge, public=public)
        self.setUserAccess(challenge, user=creator, level=AccessType.ADMIN)

        return self.save(challenge)

    def filter(self, challenge, user=None):
        """
        Filter a challenge document for display to the user.
        """
        keys = ['_id', 'creatorId', 'collectionId', 'name', 'description', 'instructrions']

        filtered = self.filterDocument(challenge, allow=keys)

        filtered['_accessLevel'] = self.getAccessLevel(
            challenge, user)

        return filtered
