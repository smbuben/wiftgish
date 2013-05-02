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

import datetime
import jinja2
import re
import urlparse


def short_url(value, path_length=15):
    netloc = urlparse.urlparse(value).netloc
    path = value.split(netloc, 1)[1]
    if len(path) > path_length:
        return netloc + path[:path_length] + '...'
    return netloc + path


def timesince(value, verbose=False):
    diff = datetime.datetime.utcnow() - value
    if verbose:
        bins = [
            (diff.days / 365, 'year'),
            (diff.days / 30, 'month'),
            (diff.days, 'day'),
            (diff.seconds / 3600, 'hour'),
            (diff.seconds / 60, 'minute'),
            (diff.seconds, 'second'),
        ]
        for (amount, period) in bins:
            if amount:
                if amount > 1:
                    period += 's'
                return '%d %s ago' % (amount, period)
        return 'a short time ago'
    else:
        bins = [
            (diff.days / 365, 'y'),
            (diff.days / 30, 'm'),
            (diff.days, 'd'),
        ]
        for (amount, period) in bins:
            if amount:
                return '%d%s' % (amount, period)
        return 'today'


@jinja2.evalcontextfilter
def linebreaks(eval_ctx, value):
    result = u'<br>'.join(re.split(r'(?:\r\n|\r|\n)', jinja2.escape(value)))
    if eval_ctx.autoescape:
        result = jinja2.Markup(result)
    return result


all_filters = {
    'short_url' :   short_url,
    'timesince' :   timesince,
    'linebreaks' :  linebreaks,
}

