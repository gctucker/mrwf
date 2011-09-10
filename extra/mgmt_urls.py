from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('mrwf.extra.views.mgmt',
 url(r'^participant/$', 'participants', name='groups'),
 (r'^participant/group/(?P<group_id>\d+)/$', 'group'),
 url(r'^prog/$', 'programme', name='programme'),
 (r'^prog/(?P<event_id>\d+)/$', 'prog_event'),
 (r'^prog/(?P<event_id>\d+)/cmt/$', 'prog_event_cmt'),
 url(r'^application/$', 'applications', name='applications'),
 (r'^application/(?P<type_id>\d+)/$', 'appli_type'),
 url(r'^application/(?P<type_id>\d+)/(?P<appli_id>\d+)/$', 'appli_detail',
     name='appli_detail'),
 url(r'^invoice/$', 'invoices', name='invoices'),
 (r'^invoice/select/$', 'select_invoice'),
 (r'^invoice/add/(?P<stall_id>\d+)/$', 'add_invoice'),
 (r'^invoice/(?P<inv_id>\d+)/$', 'stall_invoice'),
 (r'^invoice/(?P<inv_id>\d+)/edit/$', 'edit_invoice'),
 (r'^invoice/(?P<inv_id>\d+)/hard_copy/$', 'invoice_hard_copy'),
)
