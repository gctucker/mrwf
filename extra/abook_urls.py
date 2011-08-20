from django.conf.urls.defaults import patterns
from mrwf.extra import views

urlpatterns = patterns('mrwf.extra.views.abook',
 (r'^$', views.abook.SearchView.as_view()),
 (r'^person/(?P<person_id>\d+)/$', views.abook.PersonView.as_view()),
 (r'^org/(?P<org_id>\d+)/$', views.abook.OrgView.as_view()),
 (r'^org/(?P<org_id>\d+)/edit/$', views.abook.OrgEditView.as_view()),
)
