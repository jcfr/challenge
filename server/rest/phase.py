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
        self.route('GET', (':id',), self.getPhase)
        self.route('GET', (':id', 'access'), self.getAccess)
        self.route('POST', (), self.createPhase)
        self.route('POST', (':id', 'participant'), self.joinPhase)
        self.route('PUT', (':id',), self.updatePhase)
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
        self.requireParams('name', params)

        user = self.getCurrentUser()
        public = self.boolParam('public', params, default=False)
        active = self.boolParam('active', params, default=False)
        description = params.get('description', '').strip()
        instructions = params.get('instructions', '').strip()

        participantGroupId = params.get('participantGroupId')
        if participantGroupId:
            group = self.model('group').load(
                participantGroupId, user=user, level=AccessType.READ)
        else:
            group = None

        phase = self.model('phase', 'challenge').createPhase(
            name=params['name'].strip(), description=description,
            instructions=instructions, active=active, public=public,
            creator=user, challenge=challenge, participantGroup=group)

        return phase
    createPhase.description = (
        Description('Add a phase to an existing challenge.')
        .param('challengeId', 'The ID of the challenge to add the phase to.')
        .param('name', 'The name for this phase.')
        .param('description', 'Description for this phase.', required=False)
        .param('instructions', 'Instructions to participants for this phase.',
               required=False)
        .param('participantGroupId', 'If you wish to use an existing '
               'group as the participant group, pass its ID in this parameter.'
               ' If you omit this, a participant group will be automatically '
               'created for this phase.', required=False)
        .param('public', 'Whether the phase should be publicly visible.',
               dataType='boolean')
        .param('active',
            'Whether the phase will accept and score additional submissions.',
            dataType='boolean', required=False))

    @access.user
    @loadmodel(model='phase', plugin='challenge', level=AccessType.ADMIN)
    def getAccess(self, phase, params):
        return self.model('phase', 'challenge').getFullAccessList(phase)
    getAccess.description = (
        Description('Get the access control list for a phase.')
        .param('id', 'The ID of the phase.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Admin access was denied for the phase.', 403))

    @access.user
    @loadmodel(model='phase', plugin='challenge', level=AccessType.ADMIN)
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

    @access.user
    @loadmodel(model='phase', plugin='challenge', level=AccessType.WRITE)
    def updatePhase(self, phase, params):
        phase['active'] = self.boolParam('active', params, phase['active'])
        phase['name'] = params.get('name', phase['name']).strip()
        phase['description'] = params.get('description',
                                          phase.get('description', '')).strip()
        phase['instructions'] = params.get(
            'instructions', phase.get('instructions', '')).strip()
        if 'participantGroupId' in params:
            participantGroupId = params['participantGroupId'].strip()
            # load the group to validate
            user = self.getCurrentUser()
            self.model('group').load(
                participantGroupId, user=user, level=AccessType.READ)
            phase['participantGroupId'] = participantGroupId

        self.model('phase', 'challenge').updatePhase(phase)
        return phase
    updatePhase.description = (
        Description('Update the properties of a challenge phase.')
        .responseClass('Phase')
        .param('id', 'The ID of the phase.', paramType='path')
        .param('name', 'The name for this phase.', required=False)
        .param('description', 'Description for this phase.', required=False)
        .param('instructions', 'Instructions to participants for this phase.',
               required=False)
        .param('participantGroupId', 'ID of an existing group to set as the '
               'participant group for this phase.', required=False)
        .param('active',
            'Whether the phase will accept and score additional submissions.',
            dataType='boolean', required=False)
        .errorResponse('ID was invalid.')
        .errorResponse('Write permission denied on the phase.', 403))

    @access.public
    @loadmodel(model='phase', plugin='challenge', level=AccessType.READ)
    def getPhase(self, phase, params):
        return self.model('phase', 'challenge').filter(
                          phase, self.getCurrentUser())
    getPhase.description = (
        Description('Get a phase by ID.')
        .responseClass('Phase')
        .param('id', 'The ID of the phase.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read permission denied on the phase.', 403))

    @access.user
    @loadmodel(model='phase', plugin='challenge', level=AccessType.READ)
    def joinPhase(self, phase, params):
        user = self.getCurrentUser()
        phase = self.model('phase', 'challenge').filter(
                           phase, self.getCurrentUser())
        participantGroupId = phase['participantGroupId']
        if 'groups' not in user or participantGroupId not in user['groups']:
            participantGroup = self.model('group').load(
                participantGroupId, user=user, level=AccessType.READ)
            self.model('group').addUser(participantGroup, user,
                                        level=AccessType.READ)
        return phase
    joinPhase.description = (
        Description('Join a phase as a competitor.')
        .responseClass('Phase')
        .param('id', 'The ID of the phase.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read permission denied on the phase.', 403))
