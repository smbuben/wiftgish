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

import webapp2
import webapp2_extras.sessions
import webapp2_extras.jinja2
import app.config
import app.models.overview


class RequestHandler(webapp2.RequestHandler):

    # Flash message levels.
    flash_failure = 0
    flash_warn = 1
    flash_info = 2
    flash_success = 3

    def dispatch(self):
        # Get the session store for this request.
        self.session_store = \
            webapp2_extras.sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Return the session with the default cookie key.
        return self.session_store.get_session()

    @webapp2.cached_property
    def jinja2(self):
        # Return a Jinja2 renderer cached in the app registry.
        return webapp2_extras.jinja2.get_jinja2(app=self.app)

    def render(self, template, **template_vals):
        # Get the current user info that is required for all templates.
        template_vals.update(app.models.overview.get_current_user_info())
        # Set all other info required for all templates.
        template_vals.update(
            {
                'prefix' :      app.config.PATH_PREFIX,
                'breadcrumb' :  self.session.get('breadcrumb'),
                'messages' :    self.session.get_flashes(),
            })
        rendered_view = self.jinja2.render_template(template, **template_vals)
        self.response.write(rendered_view)

    def go(self, path):
        self.redirect(app.config.PATH_PREFIX + path)

    def flash(self, message, level=flash_failure):
        if not self.session.has_key('messages'):
            self.session['messages'] = list()
        if level == self.flash_failure:
            message = 'Uh oh! ' + message
        elif level == self.flash_success:
            message = 'Success! ' + message
        level = {
            self.flash_failure :    'alert-error',
            self.flash_warn:        '',
            self.flash_info :       'alert-info',
            self.flash_success :    'alert-success',
        }[level]
        self.session.add_flash(message, level)

