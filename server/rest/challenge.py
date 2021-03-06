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

import json

from girder.api import access
from girder.api.describe import Description
from girder.api.rest import Resource, loadmodel, RestException
from girder.constants import AccessType
from girder.utility.progress import ProgressContext


class Challenge(Resource):
    def __init__(self):
        self.resourceName = 'challenge'

        self.route('GET', (), self.listChallenges)
        self.route('GET', (':id',), self.getChallenge)
        self.route('GET', (':id', 'access'), self.getAccess)
        self.route('POST', (), self.createChallenge)
        self.route('PUT', (':id',), self.updateChallenge)
        self.route('PUT', (':id', 'access'), self.updateAccess)
        self.route('DELETE', (':id',), self.deleteChallenge)

    @access.public
    def listChallenges(self, params):
        limit, offset, sort = self.getPagingParameters(params, 'name')

        user = self.getCurrentUser()
        results = self.model('challenge', 'challenge').list(
            user=user, offset=offset, limit=limit, sort=sort)
        return [self.model('challenge', 'challenge').filter(c, user)
                for c in results]
    listChallenges.description = (
        Description('List challenges.')
        .param('limit', "Result set size limit (default=50).", required=False,
               dataType='int')
        .param('offset', "Offset into result set (default=0).", required=False,
               dataType='int')
        .param('sort', "Field to sort the result list by (default=name)",
               required=False)
        .param('sortdir', "1 for ascending, -1 for descending (default=1)",
               required=False, dataType='int'))

    @access.admin
    def createChallenge(self, params):
        self.requireParams('name', params)
        public = self.boolParam('public', params, default=False)
        description = params.get('description', '').strip()
        instructions = params.get('instructions', '').strip()

        challenge = self.model('challenge', 'challenge').createChallenge(
            name=params['name'].strip(), description=description, public=public,
            instructions=instructions, creator=self.getCurrentUser())

        return challenge
    createChallenge.description = (
        Description('Create a new challenge.')
        .param('name', 'The name for this challenge.')
        .param('description', 'Description for this challenge.', required=False)
        .param('instructions', 'Instructional text for this challenge.',
               required=False)
        .param('public', 'Whether the challenge should be publicly visible.',
               dataType='boolean'))

    @access.user
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.WRITE)
    def updateChallenge(self, challenge, params):
        challenge['name'] = params.get('name', challenge['name']).strip()
        challenge['description'] = params.get(
            'description', challenge.get('description', '')).strip()
        challenge['instructions'] = params.get(
            'instructions', challenge.get('instructions', '')).strip()

        self.model('challenge', 'challenge').save(challenge)
        return challenge
    updateChallenge.description = (
        Description('Update the properties of a challenge.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .param('name', 'The name for this challenge.', required=False)
        .param('description', 'Description for this challenge.', required=False)
        .param('instructions', 'Instructions to participants for this '
               'challenge.', required=False)
        .errorResponse('ID was invalid.')
        .errorResponse('Write permission denied on the challenge.', 403))

    @access.user
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.ADMIN)
    def updateAccess(self, challenge, params):
        self.requireParams('access', params)

        public = self.boolParam('public', params, default=False)
        self.model('challenge', 'challenge').setPublic(challenge, public)

        try:
            access = json.loads(params['access'])
            return self.model('challenge', 'challenge').setAccessList(
                challenge, access, save=True)
        except ValueError:
            raise RestException('The access parameter must be JSON.')
    updateAccess.description = (
        Description('Set the access control list for a challenge.')
        .param('id', 'The ID of the challenge.', paramType='path')
        .param('access', 'The access control list as JSON.')
        .param('public', 'Whether the challenge should be publicly visible.',
               dataType='boolean')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin permission denied on the challenge.', 403))

    @access.public
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.READ)
    def getChallenge(self, challenge, params):
        return self.model('challenge', 'challenge').filter(
            challenge, self.getCurrentUser())
    getChallenge.description = (
        Description('Get a challenge by ID.')
        .responseClass('Challenge')
        .param('id', 'The ID of the challenge.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read permission denied on the challenge.', 403))

    @access.user
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.ADMIN)
    def getAccess(self, challenge, params):
        return self.model('challenge', 'challenge').getFullAccessList(challenge)
    getAccess.description = (
        Description('Get the access control list for a challenge.')
        .param('id', 'The ID of the phase.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the challenge.', 403))

    @access.user
    @loadmodel(model='challenge', plugin='challenge', level=AccessType.ADMIN)
    def deleteChallenge(self, challenge, params):
        progress = self.boolParam('progress', params, default=False)
        with ProgressContext(progress, user=self.getCurrentUser(),
                             title=u'Deleting challenge ' + challenge['name'],
                             message='Calculating total size...') as ctx:
            if progress:
                ctx.update(
                    total=self.model('challenge', 'challenge').subtreeCount(
                        challenge))
            self.model('challenge', 'challenge').remove(challenge, progress=ctx)
        return {'message': 'Deleted challenge %s.' % challenge['name']}
    deleteChallenge.description = (
        Description('Delete a challenge.')
        .param('id', 'The ID of the challenge to delete.', paramType='path')
        .param('progress', 'Whether to record progress on this task. Default '
               'is false.', required=False, dataType='boolean')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the challenge.', 403))
