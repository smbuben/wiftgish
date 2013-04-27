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

from google.appengine.api import users
import webapp2
import webapp2_extras.jinja2
import app.config


class RequestHandler(webapp2.RequestHandler):
    """
    Base class for launcher requests.
    """

    @webapp2.cached_property
    def jinja2(self):
        # Return a Jinja2 renderer cached in the app registry.
        return webapp2_extras.jinja2.get_jinja2(app=self.app)


class Index(RequestHandler):
    """
    Index and login page.
    """

    def get(self):
        # If the user is logged-in then bootstrap into the main application.
        if users.get_current_user():
            return self.redirect(app.config.INIT_PATH)

        # Otherwise render the login page.
        template_vals = {
            'login_url' : users.create_login_url(app.config.INIT_PATH),
        }
        view = self.jinja2.render_template('index.html', **template_vals)
        self.response.write(view)


class Default(RequestHandler):
    """
    Everything-else handler.
    """

    def get(self):
        self.redirect('/')

