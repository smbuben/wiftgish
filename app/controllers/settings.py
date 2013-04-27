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

import base
import app.models.settings


class Handler(base.RequestHandler):

    def get(self):
        # Clear the navigation breadcrumb whenever the settings page is visited.
        self.session.pop('breadcrumb', None)
        template_vals = app.models.settings.get_settings()
        self.render('settings.html', **template_vals)

    def post(self):
        app.models.settings.update_settings(
            self.request.get('firstname'),
            self.request.get('lastname'))
        self.flash(
            'Your settings have been updated.',
            level=self.flash_success)
        self.go('/settings')
