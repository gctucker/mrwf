from django.conf.urls.defaults import patterns

urlpatterns = patterns ('mrwf.extra.views.main',
 (r'^$', 'search'),
 (r'^person/(?P<person_id>\d+)/$', 'person'),
 (r'^org/(?P<org_id>\d+)/$', 'org'),
)
