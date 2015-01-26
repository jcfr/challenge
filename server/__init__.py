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

from .rest import challenge, phase
from girder import events
from girder.api import rest
from girder.utility.model_importer import ModelImporter


def searchModels(event):

    if 'challenge_challenge' in event.info['params']['types']:
        user = rest.getCurrentUser()
        event.info['returnVal']['challenge_challenge'] = [
            ModelImporter.model('challenge', 'challenge').filter(c) for c in
            ModelImporter.model('challenge', 'challenge').textSearch(
                event.info['params']['q'], user=user)
        ]


def load(info):
    events.bind('rest.get.resource/search.after', 'challenge', searchModels)
    info['apiRoot'].challenge = challenge.Challenge()
    info['apiRoot'].challenge_phase = phase.Phase()
