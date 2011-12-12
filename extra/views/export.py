import datetime
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.template import Context
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from cams.libcams import CSVFileResponse, get_time_string, make_group_file_name
from cams.models import Record, Contact, Contactable, Member, Group, Fair
from cams.contacts import iterate_group_contacts
from mrwf.extra.models import (FairEventType, FairEvent,
                               StallEvent, StallInvoice)
from mrwf.extra.views.mgmt import get_listing_id, get_stall_invoice_address

@login_required
def group(request, group_id):
    group = get_object_or_404(Group, pk = group_id)
    csv = CSVFileResponse(('first_name', 'middle_name', 'last_name',
                           'contact_type', 'organisation',
                           'line_1', 'line_2', 'line_3', 'town', 'postcode',
                           'telephone', 'mobile', 'fax', 'email', 'website',
                           'order', 'sub-order'))

    for it in iterate_group_contacts(group):
        if it.p:
            p_first_name = it.p.first_name
            p_middle_name = it.p.middle_name
            p_last_name = it.p.last_name
        else:
            p_first_name = ''
            p_middle_name = ''
            p_last_name = ''

        csv.write((p_first_name, p_middle_name, p_last_name,
                   it.ctype, it.org_name,
                   it.c.line_1, it.c.line_2, it.c.line_3, it.c.town,
                   it.c.postcode, it.c.telephone, it.c.mobile, it.c.fax,
                   it.c.email, it.c.website,
                   str(it.c.addr_order), str(it.c.addr_suborder)))

    csv.set_file_name(make_group_file_name(group) + '.csv')
    return csv.response

@login_required
def group_email(request, group_id):
    group = get_object_or_404(Group, pk = group_id)
    emails = []
    for it in iterate_group_contacts(group):
        if it.c.email and it.c.email not in emails:
            emails.append(it.c.email)
    emails.sort()
    resp = HttpResponse(mimetype = 'text/plain')
    resp['Content-Disposition'] = 'attachement; filename=\"{0}\"'.format \
        (make_group_file_name(group, '-email') + '.txt')
    n_emails = len(emails)
    range_step = 50
    for i, range_start in enumerate(range(0, n_emails, range_step)):
        range_stop = range_start + range_step
        resp.write('Chunk {:d}\n'.format(i))
        chunk_str = ''
        for e in emails[range_start:range_stop]:
            chunk_str += ('<' + e + '>, ')
        resp.write(chunk_str.rstrip(', ') + '\n\n')
    return resp

@login_required
def programme(request):
    def istr(value):
        if value:
            return str(value)
        else:
            return ''

    events = FairEvent.objects.filter(status = Record.ACTIVE)
    events = events.filter(fair__current = True)

    listing = get_listing_id(request)
    if listing > 0:
        events = events.filter(etype = listing)
        listing_obj = get_object_or_404(FairEventType, pk = listing)
        file_name = u'Programme_{0}'.format(listing_obj.name.replace(' ', '_'))
    elif listing == 0:
        events = events.filter(etype__isnull = True)
        file_name = u'Programme_Default'
    else:
        file_name = u'Programme'

    if 'fmt' in request.GET:
        fmt = request.GET['fmt']
    else:
        fmt='csv'

    if fmt == 'csv':
        csv = CSVFileResponse(('name', 'description', 'time', 'until',
                               'age min', 'age max', 'location',
                               'order', 'suborder',

                               'event address', 'event telephone',
                               'event mobile', 'event email', 'event website',

                               'owner', 'owner address', 'owner telephone',
                               'owner mobile', 'owner email', 'owner website',

                               'organisation', 'org address', 'org telephone',
                               'org mobile', 'org email', 'org website',
                               'org order', 'org sub-order',

                               'n. spaces', 'n. tables'))

        csv.set_file_name(u'{0}_{1}.csv'.format(file_name, get_time_string()))

        for e in events:
            # ToDo: add subtype field in base FairEvent like Contactable ?
            try:
                stall = StallEvent.objects.get(pk = e.id)
                n_spaces = str(stall.n_spaces)
                n_tables = str(stall.n_tables)
            except StallEvent.DoesNotExist:
                n_spaces = ''
                n_tables = ''

            c = e.get_composite_contact()

            if e.owner.contact_set.count() > 0:
                owner_c = e.owner.contact_set.all()[0]
                owner_addr = owner_c.get_address()
                owner_tel = owner_c.telephone
                owner_mob = owner_c.mobile
                owner_email = owner_c.email
                owner_website = owner_c.website
            # ToDo: use 'empty' contact object
            else:
                owner_addr = ''
                owner_tel = ''
                owner_mob = ''
                owner_email = ''
                owner_website = ''

            if e.org:
                org_name = e.org.name
                if e.org.contact_set.count() > 0:
                    org_c = e.org.contact_set.all()[0]
                else:
                    org_c = None
            else:
                org_name = ''
                org_c = None

            if org_c:
                org_addr = org_c.get_address()
                org_tel = org_c.telephone
                org_mobile = org_c.mobile
                org_email = org_c.email
                org_website = org_c.website
                org_order = istr(org_c.addr_order)
                org_suborder = istr(org_c.addr_suborder)
            else:
                org_addr = ''
                org_tel = ''
                org_mobile = ''
                org_email = ''
                org_website = ''
                org_order = ''
                org_suborder = ''

            csv.write((e.name, e.description,
                       istr(e.time), istr(e.end_time),
                       istr(e.age_min), istr(e.age_max), e.location,
                       istr(c.addr_order), istr(c.addr_suborder),

                       c.get_address(), c.telephone,
                       c.mobile, c.email, c.website,

                       u'{0} {1}'.format(e.owner.first_name,e.owner.last_name),
                       owner_addr, owner_tel, owner_mob, owner_email,
                       owner_website,

                       org_name, org_addr, org_tel, org_mobile,
                       org_email, org_website, org_order, org_suborder,

                       n_spaces, n_tables))

        return csv.response
    elif fmt == 'plaintext':
        resp = HttpResponse(mimetype = 'text/plain')
        resp['Content-Disposition'] = \
            u'attachement; filename=\"{0}_{1}.txt\"'.format \
            (file_name, get_time_string())
        t = get_template("cams/prog_event.txt")
        ctx = Context({'e': None, 'c': None})

        for e in events:
            ctx['e'] = e
            ctx['c'] = e.get_composite_contact()
            resp.write(t.render(ctx))

        return resp
    else:
        raise Http404

@login_required
def invoices(request):
    def date_str(datetime):
        if datetime:
            return str(datetime.date())
        else:
            return ''

    invs = StallInvoice.objects.filter(stall__event__fair=Fair.get_current())
    resp = CSVFileResponse(('stall_name', 'reference', 'owner', 'email',
                            'organisation', 'email', 'invoice address',
                            'tables', 'spaces', 'amount', 'status', 'created',
                            'sent', 'paid', 'cancelled'))
    for i in invs:
        if i.stall.org:
            org_name = i.stall.org.__unicode__()
        else:
            org_name = ''
        address = get_stall_invoice_address(i, u', ')
        c = i.stall.owner.contact
        if not c or not c.email:
            c = i.stall.invoice_contact
        if not c or not c.email and i.stall.org:
            c = i.stall.org.contact
            if not c or not c.email:
                m = i.stall.owner.members_list.filter(organisation=i.stall.org)
                if len(m):
                    c = m[0].contact
        if c:
            email = c.email
        else:
            email = ''
        resp.write((i.stall.name, i.reference, i.stall.owner.__unicode__(),
                    email, org_name, address, str(i.stall.n_tables),
                    str(i.stall.n_spaces), str(i.amount), i.status_str,
                    date_str(i.created), date_str(i.sent), date_str(i.paid),
                    date_str(i.cancelled)))
    resp.set_file_name(u'Stall_invoices_{0}.csv'.format(get_time_string()))
    return resp.response
