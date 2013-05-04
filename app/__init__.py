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
The Wiftgish web application.
"""

import webapp2
import webapp2_extras.jinja2
import webapp2_extras.routes
import jinja2_extras.filters
import app.config
import os
import logging


class Defaults:
    """
    Default configuration values to use in the event that the private
    configuration module is not available.
    """

    # Default session cookie key.
    session_cookie_key = ''

    # Default salt value.
    salt = ''

    def __init__(self):
        logging.warn('Using built-in default configuration.')
        logging.warn('Create a custom private configuration to fix.')


# Try to load the private configuration module.
# Fallback to defaults if unavailable.
try:
    import private
except:
    private = Defaults()


# Shortcuts.
route = webapp2.Route
prefix = webapp2_extras.routes.PathPrefixRoute

# Initialize the Webapp2 application.
wsgi_app = webapp2.WSGIApplication([
    prefix(app.config.PATH_PREFIX, [
        route(r'/', 'app.controllers.overview.Handler'),
        prefix('/groups', [
            route(r'/<:[-\w]+>', 'app.controllers.groups.Display'),
            route(r'/create/', 'app.controllers.groups.Create'),
            route(r'/create/member/', 'app.controllers.groups.CreateMember'),
            route(r'/create/invitation/', 'app.controllers.groups.CreateInvitation'),
            route(r'/update/', 'app.controllers.groups.Update'),
            route(r'/delete/', 'app.controllers.groups.Delete'),
            route(r'/delete/invitation/', 'app.controllers.groups.DeleteInvitation'),
            route(r'/delete/member/', 'app.controllers.groups.DeleteMember'),
            route(r'/delete/self/', 'app.controllers.groups.DeleteSelf'),
            route(r'/join/<:[\w]{40,40}>', 'app.controllers.groups.CreateMember'),
        ]),
        prefix('/lists', [
            route(r'/<:[-\w]+>', 'app.controllers.lists.Display'),
            route(r'/create/', 'app.controllers.lists.Create'),
            route(r'/create/gift/', 'app.controllers.lists.CreateGift'),
            route(r'/create/survey/', 'app.controllers.lists.CreateSurvey'),
            route(r'/update/', 'app.controllers.lists.Update'),
            route(r'/update/gift/<:[-\w]+>', 'app.controllers.lists.UpdateGift'),
            route(r'/update/survey/<:[-\w]+>', 'app.controllers.lists.UpdateSurvey'),
            route(r'/delete/', 'app.controllers.lists.Delete'),
            route(r'/delete/gift/', 'app.controllers.lists.DeleteGift'),
            route(r'/delete/survey/', 'app.controllers.lists.DeleteSurvey'),
            route(r'/purchase/gift/<:[-\w]+>', 'app.controllers.lists.PurchaseGift'),
            route(r'/unpurchase/gift/<:[-\w]+>', 'app.controllers.lists.UnpurchaseGift'),
        ]),
        route(r'/settings', 'app.controllers.settings.Handler'),
        route(r'/logout', 'app.controllers.logout.Handler'),
        ]),
    ],
    config={
        'webapp2_extras.sessions' :
            {
                'secret_key' :          private.session_cookie_key,
                'cookie_args' :
                    {
                        'httponly' :    True,
                    },
            },
        'webapp2_extras.jinja2' :
            {
                'template_path' :       'app/views',
                'filters' :             jinja2_extras.filters.all_filters,
            },
        'private_salt' :                private.salt,
    },
    debug=os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'))


# Custom error handling.
def render_error(template):
    template_vals = {
        'prefix':   app.config.PATH_PREFIX,
    }
    jinja2 = webapp2_extras.jinja2.get_jinja2(app=wsgi_app)
    return jinja2.render_template(template, **template_vals)

def handle_403(request, response, exception):
    logging.exception(exception)
    response.write(render_error('error_403.html'))
    response.set_status(403)

def handle_404(request, response, exception):
    logging.exception(exception)
    response.write(render_error('error_404.html'))
    response.set_status(404)

def handle_500(request, response, exception):
    logging.exception(exception)
    response.write(render_error('error_500.html'))
    response.set_status(500)

wsgi_app.error_handlers[403] = handle_403
wsgi_app.error_handlers[404] = handle_404
wsgi_app.error_handlers[500] = handle_500

