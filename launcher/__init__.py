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
Web application to handle non-logged-in users and bootstrap into the main application.
"""

import webapp2
import jinja2_extras.filters
import os


# Initialize the Webap2 application.
wsgi_app = webapp2.WSGIApplication(
    [
        (r'/', 'launcher.controllers.Index'),
        (r'.*', 'launcher.controllers.Default'),
    ],
    config={
        'webapp2_extras.jinja2' :
            {
                'template_path' :   'launcher/views',
                'filters' :         jinja2_extras.filters.all_filters,
            },
    },
    debug=os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'))

