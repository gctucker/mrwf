from django.conf.urls.defaults import *

urlpatterns = patterns ('extra.public_views',
 (r'^$', 'index'),
 (r'prog/$', 'all_fairs'),
 (r'prog/current/$', 'current'),
 (r'prog/current/(?P<event_id>\d+)/$', 'current_event'),
 (r'prog/current/categories/$', 'current_cats'),
 (r'prog/current/search$', 'current_search'),
 (r'prog/(?P<fair_year>\d+)/$', 'fair'),
 (r'prog/(?P<fair_year>\d+)/(?P<event_id>\d+)/$', 'event'),
 (r'prog/(?P<fair_year>\d+)/categories/$', 'cats'),
 (r'prog/(?P<fair_year>\d+)/search$', 'search')
)
