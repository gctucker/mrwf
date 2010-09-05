from django.conf.urls.defaults import *

urlpatterns = patterns ('mrwf.extra.views',
 (r'^$', 'search'),
 (r'^person/(?P<person_id>\d+)/$', 'person'),
 (r'^org/(?P<org_id>\d+)/$', 'org'),
)
