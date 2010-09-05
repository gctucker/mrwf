from django.conf.urls.defaults import *
from django.contrib import admin
from settings import DEBUG, STATIC_ROOT
#from cams import abook, mgmt
#from cams.abook import urls
#from cams.mgmt import urls, public_urls

admin.autodiscover()

urlpatterns = patterns ('',
# (r'^$', 'cams.mgmt.views.home'),
 (r'^accounts/login/', 'django.contrib.auth.views.login',
  {'template_name': 'login.html'}),
 (r'^accounts/logout/', 'django.contrib.auth.views.logout',
  {'template_name': 'logout.html'}),
 (r'^admin/doc/', include('django.contrib.admindocs.urls')),
 (r'^admin/', include (admin.site.urls))#,
# (r'^abook/', include (abook.urls)),
# (r'^public/', include (mgmt.public_urls)),
# (r'^cams/', include (mgmt.urls)),
# (r'^profile/$', 'cams.mgmt.views.profile')
)

if DEBUG and STATIC_ROOT:
    urlpatterns += patterns ('',
    (r'^static/mrwf/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': STATIC_ROOT}))
