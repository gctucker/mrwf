from django.conf.urls.defaults import *
from django.contrib import admin
from settings import DEBUG, STATIC_ROOT
from mrwf import extra
from mrwf.extra import views
from mrwf.extra import cams_urls
from mrwf.extra import abook_urls
from mrwf.extra.public import urls

admin.autodiscover()

urlpatterns = patterns ('',
 (r'^$', 'mrwf.extra.views.home'),
 (r'^accounts/login/', 'django.contrib.auth.views.login',
  {'template_name': 'login.html'}),
 (r'^accounts/logout/', 'django.contrib.auth.views.logout',
  {'template_name': 'logout.html'}),
 (r'^admin/doc/', include('django.contrib.admindocs.urls')),
 (r'^admin/', include (admin.site.urls)),
 (r'^abook/', include (extra.abook_urls)),
 (r'^public/', include (extra.public.urls)),
 (r'^cams/', include (extra.cams_urls)),
 (r'^profile/$', 'mrwf.extra.views.profile'),
 (r'^profile/edit/$', 'mrwf.extra.views.profile_edit'),
 (r'^profile/edit/password/$', 'mrwf.extra.views.password'),
 (r'^profile/email_test/$', 'mrwf.extra.views.email_test')
)

if DEBUG and STATIC_ROOT:
    urlpatterns += patterns ('',
    (r'^static/mrwf/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': STATIC_ROOT}))
