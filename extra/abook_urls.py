from django.conf.urls.defaults import patterns, url
from mrwf.extra import views

urlpatterns = patterns('mrwf.extra.views.abook',
 url(r'^$', views.abook.SearchView.as_view(), name='search'),
 url(r'^add/person/$', views.abook.PersonAddView.as_view(),
     name='add_person'),
 url(r'^person/(?P<obj_id>\d+)/$', views.abook.PersonView.as_view(),
     name='person'),
 (r'^person/(?P<obj_id>\d+)/edit/$', views.abook.PersonEditView.as_view()),
 (r'^person/(?P<obj_id>\d+)/disable/$',
  views.abook.PersonDisableView.as_view()),
 (r'^person/(?P<obj_id>\d+)/delete/$',
  views.abook.PersonDeleteView.as_view()),
 url(r'^add/org/$', views.abook.OrgAddView.as_view(),
     name='add_organisation'),
 url(r'^org/(?P<obj_id>\d+)/$', views.abook.OrgView.as_view(),
     name='organisation'),
 (r'^org/(?P<obj_id>\d+)/edit/$', views.abook.OrgEditView.as_view()),
 (r'^org/(?P<obj_id>\d+)/disable/$', views.abook.OrgDisableView.as_view()),
 (r'^org/(?P<obj_id>\d+)/delete/$', views.abook.OrgDeleteView.as_view()),
)
