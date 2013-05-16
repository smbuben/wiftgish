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
import app.config
import app.models.groups
import app.models.errors
import app.models.util
import os


class Display(base.RequestHandler):

    def get(self, group_key):
        template_vals = app.models.groups.get_members_and_invites(group_key)
        template_vals['domain'] = app.config.DOMAIN
        if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
            template_vals['domain'] = 'localhost:8080'
        self.session.pop('breadcrumb', None)
        self.render('group.html', **template_vals)
        self.session['breadcrumb'] = (app.config.PATH_PREFIX
            + '/groups/'+ group_key, template_vals['title'])


class Create(base.RequestHandler):

    def post(self):
        try:
            title = self.request.get('title')
            message = self.request.get('message')
            group_key = app.models.groups.create_group(title, message)
        except app.models.errors.MaxValueError:
            alert = 'You\'ve already created the maximum number of groups.'
            self.ajax_fail(alert=alert)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        except app.models.errors.GroupJoinError:
            alert = 'The group %s was created, but you aren\'t a member yet. ' \
                    'Please create an invitation for yourself.' \
                    % (title)
            self.ajax_success(alert=alert)
        else:
            self.ajax_success(redirect='/groups/' + group_key)


class CreateInvitation(base.RequestHandler):

    def post(self):
        try:
            group_key = self.request.get('group')
            email = self.request.get('email')
            message = self.request.get('message')
            send = self.request.get('send') == 'on'
            salt = self.app.config.get('private_salt')
            app.models.groups.create_invitation(group_key, email, message, send, salt)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        except app.models.errors.MailError:
            alert = 'A new invitation has been created, ' \
                    'but we couldn\'t send it to %s. ' \
                    'You will have to send the invitation code yourself.' \
                    % (email)
            self.ajax_success(alert=alert)
        else:
            if send:
                alert = 'An invitation has been sent to %s' % (email)
                self.ajax_success(alert=alert)
            else:
                alert = 'A new invitation has been created, ' \
                        'but it has not been sent to %s. ' \
                        'You will have to send the invitation code yourself.' \
                        % (email)
                self.ajax_success(alert=alert)


class CreateMember(base.RequestHandler):

    def get(self, code):
        try:
            code = code.strip()
            if code != app.models.util.sanitize(code, strict=True, trunc=40):
                raise app.models.errors.GroupJoinError
            group_key = app.models.groups.create_member(code)
        except app.models.errors.GroupJoinError:
            self.flash(
                'That invitation is not valid. '
                'Please contact the sender for a new invitation.')
            self.go('/')
        else:
            self.go('/groups/' + group_key)

    def post(self):
        try:
            code = self.request.get('code')
            group_key = app.models.groups.create_member(code)
        except app.models.errors.GroupJoinError:
            alert = 'The entered invitation code is not valid. ' \
                    'Please check your entry and try again, ' \
                    'or contact the sender for a new invitation.'
            self.ajax_fail(alert=alert)
        else:
            self.ajax_success(redirect='/groups/' + group_key)


class Update(base.RequestHandler):

    def post(self):
        try:
            group_key = self.request.get('group')
            title = self.request.get('title')
            message = self.request.get('message')
            app.models.groups.update_group(group_key, title, message)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        else:
            self.ajax_success()


class Delete(base.RequestHandler):

    def post(self):
        group_key = self.request.get('group')
        app.models.groups.delete_group(group_key)
        self.ajax_success()


class DeleteWithRedirect(base.RequestHandler):

    def post(self):
        group_key = self.request.get('group')
        group_title = app.models.groups.get_title(group_key)
        app.models.groups.delete_group(group_key)
        self.go('/#groups')


class DeleteInvitation(base.RequestHandler):

    def post(self):
        invitation_key = self.request.get('invite')
        app.models.groups.delete_invitation(invitation_key)
        self.ajax_success()


class DeleteMember(base.RequestHandler):

    def post(self):
        member_key = self.request.get('member')
        app.models.groups.delete_member(member_key)
        self.ajax_success()


class DeleteSelf(base.RequestHandler):

    def post(self):
        group_key = self.request.get('group')
        app.models.groups.delete_self(group_key)
        self.ajax_success()

