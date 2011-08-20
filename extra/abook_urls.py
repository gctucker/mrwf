from django.conf.urls.defaults import patterns, url
from mrwf.extra import views

urlpatterns = patterns('mrwf.extra.views.abook',
 url(r'^$', views.abook.SearchView.as_view(), name='abook_search'),
 url(r'^person/(?P<person_id>\d+)/$', views.abook.PersonView.as_view(),
     name='person'),
 (r'^person/(?P<person_id>\d+)/edit/$', views.abook.PersonEditView.as_view()),
 (r'^person/(?P<person_id>\d+)/delete/$',
  views.abook.PersonDeleteView.as_view()),
 url(r'^org/(?P<org_id>\d+)/$', views.abook.OrgView.as_view(), name='org'),
 (r'^org/(?P<org_id>\d+)/edit/$', views.abook.OrgEditView.as_view()),
 (r'^org/(?P<org_id>\d+)/delete/$', views.abook.OrgDeleteView.as_view()),
)
