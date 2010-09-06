from django.conf.urls.defaults import *
from mrwf.extra import public

urlpatterns = patterns ('mrwf.extra.public',
 (r'^$', 'home.index'),
 (r'prog/$', 'prog.all_fairs'),
 (r'prog/current/$', 'prog.current'),
 (r'prog/current/(?P<event_id>\d+)/$', 'prog.current_event'),
 (r'prog/current/categories/$', 'prog.current_cats'),
 (r'prog/current/search$', 'prog.current_search'),
 (r'prog/(?P<fair_year>\d+)/$', 'prog.fair'),
 (r'prog/(?P<fair_year>\d+)/(?P<event_id>\d+)/$', 'prog.event'),
 (r'prog/(?P<fair_year>\d+)/categories/$', 'prog.cats'),
 (r'prog/(?P<fair_year>\d+)/search$', 'prog.search'),
 (r'apply/$', 'apply.post'),
 (r'apply/stallholder/$', 'apply.stallholder'),
 (r'application/$', 'apply.application')
)
