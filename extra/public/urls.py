# MRWF - extra/public/public/urls.py
#
# Copyright (C) 2009, 2010, 2011. 2012, 2013
# Guillaume Tucker <guillaume@mangoz.org>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import patterns
from mrwf.extra import public

urlpatterns = patterns('mrwf.extra.public',
 (r'^$', 'home.index'),
 (r'prog/$', 'prog.all_fairs'),
 (r'prog/current/$', 'prog.current'),
 (r'prog/current/(?P<event_id>\d+)/$', 'prog.current_event'),
 (r'prog/current/dump/$', 'prog.current_dump'),
 (r'prog/current/categories/$', 'prog.current_cats'),
 (r'prog/current/search$', 'prog.current_search'),
 (r'prog/(?P<fair_year>\d+)/$', 'prog.fair'),
 (r'prog/(?P<fair_year>\d+)/(?P<event_id>\d+)/$', 'prog.event'),
 (r'prog/(?P<fair_year>\d+)/dump/$', 'prog.dump'),
 (r'prog/(?P<fair_year>\d+)/categories/$', 'prog.cats'),
 (r'prog/(?P<fair_year>\d+)/search$', 'prog.search'),
 (r'apply/$', 'apply.post'),
 (r'apply/stallholder/$', 'apply.stallholder'),
 (r'thank_you/$', 'apply.thank_you')
)
