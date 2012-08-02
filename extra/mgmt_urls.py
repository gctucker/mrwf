from django.conf.urls.defaults import patterns, url
from cams.libcams import urlcls
from mrwf.extra import views

urlpatterns = patterns('mrwf.extra.views.mgmt',
 url(r'^participant/$', 'participants', name='groups'),
 url(r'^participant/(?P<board_id>\d+)/$', 'participants', name='groups'),
 url(r'^participant/group/(?P<group_id>\d+)/$', 'group', name='group'),
 url(r'^participant/group/(?P<group_id>\d+)/(?P<board_id>\d+)/$', 'group', name='group'),
 url(r'^prog/$', 'programme', name='programme'),
 (r'^prog/(?P<event_id>\d+)/$', 'prog_event'),
 (r'^prog/(?P<event_id>\d+)/cmt/$', 'prog_event_cmt'),
 url(r'^application/$', 'applications', name='applications'),
 (r'^application/(?P<type_id>\d+)/$', 'appli_type'),
 url(r'^application/(?P<type_id>\d+)/(?P<appli_id>\d+)/$', 'appli_detail',
     name='appli_detail'),
 urlcls(r'^invoice/$',
        views.mgmt.InvoicesView, name='invoices'),
 urlcls(r'^invoice/select/$',
        views.mgmt.SelectInvoiceView, name='select_invoice'),
 urlcls(r'^invoice/add/(?P<stall_id>\d+)/$',
        views.mgmt.AddInvoiceView, name='add_invoice'),
 urlcls(r'^invoice/(?P<inv_id>\d+)/$',
        views.mgmt.StallInvoiceView, name='stall_invoice'),
 urlcls(r'^invoice/(?P<inv_id>\d+)/edit/$',
        views.mgmt.EditInvoiceView, name='edit_invoice'),
 urlcls(r'^invoice/(?P<inv_id>\d+)/hard_copy/$',
        views.mgmt.InvoiceHardCopyView, name='invoice_hard_copy'),
)
