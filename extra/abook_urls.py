# MRWF - extra/abook_urls.py
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

from django.conf.urls.defaults import patterns
from cams.libcams import urlcls
from mrwf.extra import views

urlpatterns = patterns('mrwf.extra.views.abook',
 urlcls(r'^$',
        views.abook.SearchView, name='search'),
 urlcls(r'^browse/new/$',
        views.abook.BrowseNewView, name='browse_new'),
 urlcls(r'^add/person/$',
        views.abook.PersonAddView, name='add_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/$',
        views.abook.PersonView, name='person'),
 urlcls(r'^person/(?P<obj_id>\d+)/edit/$',
        views.abook.PersonEditView, name='edit_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/activate/$',
        views.abook.PersonActivateView, name='activate_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/disable/$',
        views.abook.PersonDisableView, name='disable_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/delete/$',
        views.abook.PersonDeleteView, name='delete_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/choose_merge/$',
        views.abook.PersonChooseMergeView, name='choose_merge_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/merge/(?P<merge_id>\d+)/$',
        views.abook.PersonMergeView, name='merge_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/choose_member/$',
        views.abook.PersonChooseMemberView, name='add_member_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/save_member/$',
        views.abook.PersonSaveMemberView, name='save_member_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/groups/$',
        views.abook.PersonGroupsView, name='groups_person'),
 urlcls(r'^add/org/$',
        views.abook.OrgAddView, name='add_organisation'),
 urlcls(r'^org/(?P<obj_id>\d+)/$',
        views.abook.OrgView, name='organisation'),
 urlcls(r'^org/(?P<obj_id>\d+)/edit/$',
        views.abook.OrgEditView, name='edit_organisation'),
 urlcls(r'^org/(?P<obj_id>\d+)/activate/$',
        views.abook.OrgActivateView, name='activate_organisation'),
 urlcls(r'^org/(?P<obj_id>\d+)/disable/$',
        views.abook.OrgDisableView, name='disable_organisation'),
 urlcls(r'^org/(?P<obj_id>\d+)/delete/$',
        views.abook.OrgDeleteView, name='delete_organisation'),
 urlcls(r'^org/(?P<obj_id>\d+)/choose_member/$',
        views.abook.OrgChooseMemberView,name='add_member_organisation'),
 urlcls(r'^org/(?P<obj_id>\d+)/save_member/$',
        views.abook.OrgSaveMemberView,name='save_member_organisation'),
 urlcls(r'^org/(?P<obj_id>\d+)/groups/$',
        views.abook.OrgGroupsView, name='groups_organisation'),
 urlcls(r'^member/(?P<obj_id>\d+)/edit/$',
        views.abook.MemberEditView, name="edit_member"),
 urlcls(r'^member/(?P<obj_id>\d+)/delete/$',
        views.abook.MemberRemoveView, name='delete_member'),
 urlcls(r'^history/$',
        views.abook.HistoryView, name='history'),
 urlcls(r'^obj_history/(?P<obj_id>\d+)/$',
        views.abook.ObjHistoryView, name='obj_history'),
)
