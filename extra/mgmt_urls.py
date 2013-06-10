# MRWF - extra/mgmt_urls.py
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

from django.conf.urls.defaults import patterns, url
from cams.libcams import urlcls
from mrwf.extra import views

urlpatterns = patterns('mrwf.extra.views.mgmt',
 url(r'^participant/$', 'participants', name='groups'),
 url(r'^participant/(?P<board_id>\d+)/$', 'participants', name='groups'),
 url(r'^participant/group/(?P<group_id>\d+)/$', 'group', name='group'),
 url(r'^participant/group/pindown/(?P<group_id>\d+)/$', 'pindown_group',
     name='pindown_group'),
 url(r'^prog/$', 'programme', name='programme'),
 (r'^prog/(?P<event_id>\d+)/$', 'prog_event'),
 (r'^prog/(?P<event_id>\d+)/cmt/$', 'prog_event_cmt'),
 url(r'^application/$', 'applications', name='applications'),
 url(r'^application/(?P<type_id>\d+)/$', 'appli_type', name='appli_type'),
 url(r'^application/(?P<type_id>\d+)/(?P<appli_id>\d+)/$', 'appli_detail',
     name='appli_detail'),
 urlcls(r'^invoice/$',
        views.mgmt.InvoicesView, name='invoices'),
 urlcls(r'^invoice/select/$',
        views.mgmt.SelectInvoiceView, name='select_invoice'),
 urlcls(r'^invoice/add/(?P<stall_id>\d+)/$',
        views.mgmt.AddInvoiceView, name='add_invoice'),
 urlcls(r'^invoice/(?P<inv_id>\d+)/$',
        views.mgmt.StallInvoiceView, name='stall_invoice'),
 urlcls(r'^invoice/(?P<inv_id>\d+)/edit/$',
        views.mgmt.EditInvoiceView, name='edit_invoice'),
 urlcls(r'^invoice/(?P<inv_id>\d+)/hard_copy/$',
        views.mgmt.InvoiceHardCopyView, name='invoice_hard_copy'),
)
