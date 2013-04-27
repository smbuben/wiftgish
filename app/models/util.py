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
Helper functions used by this module.
"""

import re


def sanitize(data, strict=False, trunc=None):
    """
    Sanitize input strings.

    Strict mode is intended for strings used outside the application (e.g.
    the invitation email). Non-strict mode is intended for strings that will
    be used and displayed (and escaped) by the local application.
    """
    if not trunc is None:
        data = data[:trunc]
    data = data.replace('"', '\'')
    if not strict:
        return re.sub(r'[^-a-zA-Z0-9 \r\n_.,!?;:+*=@#$%&()/\']', '', data)
    return re.sub(r'[^-a-zA-Z0-9 \r\n_.,!?\']', '', data)

