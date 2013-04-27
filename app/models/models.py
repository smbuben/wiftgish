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
Implementation of data models and supporting information/functions.
"""

from google.appengine.ext import db
from google.appengine.api import users


Survey_Categories = {
    10  : 'I spend most of my time...',
    20  : 'In my free time I enjoy...',
    30  : 'If I had more free time I would...',
    40  : 'I wear clothes sized...',
    50  : 'I usually wear...',
    60  : 'My favorite things to eat are...',
    70  : 'My favorite restaurants are...',
    80  : 'I most often shop at...',
    90  : 'I enjoy reading...',
    100 : 'I enjoy listening to...',
    110 : 'I enjoy watching...',
    120 : 'The best gift regardless of price would be...',
    130 : 'The best inexpensive gift would be...',
    140 : 'I don\'t want to receive...',
}


#
# Custom Validators
#

def validate_not_empty_string(value):
    """
    Don't accept an empty string.
    """
    if value == '':
        raise db.BadValueError('Empty string')


def validate_category(value):
    """
    Don't accept a category that doesn't exist.
    """
    if not Survey_Categories.has_key(value):
        raise db.BadValueError('Invalid category: %s' % (str(value)))


def validate_stars(value):
    """
    Don't accept a number of stars outside of the range 1 to 5.
    """
    if value < 1 or value > 5:
        raise db.BadValueError('Invalid stars: %s' % (str(value)))


def validate_email(value):
    """
    Don't accept an email address the doesn't match its basic form.
    """
    # This function should not be called often so importing the re module
    # here should be a slight performance benefit.
    import re
    regex = re.compile(r'^[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,4}$')
    if not regex.match(value):
        raise db.BadValueError('Invalid email address %s' % (str(value)))


#
# Data Models
#

class Settings(db.Model):
    """
    A users custom settings.
    Entities are referenced by a key based on the user's ID.
    """
    firstname = db.StringProperty(
        multiline=False,
        indexed=False)
    lastname = db.StringProperty(
        multiline=False,
        indexed=False)


class Group(db.Model):
    """
    A list-sharing group.
    """
    owner = db.UserProperty(
        required=True)
    title = db.StringProperty(
        multiline=False,
        required=True,
        validator=validate_not_empty_string,
        indexed=False)
    message = db.TextProperty()


class Member(db.Model):
    """
    A member of a list-sharing group.
    """
    owner = db.UserProperty(
        required=True)
    group = db.ReferenceProperty(
        Group,
        required=True)


class Invitation(db.Model):
    """
    A pending invitation to a list-sharing group.
    """
    group = db.ReferenceProperty(
        Group,
        required=True)
    code = db.StringProperty(
        multiline=False,
        required=True,
        validator=validate_not_empty_string)
    email = db.EmailProperty(
        required=True,
        validator=validate_email,
        indexed=False)
    timestamp = db.DateTimeProperty(
        auto_now=True,
        required=True,
        indexed=False)


class List(db.Model):
    """
    A wish list.
    """
    owner = db.UserProperty(
        required=True)
    title = db.StringProperty(
        multiline=False,
        required=True,
        validator=validate_not_empty_string,
        indexed=False)
    description = db.TextProperty()
    timestamp = db.DateTimeProperty(
        auto_now=True,
        required=True,
        indexed=False)


class Gift(db.Model):
    """
    A gift suggestion associated with a wish list.
    """
    collection = db.ReferenceProperty(
        List,
        required=True)
    item = db.StringProperty(
        multiline=False,
        required=True,
        validator=validate_not_empty_string,
        indexed=False)
    link = db.LinkProperty(
        indexed=False)
    cost = db.IntegerProperty(
        indexed=False)
    stars = db.IntegerProperty(
        validator=validate_stars,
        indexed=False)
    purchased = db.BooleanProperty(
        default=False,
        indexed=False)
    purchaser = db.UserProperty(
        indexed=False)
    order = db.IntegerProperty(
        indexed=False)
    timestamp = db.DateTimeProperty(
        auto_now_add=True,
        required=True,
        indexed=False)


class Survey(db.Model):
    """
    A survey answer associated with a wish list.
    """
    collection = db.ReferenceProperty(
        List,
        required=True)
    item = db.StringProperty(
        multiline=False,
        validator=validate_not_empty_string,
        indexed=False)
    category = db.IntegerProperty(
        required=True,
        validator=validate_category,
        indexed=False)
    order = db.IntegerProperty(
        indexed=False)
    timestamp = db.DateTimeProperty(
        auto_now_add=True,
        required=True,
        indexed=False)

