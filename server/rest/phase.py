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
from girder.api.rest import Resource, loadmodel
from girder.constants import AccessType


class Phase(Resource):
    def __init__(self):
        self.resourceName = 'challenge_phase'

        self.route('GET', (), self.listPhases)
        self.route('POST', (), self.createPhase)
        self.route('PUT', (':id', 'access'), self.updateAccess)

    @access.public
    @loadmodel(map={'challengeId': 'challenge'}, model='challenge',
               plugin='challenge', level=AccessType.READ)
    def listPhases(self, challenge, params):
        limit, offset, sort = self.getPagingParameters(params, 'name')

        user = self.getCurrentUser()
        results = self.model('phase', 'challenge').list(
            challenge, user=user, offset=offset, limit=limit, sort=sort)
        return [self.model('phase', 'challenge').filter(p, user)
                for p in results]
    listPhases.description = (
        Description('List phases for a challenge.')
        .param('challengeId', 'The ID of the challenge.')
        .param('limit', "Result set size limit (default=50).", required=False,
               dataType='int')
        .param('offset', "Offset into result set (default=0).", required=False,
               dataType='int')
        .param('sort', "Field to sort the result list by (default=name)",
               required=False)
        .param('sortdir', "1 for ascending, -1 for descending (default=1)",
               required=False, dataType='int'))

    @access.user
    @loadmodel(map={'challengeId': 'challenge'}, level=AccessType.WRITE,
               model='challenge', plugin='challenge')
    def createPhase(self, challenge, params):
        public = self.boolParam('public', params, default=False)
        description = params.get('description', '').strip()

        phase = self.model('phase', 'challenge').createPhase(
            name=params['name'].strip(), description=description, public=public,
            creator=self.getCurrentUser(), challenge=challenge)

        return phase
    createPhase.description = (
        Description('Add a phase to an existing challenge.')
        .param('challengeId', 'The ID of the challenge to add the phase to.')
        .param('name', 'The name for this phase.')
        .param('description', 'Description for this phase.', required=False)
        .param('public', 'Whether the phase should be publicly visible.',
               dataType='boolean'))

    @access.user
    @loadmodel(map={'id': 'phase'}, level=AccessType.ADMIN,
               model='phase', plugin='challenge')
    def updateAccess(self, phase, params):
        self.requireParams('access', params)

        public = self.boolParam('public', params, default=False)
        self.model('phase', 'challenge').setPublic(phase, public)

        try:
            access = json.loads(params['access'])
            return self.model('phase', 'challenge').setAccessList(
                phase, access, save=True)
        except ValueError:
            raise RestException('The access parameter must be JSON.')
    updateAccess.description = (
        Description('Set the access control list for a challenge phase.')
        .param('id', 'The ID of the phase.', paramType='path')
        .param('access', 'The access control list as JSON.')
        .param('public', 'Whether the phase should be publicly visible.',
               dataType='boolean')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin permission denied on the phase.', 403))

    def filter(self, phase, user=None):
        # TODO filter
        return phase
