from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from settings import DEBUG, STATIC_ROOT
from cams.libcams import urlcls
from mrwf.extra import views

admin.autodiscover()

urlpatterns = patterns('',
 urlcls(r'^$', views.main.HomeView, name='home'),
 (r'^accounts/login/', 'django.contrib.auth.views.login',
  {'template_name': 'login.html'}),
 url(r'^accounts/logout/', 'django.contrib.auth.views.logout',
  {'template_name': 'logout.html'}, name='logout'),
 (r'^admin/doc/', include('django.contrib.admindocs.urls')),
 (r'^admin/', include(admin.site.urls)),
 (r'^abook/', include('mrwf.extra.abook_urls', namespace='abook')),
 (r'^cams/', include('mrwf.extra.mgmt_urls')),
 (r'^export/', include('mrwf.extra.export_urls')),
 (r'^public/', include('mrwf.extra.public.urls')),
 urlcls(r'^profile/$', views.main.ProfileView, name='profile'),
 urlcls(r'^profile/edit/$', views.main.ProfileEditView, name='edit_profile'),
 urlcls(r'^profile/password/$', views.main.PasswordEditView, name='password'),
 urlcls(r'^profile/email_test/$', views.main.EmailTestView, name='email_test'),
)

if DEBUG and STATIC_ROOT:
    urlpatterns += patterns ('',
    (r'^static/mrwf/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': STATIC_ROOT}))
