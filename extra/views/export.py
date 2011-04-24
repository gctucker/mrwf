import datetime
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.template import Context
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from cams.libcams import CSVFileResponse, get_time_string, get_obj_address
from cams.models import Record, Contact, Contactable, Member, Group
from mrwf.extra.models import (FairEventType, FairEvent,
                               StallEvent, StallInvoice)
from mrwf.extra.views.mgmt import get_listing_id

@login_required
def group (request, group_id):
    group = get_object_or_404 (Group, pk = group_id)
    contacts = []
    contactables = group.members.filter (status = Record.ACTIVE)

    c_people = contactables.filter (type = Contactable.PERSON)
    c_people = c_people.order_by ('person__last_name')

    for it in c_people:
        org_name = ''
        c = Contact.objects.filter (obj = it)
        if c:
            c = c[0]
            ctype = 'person'
        else:
            member = Member.objects.filter (person = it)
            if member:
                member = member[0]
                org_name = member.organisation.name
                c = Contact.objects.filter (obj = member)
                if c:
                    c = c[0]
                    ctype = 'member'
                else:
                    c = Contact.objects.filter (obj = member.organisation)
                    if c:
                        c = c[0]
                        ctype = 'org'
        if c:
            contacts.append ((it.person, ctype, org_name, c))

    c_orgs = contactables.filter (type = Contactable.ORGANISATION)
    c_orgs = c_orgs.order_by ('organisation__name')

    for it in c_orgs:
        c = Contact.objects.filter (obj = it)
        p = None
        if c:
            c = c[0]
            c_type = 'org'
        else:
            member = Member.objects.filter (organisation = it)
            if member:
                member = member[0]
                c = Contact.objects.filter (obj = member)
                if c:
                    p = member.person
                    c = c[0]
                    c_type = 'member'
                else:
                    c = Contact.objects.filter (obj = member.person)
                    if c:
                        p = member.person
                        c = c[0]
                        c_type = 'person'
        if c:
            contacts.append ((p, c_type, it.organisation.name, c))

    csv = CSVFileResponse (('first_name', 'middle_name', 'last_name',
                            'contact_type', 'organisation',
                            'line_1', 'line_2', 'line_3', 'town', 'postcode',
                            'telephone', 'mobile', 'fax', 'email', 'website',
                            'order', 'sub-order'))

    for it in contacts:
        p = it[0]
        ctype = it[1]
        org_name = it[2]
        c = it[3]

        if p:
            p_first_name = p.first_name
            p_middle_name = p.middle_name
            p_last_name = p.last_name
        else:
            p_first_name = ''
            p_middle_name = ''
            p_last_name = ''

        csv.writerow ((p_first_name, p_middle_name, p_last_name,
                       ctype, org_name,
                       c.line_1, c.line_2, c.line_3, c.town, c.postcode,
                       c.telephone, c.mobile, c.fax, c.email, c.website,
                       str (c.addr_order), str (c.addr_suborder)))

    if group.fair:
        name_year = "%d_" % group.fair.date.year
    else:
        name_year = ''

    csv.set_file_name ('%s-%s%s.csv' % (group.name.replace (' ', '_'),
                                        name_year, get_time_string ()))

    return csv.response

@login_required
def programme (request):
    def istr (value):
        if value:
            return str (value)
        else:
            return ''

    events = FairEvent.objects.filter (status = Record.ACTIVE)
    events = events.filter (fair__current = True)

    listing = get_listing_id (request)
    if listing > 0:
        events = events.filter (etype = listing)
        listing_obj = get_object_or_404 (FairEventType, pk = listing)
        file_name = "Programme_%s" % listing_obj.name.replace (' ', '_')
    elif listing == 0:
        events = events.filter (etype__isnull = True)
        file_name = "Programme_Default"
    else:
        file_name = "Programme"

    if 'fmt' in request.GET:
        fmt = request.GET['fmt']
    else:
        fmt='csv'

    if fmt == 'csv':
        csv = CSVFileResponse (('name', 'description', 'time', 'until',
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

        csv.set_file_name ("%s_%s.csv" % (file_name, get_time_string ()))

        for e in events:
            # ToDo: add subtype field in base FairEvent like Contactable ?
            try:
                stall = StallEvent.objects.get (pk = e.id)
                n_spaces = str (stall.n_spaces)
                n_tables = str (stall.n_tables)
            except StallEvent.DoesNotExist:
                n_spaces = ''
                n_tables = ''

            c = e.get_composite_contact ()

            if e.owner.contact_set.count () > 0:
                owner_c = e.owner.contact_set.all ()[0]
                owner_addr = owner_c.get_address ()
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
                if e.org.contact_set.count () > 0:
                    org_c = e.org.contact_set.all ()[0]
                else:
                    org_c = None
            else:
                org_name = ''
                org_c = None

            if org_c:
                org_addr = org_c.get_address ()
                org_tel = org_c.telephone
                org_mobile = org_c.mobile
                org_email = org_c.email
                org_website = org_c.website
                org_order = istr (org_c.addr_order)
                org_suborder = istr (org_c.addr_suborder)
            else:
                org_addr = ''
                org_tel = ''
                org_mobile = ''
                org_email = ''
                org_website = ''
                org_order = ''
                org_suborder = ''

            csv.writerow ((e.name, e.description,
                           istr (e.time), istr (e.end_time),
                           istr (e.age_min), istr (e.age_max), e.location,
                           istr (c.addr_order), istr (c.addr_suborder),

                           c.get_address (), c.telephone,
                           c.mobile, c.email, c.website,

                           "%s %s" % (e.owner.first_name, e.owner.last_name),
                           owner_addr, owner_tel, owner_mob, owner_email,
                           owner_website,

                           org_name, org_addr, org_tel, org_mobile,
                           org_email, org_website, org_order, org_suborder,

                           n_spaces, n_tables))

        return csv.response
    elif fmt == 'plaintext':
        resp = HttpResponse (mimetype = 'text/plain')
        resp['Content-Disposition'] = \
            'attachement; filename=\"%s_%s.txt\"' % \
            (file_name, get_time_string ())
        t = get_template ("cams/prog_event.txt")
        ctx = Context ({'e': None, 'c': None})

        for e in events:
            ctx['e'] = e
            ctx['c'] = e.get_composite_contact ()
            resp.write (t.render (ctx))

        return resp
    else:
        raise Http404

@login_required
def invoices (request):
    def date_str (datetime):
        if datetime:
            return str (datetime)
        else:
            return ''

    invs = StallInvoice.objects.all ()
    resp = CSVFileResponse (('stall_name', 'owner', 'owner_address',
                             'owner_telephone', 'owner_email', 'organisation',
                             'org_address', 'org_telephone', 'org_email',
                             'tables', 'spaces', 'amount', 'status',
                             'reference', 'created', 'sent', 'paid', 'banked'))

    for i in invs:
        owner_c = Contact.objects.filter (obj = i.stall.owner)
        if owner_c:
            c = owner_c[0]
            owner_address = c.get_address ()
            owner_telephone = c.telephone
            owner_email = c.email
        else:
            owner_address = ''
            owner_telephone = ''
            owner_email = ''

        if i.stall.org:
            org_name = i.stall.org.__unicode__ ()
            org_c = Contact.objects.filter (obj = i.stall.org)
            if org_c:
                org_c = org_c[0]
        else:
            org_name = ''
            org_c = None

        if org_c:
            org_address = org_c.get_address ()
            org_telephone = org_c.telephone
            org_email = org_c.email
        else:
            org_address = ''
            org_telephone = ''
            org_email = ''

        resp.writerow ((i.stall.name, i.stall.owner.__unicode__ (),
                        owner_address, owner_telephone, owner_email, org_name,
                        org_address, org_telephone, org_email,
                        str (i.stall.n_tables), str (i.stall.n_spaces),
                        str (i.amount), i.status_str (), i.reference,
                        date_str (i.created), date_str (i.sent),
                        date_str(i.paid), date_str (i.banked)))

    resp.set_file_name ("Stall_invoices_%s.csv" % get_time_string ())
    return resp.response
