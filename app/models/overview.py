#
# This file is part of the Wiftgish project.
#
# Copyright (C) 2013 Stephen M Buben <smbuben@gmail.com>
#
# Wiftgish is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Wiftgish is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Wiftgish.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Functions related to summary information for a single user.
"""

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

import app.config
import models


def get_current_user_info():
    """
    Retrieve all information associated with the current user:
        - user object
        - wish lists
        - list-sharing groups/memberships
        - settings
    """
    user = users.get_current_user()
    cache_keys = [user.user_id() + x for x in ['__L', '__G', '__M', '__SET']]
    cache_vals = memcache.get_multi(cache_keys)
    [lists, groups, memberships, settings] = [cache_vals.get(x) for x in cache_keys]
    cache_vals.clear()

    if lists is None:
        lists = models.List.gql(
                'WHERE owner = :1', user
            ).fetch(None)
        cache_vals[cache_keys[0]] = lists

    lists_left = app.config.NUM_LISTS_MAX - len(lists)
    if lists_left < 0:
        lists_left = 0

    if groups is None:
        groups = models.Group.gql(
                'WHERE owner = :1', user
            ).fetch(None)
        cache_vals[cache_keys[1]] = groups

    groups_left = app.config.NUM_GROUPS_MAX - len(groups)
    if groups_left < 0:
        groups_left = 0

    if memberships is None:
        memberships =  models.Member.gql(
                'WHERE owner = :1', user
            ).fetch(None)
        cache_vals[cache_keys[2]] = memberships

    groups = [{'entity' : g, 'owner' : True, 'member' : False} for g in groups]
    for m in memberships:
        for g in groups:
            if models.Member.group.get_value_for_datastore(m) == g['entity'].key():
                g['member'] = True
                break
        else:
            groups.append({'entity' : m.group, 'owner' : False, 'member' : True})

    if settings is None:
        settings = models.Settings.get_by_key_name(cache_keys[3])
        if settings is None:
            cache_vals[cache_keys[3]] = False
        else:
            cache_vals[cache_keys[3]] = settings

    if cache_vals:
        memcache.set_multi(cache_vals, time=app.config.TIME_CACHE_DATA)

    result = {
        'user' :            user,
        'lists' :           lists,
        'lists_left' :      lists_left,
        'groups' :          groups,
        'groups_left' :     groups_left,
        'settings' :        settings,
    }
    return result

