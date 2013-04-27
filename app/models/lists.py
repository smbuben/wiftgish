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
Functions related to managing users' wish lists.
"""

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

import app.config
import errors
import models
import settings
import util

import datetime
import re
import urlparse


def __get_list_by_key(list_key, check_owner=True):
    """
    Retrieve a list entity by its datastore key and verify that the
    accessing user has the appropriate permission for the list.
    """
    wishlist = memcache.get(list_key)
    if wishlist is None:
        wishlist = models.List.get(list_key)
        memcache.set(list_key, wishlist)
        if wishlist is None:
            raise errors.QueryError
    user = users.get_current_user()
    if not user == wishlist.owner:
        if check_owner or not __list_access_allowed(wishlist, user):
            raise errors.PermissionError
    return wishlist


def __list_access_allowed(wishlist, user):
    """
    Verify that a user has permission to view a list by ensuring that the
    users are members of at least one common group.
    """
    cache_keys = [x + '__M' for x in [user.user_id(), wishlist.owner.user_id()]]
    cache_vals = memcache.get_multi(cache_keys)
    [user_members, owner_members] = [cache_vals.get(x) for x in cache_keys]
    cache_vals.clear()
    if not user_members:
        user_members = models.Member.gql(
                'WHERE owner = :1', user
            ).fetch(None)
        cache_vals[cache_keys[0]] = user_members
    if not owner_members:
        owner_members = models.Member.gql(
                'WHERE owner = :1', wishlist.owner
            ).fetch(None)
        cache_vals[cache_keys[1]] = owner_members
    if cache_vals:
        memcache.set_multi(cache_vals, time=app.config.TIME_CACHE_DATA)
    user_groups = [str(models.Member.group.get_value_for_datastore(x))
        for x in user_members]
    owner_groups = [str(models.Member.group.get_value_for_datastore(x))
        for x in owner_members]
    for g in user_groups:
        if g in owner_groups:
            return True
    return False


def __get_survey_by_key(survey_key, check_owner=True):
    """
    Retrieve a survey entity by its datastore key and verify that the
    accessing user has the appropriate permission for the survey.
    """
    survey = models.Survey.get(survey_key)
    list_key = str(models.Survey.collection.get_value_for_datastore(survey))
    survey.collection = __get_list_by_key(list_key, check_owner=check_owner)
    return survey


def __get_gift_by_key(gift_key, check_owner=True):
    """
    Retrieve a gift entity by its datastore key and verify that the
    accessing user has the appropriate permission for the gift.
    """
    gift = models.Gift.get(gift_key)
    list_key = str(models.Gift.collection.get_value_for_datastore(gift))
    gift.collection = __get_list_by_key(list_key, check_owner=check_owner)
    return gift


def __update_list_timestamp(wishlist):
    """
    Touch the given wish list in order to update its timestamp.
    """
    try:
        wishlist.put()
        import datetime
        # The entity's timestamp is updated on a put... in the datastore.
        # Cheat and manually touch the cached list.
        wishlist.timestamp = datetime.datetime.utcnow()
        memcache.set(str(wishlist.key()), wishlist)
    except:
        pass


def __del_cached_list(list_key):
    """
    Remove a user's wishlist from the memcache.
    This must be done when a list is deleted to ensure that a consistent
    view is presented despite the HRD eventual consistency model.

    TODO:
    There is a potential memcache setting race condition between a user's
    modification of their wishlists and a group member's viewing of the lists.
    This should be very unlikely.
    """
    user = users.get_current_user()
    user_lists_key = user.user_id() + '__L'
    lists = memcache.get(user_lists_key)
    if lists is None:
        lists = models.List.gql(
                'WHERE owner = :1', user
            ).fetch(None)
    lists = [x for x in lists if str(x.key()) != list_key]
    memcache.set(user_lists_key, lists, time=app.config.TIME_CACHE_DATA)
    memcache.delete(list_key)


def __update_cached_list(wishlist):
    """
    Update a user's wishlist in the memcache.
    This must be done after each list modification to ensure that a
    consistent view is presented despite the HRD eventual consistency model.

    TODO:
    There is a potential memcache setting race condition between a user's
    modification of their wishlists and a group member's viewing of the lists.
    This should by very unlikely.
    """
    list_key = str(wishlist.key())
    user_lists_key = wishlist.owner.user_id() + '__L'
    lists = memcache.get(user_lists_key)
    if lists is None:
        lists = models.List.gql(
                'WHERE owner = :1', wishlist.owner
            ).fetch(None)
    lists = [x for x in lists if str(x.key()) != list_key]
    lists.append(wishlist)
    memcache.set_multi(
        {
            list_key :          wishlist,
            user_lists_key :    lists
        },
        app.config.TIME_CACHE_DATA)


def __del_cached_surveys(list_key):
    """
    Remove all surveys associated with a wish list from the memcache.
    """
    memcache.delete(list_key + '__S')


def __del_cached_survey(wishlist, survey_key):
    """
    Remove a user's survey answer from the memcache.
    This must be done when a survey is deleted to ensure that a consistent
    view is presented despite the HRD eventual consistency model.

    TODO:
    There is a potential memcache setting race condition between a user's
    modification of their surveys and a group member's viewing of the surveys.
    This should be very unlikely.
    """
    list_key = str(wishlist.key())
    list_surveys_key = list_key + '__S'
    surveys = memcache.get(list_surveys_key)
    if surveys is None:
        surveys = models.Survey.gql(
                'WHERE collection = :1', wishlist
            ).fetch(None)
    surveys = [x for x in surveys if str(x.key()) != survey_key]
    memcache.set(list_surveys_key, surveys, time=app.config.TIME_CACHE_DATA)


def __update_cached_survey(survey):
    """
    Update a user's survey answer in the memcache.
    This must be done after each survey answer modification to ensure that
    a consistent view is presented despite the HRD eventual consistency model.

    TODO:
    There is a potential memcache setting race condition between a user's
    modification of their surveys and a group member's viewing of the surveys.
    This should be very unlikely.
    """
    wishlist = survey.collection
    list_key = str(wishlist.key())
    list_surveys_key = list_key + '__S'
    surveys = memcache.get(list_surveys_key)
    if surveys is None:
        surveys = models.Survey.gql(
                'WHERE collection = :1', wishlist
            ).fetch(None)
    surveys = [x for x in surveys if str(x.key()) != str(survey.key())]
    surveys.append(survey)
    memcache.set(list_surveys_key, surveys, time=app.config.TIME_CACHE_DATA)


def __del_cached_gifts(list_key):
    """
    Remove all gifts associated with a wish list from the memcache.
    """
    memcache.delete(list_key + '__G')


def __del_cached_gift(wishlist, gift_key):
    """
    Remove a user's gift answer from the memcache.
    This must be done when a gift is deleted to ensure that a consistent
    view is presented despite the HRD eventual consistency model.

    TODO:
    There is a potential memcache setting race condition between a user's
    modification of their gifts and a group member's viewing of the gifts.
    This should be very unlikely.
    """
    list_key = str(wishlist.key())
    list_gifts_key = list_key + '__G'
    gifts = memcache.get(list_gifts_key)
    if gifts is None:
        gifts = models.Gift.gql(
                'WHERE collection = :1', wishlist
            ).fetch(None)
    gifts = [x for x in gifts if str(x.key()) != gift_key]
    memcache.set(list_gifts_key, gifts, time=app.config.TIME_CACHE_DATA)


def __update_cached_gift(gift):
    """
    Update a user's gift answer in the memcache.
    This must be done after each gift answer modification to ensure that
    a consistent view is presented despite the HRD eventual consistency model.

    TODO:
    There is a potential memcache setting race condition between a user's
    modification of their gifts and a group member's viewing of the gifts.
    This should be very unlikely.
    """
    wishlist = gift.collection
    list_key = str(wishlist.key())
    list_gifts_key = list_key + '__G'
    gifts = memcache.get(list_gifts_key)
    if gifts is None:
        gifts = models.Gift.gql(
                'WHERE collection = :1', wishlist
            ).fetch(None)
    gifts = [x for x in gifts if str(x.key()) != str(gift.key())]
    gifts.append(gift)
    memcache.set(list_gifts_key, gifts, time=app.config.TIME_CACHE_DATA)


def __format_category(category):
    """
    Format user category input to the stored format.
    """
    # The category is not optional.
    if category == '':
        raise db.BadValueError
    try:
        category = int(category)
    except:
        raise db.BadValueError
    if category == 0:
        raise db.BadValueError
    return category


def __format_link(link):
    """
    Format user link input to the stored format.
    """
    if link == '':
        return None
    if not link.startswith('http://') and not link.startswith('https://'):
        link = 'http://' + link
    link = urlparse.urlparse(link)
    if not re.match(r'^(?:\w[-\w]*(?<=\w)\.)+(?:\w[-\w]*(?<=\w))(?::\d+)?$', link.netloc):
        raise db.BadValueError
    return urlparse.urlunparse(link)


def __format_cost(cost):
    """
    Format user cost input to the stored format.
    """
    if cost == '':
        return None
    if cost.startswith('$'):
        cost = cost[1:]
    try:
        cost = int(round(float(cost)))
    except:
        raise db.BadValueError
    return cost


def __format_stars(stars):
    """
    Format user stars input to the stored format.
    """
    if stars == '':
        return None
    try:
        stars = int(stars)
    except:
        raise db.BadValueError
    if stars == 0:
        raise db.BadValueError
    return stars


def get_surveys_and_gifts(list_key):
    """
    Retrieve all surveys and gifts associated with a wish list.
    """
    wishlist = __get_list_by_key(list_key, check_owner=False)
    cache_keys = [list_key + x for x in ['__S', '__G']]
    cache_vals = memcache.get_multi(cache_keys)
    [surveys, gifts] = [cache_vals.get(x) for x in cache_keys]
    cache_vals.clear()

    if surveys is None:
        surveys = models.Survey.gql(
                'WHERE collection = :1', wishlist
            ).fetch(None)
        cache_vals[cache_keys[0]] = surveys
    surveys_left = app.config.NUM_SURVEYS_MAX - len(surveys)

    if surveys_left < 0:
        surveys_left = 0

    if gifts is None:
        gifts = models.Gift.gql(
                'WHERE collection = :1', wishlist
            ).fetch(None)
        cache_vals[cache_keys[1]] = gifts

    gifts_left = app.config.NUM_GIFTS_MAX - len(gifts)
    if gifts_left < 0:
        gifts_left = 0

    if cache_vals:
        memcache.set_multi(cache_vals, time=app.config.TIME_CACHE_DATA)

    results = {
        'list' :            wishlist,
        'owner' :           settings.get_display_name(wishlist.owner),
        'categories' :      models.Survey_Categories,
        'surveys' :         surveys,
        'surveys_left' :    surveys_left,
        'gifts' :           gifts,
        'gifts_left' :      gifts_left,
        'editor' :          users.get_current_user() == wishlist.owner,
    }
    return results


def get_title(list_key):
    """
    Retrieve the title of a wishlist.
    """
    wishlist = __get_list_by_key(list_key)
    return wishlist.title


def get_survey(survey_key):
    """
    Retrieve a single survey answer.
    """
    survey = __get_survey_by_key(survey_key)
    results = {
        'survey' :          survey,
        'categories' :      models.Survey_Categories,
        'owner' :           settings.get_display_name(survey.collection.owner),
    }
    return results


def get_gift(gift_key):
    """
    Retrieve a single gift suggestion.
    """
    gift = __get_gift_by_key(gift_key)
    results = {
        'gift' :            gift,
        'owner' :           settings.get_display_name(gift.collection.owner),
    }
    return results


def create_list(title, description):
    """
    Create a new wish list.
    """
    user = users.get_current_user()
    lists = memcache.get(user.user_id() + '__L')
    if lists:
        count = len(lists)
    else:
        count = models.Group.gql(
                'WHERE owner = :1', user
            ).count()
    if count >= app.config.NUM_LISTS_MAX:
        raise errors.MaxValueError
    wishlist = models.List(
        owner=user,
        title=util.sanitize(title, trunc=app.config.TEXT_LINE_LENGTH),
        description=util.sanitize(description, trunc=app.config.TEXT_BLOCK_LENGTH))
    wishlist.put()
    __update_cached_list(wishlist)
    list_key = str(wishlist.key())
    return list_key


def create_survey(list_key, item, category):
    """
    Create a new survey answer associated with a wish list.
    """
    wishlist = __get_list_by_key(list_key)
    surveys = memcache.get(list_key + '__S')
    if surveys:
        count = len(surveys)
    else:
        count = models.Survey.gql(
                'WHERE collection = :1', wishlist
            ).count()
    if count >= app.config.NUM_SURVEYS_MAX:
        raise errors.MaxValueError
    survey = models.Survey(
        collection=wishlist,
        item=util.sanitize(item, trunc=app.config.TEXT_LINE_LENGTH),
        category=__format_category(util.sanitize(category, strict=True, trunc=4)))
    survey.put()
    __update_list_timestamp(wishlist)
    __update_cached_survey(survey)
    return list_key


def create_gift(list_key, item, link, cost, stars):
    """
    Create a new gift suggestion associated with a wish list.
    """
    wishlist = __get_list_by_key(list_key)
    gifts = memcache.get(list_key + '__G')
    if gifts:
        count = len(gifts)
    else:
        count = models.Gift.gql(
                'WHERE collection = :1', wishlist
            ).count()
    if count >= app.config.NUM_GIFTS_MAX:
        raise errors.MaxValueError
    gift = models.Gift(
        collection=wishlist,
        item=util.sanitize(item, trunc=app.config.TEXT_LINE_LENGTH),
        link=__format_link(util.sanitize(link, trunc=app.config.TEXT_LINE_LENGTH)),
        cost=__format_cost(util.sanitize(cost, strict=True, trunc=30)),
        stars=__format_stars(util.sanitize(stars, strict=True, trunc=1)))
    gift.put()
    __update_list_timestamp(wishlist)
    __update_cached_gift(gift)
    return list_key


def update_list(list_key, title, description):
    """
    Modify wish list information.
    """
    wishlist = __get_list_by_key(list_key)
    wishlist.title = util.sanitize(title, trunc=app.config.TEXT_LINE_LENGTH)
    wishlist.description = util.sanitize(description, trunc=app.config.TEXT_BLOCK_LENGTH)
    wishlist.put()
    __update_cached_list(wishlist)
    return list_key


def update_survey(survey_key, item, category):
    """
    Modify a survey answer.
    """
    survey = __get_survey_by_key(survey_key)
    survey.item = util.sanitize(item, trunc=app.config.TEXT_LINE_LENGTH)
    survey.category = __format_category(util.sanitize(category, strict=True, trunc=4))
    # Survey timestamp is not auto_now. Update it manually when survey updated.
    survey.timestamp = datetime.datetime.utcnow()
    survey.put()
    __update_list_timestamp(survey.collection)
    __update_cached_survey(survey)
    return str(survey.collection.key())


def update_gift(gift_key, item, link, cost, stars):
    """
    Modify a gift suggestion.
    """
    gift = __get_gift_by_key(gift_key)
    new_item = util.sanitize(item, trunc=app.config.TEXT_LINE_LENGTH)
    # If the gift suggestion item is changing then clear the purchased flag.
    # This is probably the best way to handle this.
    if gift.item != new_item:
        gift.purchased = False
        gift.purchaser = None
        gift.item = new_item
    gift.link = __format_link(util.sanitize(link, trunc=app.config.TEXT_LINE_LENGTH))
    gift.cost = __format_cost(util.sanitize(cost, strict=True, trunc=30))
    gift.stars = __format_stars(util.sanitize(stars, strict=True, trunc=1))
    # Gift timestamp is not auto_now (and don't want this because it would
    # trigger on purchase/unpurchase). Update it manually when gift updated.
    gift.timestamp = datetime.datetime.utcnow()
    gift.put()
    __update_list_timestamp(gift.collection)
    __update_cached_gift(gift)
    return str(gift.collection.key())


def delete_list(list_key):
    """
    Remove a wish list and all associated surveys and gifts.
    """
    wishlist = __get_list_by_key(list_key)
    cache_keys = [list_key + x for x in ['__S', '__G']]
    cache_vals = memcache.get_multi(cache_keys)
    [surveys, gifts] = [cache_vals.get(x) for x in cache_keys]
    if surveys is None:
        surveys = models.Survey.gql(
                'WHERE collection = :1', wishlist
            ).fetch(None, keys_only=True)
    else:
        surveys = [x.key() for x in surveys]
    if gifts is None:
        gifts = models.Gift.gql(
                'WHERE collection = :1', wishlist
            ).fetch(None, keys_only=True)
    else:
        gifts = [x.key() for x in gifts]
    db.delete(surveys + gifts)
    __del_cached_surveys(list_key)
    __del_cached_gifts(list_key)
    wishlist.delete()
    __del_cached_list(list_key)


def delete_survey(survey_key):
    """
    Remove a survey answer from a wish list.
    """
    survey = __get_survey_by_key(survey_key)
    wishlist = survey.collection
    list_key = str(wishlist.key())
    survey.delete()
    __update_list_timestamp(wishlist)
    __del_cached_survey(wishlist, survey_key)


def delete_gift(gift_key):
    """
    Remove a gift suggestion from a wish list.
    """
    gift = __get_gift_by_key(gift_key)
    wishlist = gift.collection
    list_key = str(wishlist.key())
    gift.delete()
    __update_list_timestamp(wishlist)
    __del_cached_gift(wishlist, gift_key)


def purchase_gift(gift_key):
    """
    Mark a gift suggestion as purchased.
    """
    gift = __get_gift_by_key(gift_key, check_owner=False)
    user = users.get_current_user()
    if user != gift.collection.owner and not gift.purchased:
        gift.purchased = True
        gift.purchaser = user
        gift.put()
        __update_cached_gift(gift)
    return str(gift.collection.key())


def unpurchase_gift(gift_key):
    """
    Mark a gift suggestion as not purchased.
    """
    gift = __get_gift_by_key(gift_key, check_owner=False)
    user = users.get_current_user()
    if user != gift.collection.owner and gift.purchased:
        gift.purchased = False
        gift.purchaser = None
        gift.put()
        __update_cached_gift(gift)
    return str(gift.collection.key())

