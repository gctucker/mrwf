from django.conf.urls.defaults import patterns

urlpatterns = patterns ('mrwf.extra.views.export',
 (r'^group/(?P<group_id>\d+)/$', 'group'),
 (r'^programme/$', 'programme'),
 (r'^invoices/$', 'invoices'),
)
