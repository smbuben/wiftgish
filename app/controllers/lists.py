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
        self.render('list.html', **template_vals)


class Create(base.RequestHandler):

    def post(self):
        try:
            title = self.request.get('title')
            description = self.request.get('description')
            list_key = app.models.lists.create_list(title, description)
        except app.models.errors.MaxValueError:
            self.flash(
                'You\'ve already created the maximum number of lists.')
        except app.models.errors.BadValueError:
            self.flash(
                'You didn\'t enter something quite right. '
                'Please try again.')
        else:
            return self.go('/lists/' + list_key)
        self.go('/')


class CreateSurvey(base.RequestHandler):

    def post(self):
        try:
            list_key = self.request.get('list')
            item = self.request.get('item')
            category = self.request.get('category')
            app.models.lists.create_survey(list_key, item, category)
        except app.models.errors.MaxValueError:
            self.flash(
                'You\'ve already created the maximum number of survey answers.')
        except app.models.errors.BadValueError:
            self.flash(
                'You didn\'t enter something quite right. '
                'Please try again.')
        else:
            return self.go('/lists/' + list_key + '#surveys')
        self.go('/lists/' + list_key)


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
            self.flash(
                'You\'ve already created the maximum number of  gift suggestions.')
        except app.models.errors.BadValueError:
            self.flash(
                'You didn\'t enter something quite right. '
                'Please try again.')
        else:
            return self.go('/lists/' + list_key + '#gifts')
        self.go('/lists/' + list_key)


class Update(base.RequestHandler):

    def post(self):
        try:
            list_key = self.request.get('list')
            title = self.request.get('title')
            description = self.request.get('description')
            app.models.lists.update_list(list_key, title, description)
        except app.models.errors.BadValueError:
            self.flash(
                'You didn\'t enter something quite right. '
                'Please try again.')
        self.go('/lists/' + list_key)


class UpdateSurvey(base.RequestHandler):

    def get(self, survey_key):
        template_vals = app.models.lists.get_survey(survey_key)
        self.render('survey.html', **template_vals)


    def post(self, survey_key):
        try:
            item = self.request.get('item')
            category = self.request.get('category')
            list_key = app.models.lists.update_survey(survey_key, item, category)
        except app.models.errors.BadValueError:
            self.flash(
                'You didn\'t enter something quite right. '
                'Please try again.')
        else:
            return self.go('/lists/' + list_key + '#surveys')
        self.go('/lists/update/survey/' + survey_key)


class UpdateGift(base.RequestHandler):

    def get(self, gift_key):
        template_vals = app.models.lists.get_gift(gift_key)
        self.render('gift.html', **template_vals)


    def post(self, gift_key):
        try:
            item = self.request.get('item')
            cost = self.request.get('cost')
            link = self.request.get('link')
            stars = self.request.get('stars')
            list_key = app.models.lists.update_gift(gift_key, item, link, cost, stars)
        except app.models.errors.BadValueError:
            self.flash(
                'You didn\'t enter something quite right. '
                'Please try again.')
        else:
            return self.go('/lists/' + list_key + '#gifts')
        self.go('/lists/update/gift/' + gift_key)


class Delete(base.RequestHandler):

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
        self.go('/lists/' + list_key + '#surveys')


class DeleteGift(base.RequestHandler):

    def post(self):
        list_key = self.request.get('list')
        gift_key = self.request.get('gift')
        app.models.lists.delete_gift(gift_key)
        self.go('/lists/' + list_key + '#gifts')


class PurchaseGift(base.RequestHandler):

    def get(self, gift_key):
        list_key = app.models.lists.purchase_gift(gift_key)
        self.go('/lists/' + list_key + '#gifts')


class UnpurchaseGift(base.RequestHandler):

    def get(self, gift_key):
        list_key = app.models.lists.unpurchase_gift(gift_key)
        self.go('/lists/' + list_key + '#gifts')

