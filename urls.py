from django.conf.urls.defaults import patterns, include
from django.contrib import admin
from settings import DEBUG, STATIC_ROOT
from mrwf.extra import views

admin.autodiscover()

urlpatterns = patterns('',
 (r'^$', views.main.HomeView.as_view()),
 (r'^accounts/login/', 'django.contrib.auth.views.login',
  {'template_name': 'login.html'}),
 (r'^accounts/logout/', 'django.contrib.auth.views.logout',
  {'template_name': 'logout.html'}),
 (r'^admin/doc/', include('django.contrib.admindocs.urls')),
 (r'^admin/', include(admin.site.urls)),
 (r'^abook/', include('mrwf.extra.abook_urls')),
 (r'^cams/', include('mrwf.extra.mgmt_urls')),
 (r'^export/', include('mrwf.extra.export_urls')),
 (r'^public/', include('mrwf.extra.public.urls')),
 (r'^profile/$', views.main.ProfileView.as_view()),
 (r'^profile/edit/$', views.main.ProfileEditView.as_view()),
 (r'^profile/password/$', 'mrwf.extra.views.main.password'),
 (r'^profile/email_test/$', 'mrwf.extra.views.main.email_test'),
)

if DEBUG and STATIC_ROOT:
    urlpatterns += patterns ('',
    (r'^static/mrwf/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': STATIC_ROOT}))
