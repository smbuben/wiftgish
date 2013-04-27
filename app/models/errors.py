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
Exceptions that will be raised by this module.
"""

from google.appengine.ext import db
from google.appengine.api import mail


class Error(Exception):
    pass

class QueryError(Error):
    pass

class StoreError(Error):
    pass

class PermissionError(Error):
    pass

class MaxValueError(Error):
    pass

class GroupJoinError(Error):
    pass

BadValueError = db.BadValueError

MailError = mail.Error

