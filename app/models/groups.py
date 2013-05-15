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
Functions related to managing groups of users.
"""

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

import app.config
import errors
import models
import settings
import util

import cgi
import hashlib
import os
import time


def __get_group_by_key(group_key, check_owner=True):
    """
    Retrieve a group entity by its datastore key and verify that the
    accessing user has the appropriate permission for the group.
    """
    group = memcache.get(group_key)
    if group is None:
        group = models.Group.get(group_key)
        memcache.set(group_key, group)
        if group is None:
            raise errors.QueryError
    user = users.get_current_user()
    if not user == group.owner:
        if check_owner or not __group_access_allowed(group_key, user):
            raise errors.PermissionError
    return group


def __group_access_allowed(group_key, user):
    """
    Verify that a user has permission to view a group by ensuring that the
    user is a member of the group.
    """
    memberships_key = user.user_id() + '__M'
    memberships = memcache.get(memberships_key)
    if not memberships:
        memberships = models.Member.gql(
                'WHERE owner = :1', user
            ).fetch(None)
        memcache.set(memberships_key, memberships, time=app.config.TIME_CACHE_DATA)
    for m in memberships:
        if str(models.Member.group.get_value_for_datastore(m)) == group_key:
            return True
    return False


def __del_cached_group(group_key):
    """
    Remove a group from the memcache.
    This must be done when a group is deleted to ensure that a consistent
    view is presented despite the HRD eventual consistency model.
    """
    user = users.get_current_user()
    user_groups_key = user.user_id() + '__G'
    groups = memcache.get(user_groups_key)
    if groups is None:
        groups = models.Group.gql(
                'WHERE owner = :1', user
            ).fetch(None)
    groups = [x for x in groups if str(x.key()) != group_key]
    memcache.set(user_groups_key, groups, time=app.config.TIME_CACHE_DATA)
    memcache.delete_multi([group_key, group_key + '__M', group_key + '__I'])


def __update_cached_group(group):
    """
    Update a group in the memcache.
    This must be done after each group modification to ensure that a
    consistent view is presented despite the HRD eventual consistency model.
    """
    group_key = str(group.key())
    user_groups_key = group.owner.user_id() + '__G'
    groups = memcache.get(user_groups_key)
    if groups is None:
        groups = models.Group.gql(
                'WHERE owner = :1', group.owner
            ).fetch(None)
    groups = [x for x in groups if str(x.key()) != group_key]
    groups.append(group)
    memcache.set_multi(
        {
            group_key :         group,
            user_groups_key :   groups
        },
        app.config.TIME_CACHE_DATA)


def __del_cached_members(members, group_key):
    """
    Remove reference to a group from members' memcache data.
    This must be done when a group is deleted to ensure that a consistent
    view is presented despite the HRD eventual consistency model.
    """
    # There is room for optimization here.
    # But, this shouldn't be called very often so I currently don't care.
    cache_vals = {}
    for member in members:
        user = member.owner
        user_members_key = user.user_id() + '__M'
        user_members = memcache.get(user_members_key)
        if user_members is None:
            user_members = models.Member.gql(
                    'WHERE owner = :1', user
                ).fetch(None)
        user_members = [x for x in user_members if str(x.group.key()) != group_key]
        cache_vals[user_members_key] = user_members
    memcache.set_multi(cache_vals, time=app.config.TIME_CACHE_DATA)


def __del_cached_member(group, user, member_key):
    """
    Remove reference to a member from the memcache.
    This must be done when a member is deleted to ensure that a consistent
    view is presented despite the HRD eventual consistency model.
    """
    group_key = str(group.key())
    cache_keys = [x + '__M' for x in [group_key, user.user_id()]]
    cache_vals = memcache.get_multi(cache_keys)
    [group_members, user_members] = [cache_vals.get(x) for x in cache_keys]
    if group_members is None:
        group_members = models.Member.gql(
                'WHERE group = :1', group
            ).fetch(None)
    group_members = [x for x in group_members if str(x.key()) != member_key]
    if user_members is None:
        user_members = models.Member.gql(
                'WHERE owner = :1', user
            ).fetch(None)
    user_members = [x for x in user_members if str(x.key()) != member_key]
    memcache.set_multi(
        {
            cache_keys[0] :     group_members,
            cache_keys[1] :     user_members
        })


def __update_cached_member(group, member):
    """
    Update a member in the memcache.
    This must be done after each membership modification to ensure that a
    consistent view is presented despite the HRD eventual consistency model.
    """
    group_key = str(group.key())
    member_key = str(member.key())
    cache_keys = [x + '__M' for x in [group_key, member.owner.user_id()]]
    cache_vals = memcache.get_multi(cache_keys)
    [group_members, user_members] = [cache_vals.get(x) for x in cache_keys]
    if group_members is None:
        group_members = models.Member.gql(
                'WHERE group = :1', group
            ).fetch(None)
    group_members = [x for x in group_members if str(x.key()) != member_key]
    group_members.append(member)
    if user_members is None:
        user_members = models.Member.gql(
                'WHERE owner = :1', member
            ).fetch(None)
    user_members = [x for x in user_members if str(x.key()) != member_key]
    user_members.append(member)
    memcache.set_multi(
        {
            cache_keys[0] :     group_members,
            cache_keys[1] :     user_members
        })


def __del_cached_invites(group_key):
    """
    Remove all invitations associated with a group from the memcache.
    """
    memcache.delete(group_key + '__I')


def __del_cached_invite(group, invite_key):
    """
    Remove an invitation from the memcache.
    This must be done when an invitation is deleted to ensure that a consistent
    view is presented despite the HRD eventual consistency model.
    """
    group_key = str(group.key())
    group_invites_key = group_key + '__I'
    invites = memcache.get(group_invites_key)
    if invites is None:
        invites = models.Invitation.gql(
                'WHERE group = :1', group
            ).fetch(None)
    invites = [x for x in invites if str(x.key()) != invite_key]
    memcache.set(group_invites_key, invites, time=app.config.TIME_CACHE_DATA)


def __update_cached_invite(invite):
    """
    Update an invitation in the memcache.
    This must be done after each invitation modification to ensure that a
    consistent view is presented despite the HRD eventual consistency model.
    """
    group = invite.group
    group_key = str(group.key())
    group_invites_key = group_key + '__I'
    invites = memcache.get(group_invites_key)
    if invites is None:
        invites = models.Invitation.gql(
                'WHERE group = :1', group
            ).fetch(None)
    invites = [x for x in invites if str(x.key()) != str(invite.key())]
    invites.append(invite)
    memcache.set(group_invites_key, invites, time=app.config.TIME_CACHE_DATA)


def get_members_and_invites(group_key):
    """
    Retrieve all members and invitations associated with a group.
    """
    group = __get_group_by_key(group_key, check_owner=False)
    cache_keys = [group_key + x for x in ['__M', '__I']]
    cache_vals = memcache.get_multi(cache_keys)
    [members, invites] = [cache_vals.get(x) for x in cache_keys]
    cache_vals.clear()

    if members is None:
        members = models.Member.gql(
                'WHERE group = :1', group
            ).fetch(None)
        cache_vals[cache_keys[0]] = members

    if invites is None:
        invites = models.Invitation.gql(
                'WHERE group = :1', group
            ).fetch(None)
        cache_vals[cache_keys[1]] = invites

    member_lists = []
    for member in members:
        owner = member.owner
        lists = memcache.get(owner.user_id() + '__L')
        if lists is None:
            lists = models.List.gql(
                    'WHERE owner = :1', owner
                ).fetch(None)
            cache_vals[owner.user_id() + '__L'] = lists
        name = settings.get_display_name(owner)
        member_lists.append(dict(member=member, lists=lists, name=name))

    invites_left = app.config.NUM_MEMBERS_MAX - len(member_lists) - len(invites)
    if invites_left < 0:
        invites_left = 0

    if cache_vals:
        memcache.set_multi(cache_vals, time=app.config.TIME_CACHE_DATA)

    results = {
        'group' :           group,
        'title' :           group.title,
        'member_lists' :    member_lists,
        'invites' :         invites,
        'invites_left' :    invites_left,
        'editor' :          users.get_current_user() == group.owner,
    }
    return results


def get_title(group_key):
    """
    Retrieve the title of a group.
    """
    group = __get_group_by_key(group_key, check_owner=False)
    return group.title


def get_from_invitation(invitation_key):
    """
    Retrieve the group associated with an invitation.
    """
    invite = models.Invitation.get(invitation_key)
    if not invite:
        raise errors.QueryError
    group_key = models.Invitation.group.get_value_for_datastore(invite)
    return str(group_key)


def get_from_member(member_key):
    """
    Retrieve the group associated with a member.
    """
    member = models.Member.get(member_key)
    if not member:
        raise errors.QueryError
    group_key = models.Member.group.get_value_for_datastore(member)
    return str(group_key)


def create_group(title, message):
    """
    Create a new group.
    """
    user = users.get_current_user()
    groups = memcache.get(user.user_id() + '__G')
    if groups:
        count = len(groups)
    else:
        count = models.Group.gql(
                'WHERE owner = :1', user
            ).count()
    if count >= app.config.NUM_GROUPS_MAX:
        raise errors.MaxValueError
    group = models.Group(
        owner=user,
        title=util.sanitize(title, trunc=app.config.TEXT_LINE_LENGTH),
        message=util.sanitize(message, trunc=app.config.TEXT_BLOCK_LENGTH))
    group.put()
    __update_cached_group(group)
    try:
        member = models.Member(
            owner=user,
            group=group)
        member.put()
    except:
        raise errors.GroupJoinError
    __update_cached_member(group, member)
    return str(group.key())


def create_invitation(group_key, email, greeting, send, salt):
    """
    Create a new invitation associated with a group.
    """
    group = __get_group_by_key(group_key)
    cache_keys = [group_key + x for x in ['__M', '__I']]
    cache_vals = memcache.get_multi(cache_keys)
    [members, invites] = [cache_vals.get(x) for x in cache_keys]
    if not members is None:
        count = len(members)
    else:
        count = models.Member.gql(
                'WHERE group = :1', group
            ).count()
    if not invites is None:
        count += len(invites)
    else:
        count += models.Invitation.gql(
                'WHERE group = :1', group
            ).count()
    if count >= app.config.NUM_MEMBERS_MAX:
        raise errors.MaxValueError
    email = util.sanitize(email, trunc=80)
    # Reminder:
    # The request parameters are unicode. hashlib.sha1 is expecting a str.
    # Must encode properly for this to work.
    sha1 = hashlib.sha1()
    sha1.update(
        group_key.encode('ascii', 'ignore')
        + email.encode('ascii', 'ignore')
        + str(time.time())
        + salt)
    code = sha1.hexdigest()
    invite = models.Invitation(
        group=group,
        code=code,
        email=email)
    invite.put()
    __update_cached_invite(invite)
    if send:
        from google.appengine.api import mail
        message = mail.EmailMessage()
        message.sender = users.get_current_user().email()
        message.to = email
        message.subject = 'Share your gift wish list at Wiftgish!'
        greeting = util.sanitize(greeting, strict=True, trunc=1000)
        if not greeting:
            greeting = '\n'
        else:
            greeting = '\n' + greeting + '\n'
        domain = app.config.DOMAIN
        if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
            domain = 'localhost:8080'
        message.body = """
Hi!

I'm inviting you to share your gift wish lists with me on Wiftgish. To join my group: '%s', you can use the direct link:

http://%s%s/groups/join/%s

Or, sign in at http://%s and enter the invitation code:

%s
%s
See you there!
""" % (
            cgi.escape(group.title),
            domain,
            app.config.PATH_PREFIX,
            code,
            domain,
            code,
            cgi.escape(greeting))
        message.send()


def create_member(invitation_code):
    """
    Create a new member associated with a group/invitation.
    """
    invitation_code = util.sanitize(invitation_code, strict=True, trunc=40)
    invite = models.Invitation.gql(
            'WHERE code = :1', invitation_code
        ).get()
    if not invite:
        raise errors.GroupJoinError
    group_key = str(models.Invitation.group.get_value_for_datastore(invite))
    user = users.get_current_user()
    # Can't use __get_group_by_key() because it verifies permission that the
    # current user doesn't have yet. As a bonus, this minimizes the number of
    # memcache reads.
    cache_keys = [group_key, user.user_id() + '__M']
    cache_vals = memcache.get_multi(cache_keys)
    [group, memberships] = [cache_vals.get(x) for x in cache_keys]
    cache_vals.clear()
    if group is None:
        group = models.Group.get(group_key)
        if not group:
            raise errors.QueryError
        cache_vals[group_key] = group
    invite_key = str(invite.key())
    invite.delete()
    __del_cached_invite(group, invite_key)
    if memberships is None:
        memberships = models.Member.gql(
                'WHERE owner = :1', user
            ).fetch(None)
        cache_vals[cache_keys[1]] = memberships
    if cache_vals:
        memcache.set_multi(cache_vals, time=app.config.TIME_CACHE_DATA)
    for m in memberships:
        if str(models.Member.group.get_value_for_datastore(m)) == group_key:
            break
    else:
        member = models.Member(
            owner=user,
            group=group)
        member.put()
        __update_cached_member(group, member)
    return group_key


def update_group(group_key, title, message):
    """
    Modify group information.
    """
    group = __get_group_by_key(group_key)
    group.title = util.sanitize(title, trunc=app.config.TEXT_LINE_LENGTH)
    group.message = util.sanitize(message, trunc=app.config.TEXT_BLOCK_LENGTH)
    group.put()
    __update_cached_group(group)
    # TODO: What about cached user's membership lists?


def delete_group(group_key):
    """
    Remove a group and all associated members and invitations.
    """
    group = __get_group_by_key(group_key)
    cache_keys = [group_key + x for x in ['__I', '__M']]
    cache_vals = memcache.get_multi(cache_keys)
    [invites, members] = [cache_vals.get(x) for x in cache_keys]
    if invites is None:
        invites = models.Invitation.gql(
                'WHERE group = :1', group
            ).fetch(None, keys_only=True)
    else:
        invites = [x.key() for x in invites]
    if members is None:
        members = models.Member.gql(
                'WHERE group = :1', group
            ).fetch(None)
    __del_cached_members(members, group_key)
    members = [x.key() for x in members]
    db.delete(invites + members)
    group.delete()
    __del_cached_group(group_key)


def delete_invitation(invitation_key):
    """
    Remove an invitation.
    """
    invite = models.Invitation.get(invitation_key)
    if not invite:
        raise errors.QueryError
    group_key = str(models.Invitation.group.get_value_for_datastore(invite))
    # Check permission for this operation through the group.
    group = __get_group_by_key(group_key)
    invite.delete()
    __del_cached_invite(group, invitation_key)
    return group_key


def delete_member(member_key):
    """
    Remove a member from a group.
    """
    member = models.Member.get(member_key)
    if not member:
        raise errors.QueryError
    user = member.owner
    group_key = str(models.Member.group.get_value_for_datastore(member))
    # Check permission for this operation through the group.
    group = __get_group_by_key(group_key)
    member.delete()
    __del_cached_member(group, user, member_key)
    return group_key


def delete_self(group_key):
    """
    Remove self as a member of a group.
    """
    group = __get_group_by_key(group_key, check_owner=False)
    user = users.get_current_user()
    member_key = models.Member.gql(
            'WHERE owner = :1 and group = :2', user, group
        ).get(keys_only=True)
    if not member_key:
        raise errors.QueryError
    db.delete(member_key)
    __del_cached_member(group, user, str(member_key))

