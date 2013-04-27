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
Functions related to managing users' settings.
"""

from google.appengine.api import memcache
from google.appengine.api import users

import app.config
import models
import util


def __get_settings(user=None):
    """
    Retrieve a user's settings.
    If a user is not provided, the settings of the current user are retrieved.
    """
    if user is None:
        user = users.get_current_user()
    settings_key = user.user_id() + '__SET'
    settings = memcache.get(settings_key)
    if settings is None:
        settings = models.Settings.get_by_key_name(settings_key)
        if settings is None:
            memcache.set(settings_key, False, time=app.config.TIME_CACHE_DATA)
        else:
            memcache.set(settings_key, settings, time=app.config.TIME_CACHE_DATA)
    elif settings is False:
        settings = None
    return settings


def is_modified():
    """
    Determine whether or not the current user has ever modified their settings.
    """
    settings = __get_settings()
    if settings:
        return True
    return False


def get_settings():
    """
    Retrieve the current user's settings.
    """
    return {'settings' : __get_settings()}


def get_display_name(user=None):
    """
    Retrieve the name to display for a user.
    If a user is not provided, the display name of the current user is retrieved.
    """
    settings = __get_settings(user)
    if not settings or (settings.firstname == '' and settings.lastname == ''):
        return user.nickname()
    return settings.firstname + ' ' + settings.lastname


def update_settings(firstname, lastname):
    """
    Modify the current user's settings.
    """
    user = users.get_current_user()
    key = user.user_id() + '__SET'
    settings = __get_settings(user)
    if not settings:
        settings = models.Settings(key_name=key)
    settings.firstname = util.sanitize(firstname, strict=True, trunc=app.config.TEXT_LINE_LENGTH)
    settings.lastname = util.sanitize(lastname, strict=True, trunc=app.config.TEXT_LINE_LENGTH)
    settings.put()
    memcache.set(key, settings, time=app.config.TIME_CACHE_DATA)

