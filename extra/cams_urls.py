from django.conf.urls.defaults import *
from mrwf import extra
from mrwf.extra import views

urlpatterns = patterns ('mrwf.extra.views',
 (r'^participant/$', 'participants'),
# (r'^participant/(?P<part_id>\d+)/$', 'part_details'),
 (r'^participant/group/(?P<group_id>\d+)/$', 'group'),
 (r'^participant/group/(?P<group_id>\d+)/export/$', 'export_group'),
 (r'^prep/$', 'preparation'),
 (r'^prep/(?P<event_id>\d+)/$', 'prep_event'),
 (r'^prep/(?P<event_id>\d+)/cmt/$', 'prep_event_cmt'),
 (r'^prog/$', 'programme'),
 (r'^prog/(?P<event_id>\d+)/$', 'prog_event'),
 (r'^prog/(?P<event_id>\d+)/cmt/$', 'prog_event_cmt'),
 (r'^application/$', 'applications'),
 (r'^application/(?P<type_id>\d+)/$', 'appli_type'),
 (r'^application/(?P<type_id>\d+)/(?P<appli_id>\d+)/$', 'appli_detail'),
 (r'^fair/$', 'fairs'),
)
