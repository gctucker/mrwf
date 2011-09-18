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
 urlcls(r'^person/(?P<obj_id>\d+)/choose_member/$',
        views.abook.PersonChooseMemberView, name='add_member_person'),
 urlcls(r'^person/(?P<obj_id>\d+)/save_member/$',
        views.abook.PersonSaveMemberView, name='save_member_person'),
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
 urlcls(r'^member/(?P<obj_id>\d+)/edit/$',
        views.abook.MemberEditView, name="edit_member"),
 urlcls(r'^member/(?P<obj_id>\d+)/delete/$',
        views.abook.MemberRemoveView, name='delete_member'),
 urlcls(r'^history/$',
        views.abook.HistoryView, name='history'),
 urlcls(r'^obj_history/(?P<obj_id>\d+)/$',
        views.abook.ObjHistoryView, name='obj_history'),
)
