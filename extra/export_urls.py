# MRWF - extra/export_urls.py
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

urlpatterns = patterns('mrwf.extra.views.export',
 (r'^group/(?P<group_id>\d+)/$', 'group'),
 (r'^group_email/(?P<group_id>\d+)/$', 'group_email'), # Temporary...
 (r'^programme/$', 'programme'),
 (r'^invoices/$', 'invoices'),
)

urlpatterns += patterns ('mrwf.extra.views.pdfexport',
 (r'^group_org_pdf/(?P<group_id>\d+)/$', 'group_org_pdf'), # Temporary...
)
