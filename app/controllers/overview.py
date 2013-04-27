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


class Handler(base.RequestHandler):

    def get(self):
        # Clear the navigation breadcrumb whenever the root page is visited.
        self.session.pop('breadcrumb', None)

        # This template requires nothing outside of the default data set
        # by the base class render method.
        template_vals = {'overview' : True}
        self.render('overview.html', **template_vals)

