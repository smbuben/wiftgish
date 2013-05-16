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
import app.models.errors
import app.models.lists


class Display(base.RequestHandler):

    def get(self, list_key):
        template_vals = app.models.lists.get_surveys_and_gifts(list_key)
        sort = self.request.get('sort', default_value='date')
        # Base sort is by date.
        template_vals['gifts'] = sorted(
            template_vals['gifts'], key=lambda x: x.timestamp, reverse=True)
        # Additional optional sorts.
        if sort == 'name':
            template_vals['gifts'] = sorted(
                template_vals['gifts'], key=lambda x: x.item)
        elif sort == 'cost':
            template_vals['gifts'] = sorted(
                template_vals['gifts'], key=lambda x: x.cost)
        elif sort == 'rating':
            template_vals['gifts'] = sorted(
                template_vals['gifts'], key=lambda x: x.stars, reverse=True)
        template_vals['sort'] = sort
        self.render('list.html', **template_vals)


class Create(base.RequestHandler):

    def post(self):
        try:
            title = self.request.get('title')
            description = self.request.get('description')
            list_key = app.models.lists.create_list(title, description)
        except app.models.errors.MaxValueError:
            alert = 'You\'ve already created the maximum number of lists.'
            self.ajax_fail(alert=alert)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        else:
            self.ajax_success(redirect='/lists/' + list_key)


class CreateSurvey(base.RequestHandler):

    def post(self):
        try:
            list_key = self.request.get('list')
            item = self.request.get('item')
            category = self.request.get('category')
            app.models.lists.create_survey(list_key, item, category)
        except app.models.errors.MaxValueError:
            alert = 'You\'ve already created the maximum number of survey answers.'
            self.ajax_fail(alert=alert)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        else:
            self.ajax_success()


class CreateGift(base.RequestHandler):

    def post(self):
        try:
            list_key = self.request.get('list')
            item = self.request.get('item')
            link = self.request.get('link')
            cost = self.request.get('cost')
            stars = self.request.get('stars')
            app.models.lists.create_gift(list_key, item, link, cost, stars)
        except app.models.errors.MaxValueError:
            alert = 'You\'ve already created the maximum number of gift suggestions.'
            self.ajax_fail(alert=alert)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        else:
            self.ajax_success()


class Update(base.RequestHandler):

    def post(self):
        try:
            list_key = self.request.get('list')
            title = self.request.get('title')
            description = self.request.get('description')
            app.models.lists.update_list(list_key, title, description)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        else:
            self.ajax_success()


class UpdateSurvey(base.RequestHandler):

    def post(self):
        try:
            survey_key = self.request.get('survey')
            item = self.request.get('item')
            category = self.request.get('category')
            app.models.lists.update_survey(survey_key, item, category)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        else:
            self.ajax_success()


class UpdateGift(base.RequestHandler):

    def post(self):
        try:
            gift_key = self.request.get('gift')
            item = self.request.get('item')
            cost = self.request.get('cost')
            link = self.request.get('link')
            stars = self.request.get('stars')
            app.models.lists.update_gift(gift_key, item, link, cost, stars)
        except app.models.errors.BadValueError:
            alert = 'That doesn\'t look right. Check your entry and try again.'
            self.ajax_fail(alert=alert)
        else:
            self.ajax_success()


class Delete(base.RequestHandler):

    def post(self):
        list_key = self.request.get('list')
        app.models.lists.delete_list(list_key)
        self.ajax_success()


class DeleteWithRedirect(base.RequestHandler):

    def post(self):
        list_key = self.request.get('list')
        list_title = app.models.lists.get_title(list_key)
        app.models.lists.delete_list(list_key)
        self.go('/#lists')


class DeleteSurvey(base.RequestHandler):

    def post(self):
        list_key = self.request.get('list')
        survey_key = self.request.get('survey')
        app.models.lists.delete_survey(survey_key)
        self.ajax_success()


class DeleteGift(base.RequestHandler):

    def post(self):
        list_key = self.request.get('list')
        gift_key = self.request.get('gift')
        app.models.lists.delete_gift(gift_key)
        self.ajax_success()


class PurchaseGift(base.RequestHandler):

    def get(self, gift_key):
        app.models.lists.purchase_gift(gift_key)
        self.ajax_success()


class UnpurchaseGift(base.RequestHandler):

    def get(self, gift_key):
        app.models.lists.unpurchase_gift(gift_key)
        self.ajax_success()

