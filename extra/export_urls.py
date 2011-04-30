from django.conf.urls.defaults import patterns

urlpatterns = patterns ('mrwf.extra.views.export',
 (r'^group/(?P<group_id>\d+)/$', 'group'),
 (r'^group_email/(?P<group_id>\d+)/$', 'group_email'), # Temporary...
 (r'^programme/$', 'programme'),
 (r'^invoices/$', 'invoices'),
)
