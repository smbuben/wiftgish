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
            self.flash(
                'You\'ve already created the maximum number of groups.')
        except app.models.errors.BadValueError:
            self.flash(
                'You didn\'t enter something quite right. '
                'Please try again.')
        except app.models.errors.GroupJoinError:
            self.flash(
                'We couldn\'t add you to this group. '
                'Please create an invitation for yourself.')
        else:
            return self.go('/groups/' + group_key)
        self.go('/')


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
            self.flash(
                'That\'s not a valid email address. '
                'Please try again.')
        except app.models.errors.MailError:
            self.flash(
                'We couldn\'t send the invitation to %s on your behalf. '
                'You will have to send it manually.'
                    % (email))
        else:
            # Give additional positive feedback if the invitation is to be sent.
            if send:
                self.flash(
                    'An invitation has been sent to %s. ' % (email),
                    level=self.flash_success)
            else:
                self.flash(
                    'A new invitation was created. '
                    'But, you will need to send the invitation to %s yourself.'
                        % (email),
                    level=self.flash_warn)
        # Not redirecting to the invites anchor so the user can see the flash.
        self.go('/groups/' + group_key)


class CreateMember(base.RequestHandler):

    def get(self, code):
        try:
            code = code.strip()
            if code != app.models.util.sanitize(code, strict=True, trunc=40):
                raise app.models.errors.GroupJoinError
            group_key = app.models.groups.create_member(code)
        except app.models.errors.GroupJoinError:
            self.flash(
                'That invitation code is not valid. '
                'Please contact the sender for a new invitation.')
        else:
            return self.go('/groups/' + group_key)
        self.go('/')

    def post(self):
        self.get(self.request.get('code'))


class Update(base.RequestHandler):

    def post(self):
        try:
            group_key = self.request.get('group')
            title = self.request.get('title')
            message = self.request.get('message')
            app.models.groups.update_group(group_key, title, message)
        except app.models.errors.BadValueError:
            self.flash(
                'You didn\'t enter something quite right. '
                'Please try again.')
        self.go('/groups/' + group_key)


class Delete(base.RequestHandler):

    def post(self):
        group_key = self.request.get('group')
        group_title = app.models.groups.get_title(group_key)
        app.models.groups.delete_group(group_key)
        self.go('/#groups')


class DeleteInvitation(base.RequestHandler):

    def post(self):
        invitation_key = self.request.get('invite')
        group_key = app.models.groups.get_from_invitation(invitation_key)
        app.models.groups.delete_invitation(invitation_key)
        self.go('/groups/' + group_key + '#invites')


class DeleteMember(base.RequestHandler):

    def post(self):
        member_key = self.request.get('member')
        group_key = app.models.groups.get_from_member(member_key)
        app.models.groups.delete_member(member_key)
        self.go('/groups/' + group_key + '#members')


class DeleteSelf(base.RequestHandler):

    def post(self):
        group_key = self.request.get('group')
        group_title = app.models.groups.get_title(group_key)
        app.models.groups.delete_self(group_key)
        self.flash(
            'You are no longer a member of group %s.' % (group_title),
            level=self.flash_success)
        self.go('/')

