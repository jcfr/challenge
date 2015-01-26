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

import datetime

from girder.constants import AccessType
from girder.models.model_base import AccessControlledModel


class Challenge(AccessControlledModel):
    def initialize(self):
        self.name = 'challenge_challenge'
        self.ensureIndices(('collectionId', 'name'))
        self.ensureTextIndex({
            'name': 10,
            'description': 1
        })

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
        doc['name'] = doc['name'].strip()
        if doc.get('description'):
            doc['description'] = doc['description'].strip()
        if doc.get('instructions'):
            doc['instructions'] = doc['instructions'].strip()

        if not doc['name']:
            raise ValidationException(
                'Challenge name must not be empty.', 'name')

        # Ensure unique name for the collection
        q = {
            'name': doc['name']
        }
        if '_id' in doc:
            q['_id'] = {'$ne': doc['_id']}
        duplicate = self.findOne(q, fields=['_id'])
        if duplicate is not None:
            raise ValidationException('A challenge with that name already '
                                      'exists.', 'name')

        return doc

    def remove(self, challenge):
        # TODO remove all phases
        AccessControlledModel.remove(self, challenge)

    def createChallenge(self, name, creator, description='', instructions='',
                        public=True):
        collection = self.model('collection').findOne({
            'name': name
        })

        if collection is None:
            collection = self.model('collection').createCollection(
                name, creator=creator, public=public)
        challenge = {
            'name': name,
            'creatorId': creator['_id'],
            'collectionId': collection['_id'],
            'description': description,
            'instructions': instructions,
            'created': datetime.datetime.now()
        }

        self.setPublic(challenge, public=public)
        self.setUserAccess(challenge, user=creator, level=AccessType.ADMIN)

        return self.save(challenge)

    def filter(self, challenge, user=None):
        """
        Filter a challenge document for display to the user.
        """
        keys = ['_id', 'creatorId', 'collectionId', 'name', 'description',
                'instructions']

        filtered = self.filterDocument(challenge, allow=keys)
        filtered['_accessLevel'] = self.getAccessLevel(challenge, user)

        return filtered
