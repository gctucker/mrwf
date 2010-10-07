import datetime
from django import forms
from django.core.urlresolvers import reverse
from django.http import (HttpResponseForbidden, HttpResponseRedirect,
                         Http404, HttpResponseServerError)
from django.template import RequestContext
from django.db.models.query import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from mrwf.extra.views.main import add_common_tpl_vars
from cams.libcams import str2list, CSVFileResponse
from cams.models import (Record, Player, Fair, Contact, Group, Actor, Role,
                         Event, EventComment, Application, Invoice)
from mrwf.extra.models import (FairEventType, FairEvent, StallEvent,
                               FairEventApplication, StallInvoice)

class CommentForm (forms.Form):
    attrs = {'cols': '80', 'rows': '5'}
    content = forms.CharField (widget = forms.Textarea (attrs = attrs))


def get_comments (ev):
    comments = EventComment.objects.filter (event = ev)
    comments = comments.order_by ('-created')
    return comments

def get_form_if_actor (request, event_id):
    if request.user.is_staff:
        return CommentForm ()

    player = get_object_or_404 (Player, user = request.user)
    ev = get_object_or_404 (Event, pk = event_id)

    try:
        actor = Actor.objects.get (person = player.person, event = ev)
        form = CommentForm ()
    except Actor.DoesNotExist:
        form = None

    return form

def get_show_all (request):
    if request.user.is_staff:
        if 'show_all' in request.GET:
            show_all = (request.GET['show_all'] == 'True')
            request.session['show_all'] = str (show_all)
        elif 'show_all' in request.session:
            show_all = (request.session['show_all'] == 'True')
        else:
            show_all = False
    else:
        show_all = False

    return show_all

def get_listing_id (request):
    if 'listing' in request.GET:
        listing = request.GET['listing']
        request.session['listing'] = listing
    elif 'listing' in request.session:
        listing = request.session['listing']
    else:
        listing = None

    if not listing:
        listing_id = -1
    elif listing == "_default":
        listing_id = 0
    else:
        try:
            listing_id = int (listing)
        except ValueError:
            listing_id = -1

    return listing_id

# -----------------------------------------------------------------------------
# entry points from url's

@login_required
def participants (request):
    groups = Group.objects.all ()
    fair = get_object_or_404 (Fair, current = True)
    groups = groups.filter (Q (fair = fair) | Q (fair__isnull = True))
    tpl_vars = {'page_title': 'Participants', 'url': 'cams/participant/'}
    add_common_tpl_vars (request, tpl_vars, 'parts', groups)
    return render_to_response ('cams/participants.html', tpl_vars)

@login_required
def group (request, group_id):
    group = get_object_or_404 (Group, pk = group_id)
    roles = Role.objects.filter (group = group)
    roles = roles.order_by ('person__last_name')
    tpl_vars = {'page_title': 'Group members', 'group': group,
                'url': 'cams/participant/group/%d/' % group.id}
    add_common_tpl_vars (request, tpl_vars, 'parts', roles)
    return render_to_response ('cams/group.html', tpl_vars)

@login_required
def post_event_cmt (request, event_id, view):
    if request.method != 'POST':
        return HttpResponseServerError ("%s instead of POST" % request.method,
                                        mimetype = 'text/plain')

    form = CommentForm (request.POST)
    if not form.is_valid ():
        return HttpResponseServerError ("form not valid",
                                        mimetype = 'text/plain')

    ev = get_object_or_404 (Event, pk = event_id)
    player = get_object_or_404 (Player, user = request.user)
    if not request.user.is_staff:
        try:
            actor = Actor.objects.get (person = player.person, event = ev)
        except Actor.DoesNotExist:
            return HttpResponseForbidden ("you are not allowed to post here",
                                          mimetype = 'text/plain')

    cmt = EventComment (author = player, event = ev,
                        text = form.cleaned_data['content'])
    cmt.save ()
    return HttpResponseRedirect (reverse (view, args = [event_id]))

@login_required
def preparation (request):
    show_all = get_show_all (request)

    if show_all:
        acts = Event.objects.all ()
        acts = acts.order_by ('date', 'time')
        tpl = 'cams/prep_all.html'
    else:
        player = get_object_or_404 (Player, user = request.user)
        acts = Actor.objects.filter (person = player.person)
        acts = acts.order_by ('event__date', 'event__time')
        tpl = 'cams/preparation.html'

    # ToDo: filter past events and add option to see them
    tpl_vars = {'page_title': 'Preparation', 'url': 'cams/prep/',
                'show_all': show_all}
    add_common_tpl_vars (request, tpl_vars, 'prep', acts)
    return render_to_response (tpl, tpl_vars)

@login_required
def prep_event (request, event_id):
    ev = get_object_or_404 (Event, pk = event_id)
    form = get_form_if_actor (request, event_id)
    tpl_vars = {'page_title': 'Event', 'ev': ev, 'form': form,
                'url': 'cams/prep/%d/' % ev.id}
    add_common_tpl_vars (request, tpl_vars, 'prep', get_comments (ev), 4)
    return render_to_response ('cams/prep_event.html', tpl_vars,
                               context_instance = RequestContext (request),)

@login_required
def prep_event_cmt (request, event_id):
    return post_event_cmt (request, event_id, prep_event)

@login_required
def programme (request):
    class SearchForm (forms.Form):
        match = forms.CharField (required = True, max_length = 64)

    fair = get_object_or_404 (Fair, current = True)
    prog = FairEvent.objects.filter (fair = fair)

    if not request.user.is_staff:
        prog = prog.filter (status = Record.ACTIVE)

    search_form = SearchForm (request.GET)
    if search_form.is_valid ():
        match = search_form.cleaned_data['match']
        #request.session['match'] = match
    elif 'match' in request.session:
        #match = request.session['match']
        #search_form = SearchForm (initial = {'match': match})
        match = ''
    else:
        match = ''

    for w in str2list (match):
        prog = prog.filter (Q (name__icontains = w)
                            | Q (org__name__icontains = w))

    listing = get_listing_id (request)
    if listing > 0:
        if FairEventType.objects.filter (pk = listing).exists ():
            prog = prog.filter (etype = listing)
        else:
            listing = -1
    elif listing == 0:
        prog = prog.filter (etype__isnull = True)

    # ToDo: order events by 'order' and 'sub-order'

    listings = FairEventType.objects.all ()
    listings = listings.values ('id', 'name')

    tpl_vars = {'page_title': 'Programme', 'url': 'cams/prog/',
                'listings': listings, 'current': listing,
                'search_form': search_form}
    add_common_tpl_vars (request, tpl_vars, 'prog', prog)
    return render_to_response ('cams/programme.html', tpl_vars)

@login_required
def prog_event (request, event_id):
    ev = get_object_or_404 (FairEvent, pk = event_id)
    if (not request.user.is_staff) and (ev.status != Record.ACTIVE):
        raise Http404
    form = get_form_if_actor (request, event_id)

    if StallEvent.objects.filter (pk = event_id).exists ():
        admin_type = 'stallevent'
    else:
        admin_type = 'fairevent'

    tpl_vars = {'page_title': 'Fair Event', 'ev': ev, 'form': form,
                'url': 'cams/prog/%d/' % ev.id, 'admin_type': admin_type}
    add_common_tpl_vars (request, tpl_vars, 'prog', get_comments (ev), 4)
    return render_to_response ('cams/prog_event.html', tpl_vars,
                               context_instance = RequestContext (request))

@login_required
def prog_event_cmt (request, event_id):
    return post_event_cmt (request, event_id, prog_event)

@login_required
def applications (request):
    applis = FairEventApplication.objects.all ()
    cats = []
    for cat_id, cat_name in FairEventApplication.xtypes:
        cat_type = {'id': cat_id, 'name': cat_name}
        applis = FairEventApplication.objects.filter (subtype = cat_id)
        pending = applis.filter (status = Application.PENDING)
        accepted = applis.filter (status = Application.ACCEPTED)
        rejected = applis.filter (status = Application.REJECTED)
        stats = {'pending': pending.count (), 'accepted': accepted.count (),
                 'rejected': rejected.count (), 'total': applis.count ()}
        cats.append ((cat_type, stats))
    tpl_vars = {'page_title': 'Applications', 'cats': cats}
    add_common_tpl_vars (request, tpl_vars, 'appli')
    return render_to_response ('cams/applications.html', tpl_vars)

@login_required
def appli_type (request, type_id):
    type_id = int (type_id)
    applis = FairEventApplication.objects.filter (subtype = type_id)
    applis = applis.order_by ('-created')
    type_name = FairEventApplication.xtypes[type_id][1]
    tpl_vars = {'page_title': 'Applications: %ss' % type_name,
                'url': 'cams/application/%d/' % type_id,
                'applis': applis, 'type_id': type_id}
    add_common_tpl_vars (request, tpl_vars, 'appli', applis, 10)
    template = "cams/appli_list.html"
    return render_to_response (template, tpl_vars)

@login_required
def appli_detail (request, type_id, appli_id):
    type_id = int (type_id)
    appli_id = int (appli_id)
    appli = get_object_or_404 (FairEventApplication, pk = appli_id)

    if 'action' in request.GET:
        action = request.GET['action']
        if action == 'accept':
            appli.status = Application.ACCEPTED
            appli.save ()
        elif action == 'reject':
            appli.status = Application.REJECTED
            appli.save ()
        else:
            raise Http404

    if appli.subtype != type_id:
        raise Http404

    if type_id == FairEventApplication.STALLHOLDER:
        detail = get_object_or_404 (StallEvent, pk = appli.event.id)
    else:
        detail = None

    tpl_vars = {'page_title': 'Application', 'type_id': type_id,
                'appli': appli, 'detail': detail}
    add_common_tpl_vars (request, tpl_vars, 'appli')
    type_name = FairEventApplication.xtypes[type_id][1]
    template = "cams/appli_%s.html" % type_name
    return render_to_response (template, tpl_vars)

@login_required
def invoices (request):
    filters = ('All', 'Pending', 'Banked')
    if 'filter' in request.GET:
        fil = request.GET['filter']
        if not fil in filters:
            fil = filters[0]
        request.session['invoice_filter'] = fil
    elif 'invoice_filter' in request.session:
        fil = request.session['invoice_filter']
    else:
        fil = filters[0]

    invs = StallInvoice.objects.all ()

    if fil == 'Pending':
        invs = invs.exclude (status = Invoice.BANKED)
    elif fil == 'Banked':
        invs = invs.filter (status = Invoice.BANKED)

    tpl_vars = {'page_title': 'Invoices', 'url': 'cams/invoice/',
                'filters': filters, 'filter': fil}
    add_common_tpl_vars (request, tpl_vars, 'invoice', invs, 10)
    return render_to_response ('cams/invoices.html', tpl_vars)

@login_required
def select_invoice (request):
    stalls = StallEvent.objects.filter (stallinvoice__isnull = True)
    stalls = stalls.filter (status = Record.ACTIVE)
    tpl_vars = {'page_title': 'Invoice', 'url': 'cams/invoice/select/'}
    add_common_tpl_vars (request, tpl_vars, 'invoice', stalls)
    return render_to_response ('cams/select_stall_invoice.html', tpl_vars)

@login_required
def add_invoice (request, stall_id):
    class StallInvoiceForm (forms.ModelForm):
        class Meta:
            model = StallInvoice
            exclude = ['stall', 'sent', 'paid', 'banked']

    stall = get_object_or_404 (StallEvent, pk = int (stall_id))

    if request.method == 'POST':
        form = StallInvoiceForm (request.POST)
        form.instance.stall = stall
        if form.is_valid ():
            form.save()
            return HttpResponseRedirect (reverse (invoices))
    else:
        TABLE_PRICE = 5
        SPACE_PRICE = 20
        amount = stall.n_tables * TABLE_PRICE
        amount += stall.n_spaces * SPACE_PRICE
        form = StallInvoiceForm (initial = {'amount': amount})

    tpl_vars = {'page_title': 'New invoice', 'form': form, 'stall': stall,
                'url': 'cams/invoice/'}
    add_common_tpl_vars (request, tpl_vars, 'invoice')
    return render_to_response ("cams/add_invoice.html", tpl_vars,
                               context_instance = RequestContext (request))

@login_required
def edit_invoice (request, inv_id):
    class StallInvoiceEditForm (forms.ModelForm):
        class Meta:
            model = StallInvoice
            fields = ['status', 'amount']
    inv = get_object_or_404 (StallInvoice, pk = int (inv_id))
    if request.method == 'POST':
        form = StallInvoiceEditForm (request.POST, instance = inv)
        if form.is_valid ():
            form.save ()
            return HttpResponseRedirect (
                reverse (stall_invoice, args = [inv_id]))
    else:
        form = StallInvoiceEditForm (instance = inv)

    tpl_vars = {'page_title': 'Edit invoice', 'inv': inv, 'form': form}
    add_common_tpl_vars (request, tpl_vars, 'invoice')
    return render_to_response ('cams/edit_invoice.html', tpl_vars,
                               context_instance = RequestContext (request))

@login_required
def stall_invoice (request, inv_id):
    status_keywords = {'sent': Invoice.SENT, 'paid': Invoice.PAID,
                       'banked': Invoice.BANKED}

    inv = get_object_or_404 (StallInvoice, pk = int (inv_id))
    if 'set' in request.GET:
        set = request.GET['set']
        if set in status_keywords:
            status = status_keywords[set]
            if inv.status < status:
                inv.status = status
                inv.save ()

    tpl_vars = {'page_title': 'Stall invoice details', 'inv': inv}
    add_common_tpl_vars (request, tpl_vars, 'invoice')
    return render_to_response ('cams/stall_invoice.html', tpl_vars)

@login_required
def export_invoices (request):
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
                             'created', 'sent', 'paid', 'banked'))

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
                        str (i.amount), i.status_str (), date_str (i.created),
                        date_str (i.sent), date_str(i.paid),
                        date_str (i.banked)))

    resp.set_file_name ("Stall_invoices")
    return resp.response

@login_required
def fairs (request):
    fair = get_object_or_404 (Fair, current = True)
    tpl_vars = {'page_title': 'Fairs', 'fair': fair}
    add_common_tpl_vars (request, tpl_vars, 'fairs')
    return render_to_response ('cams/fairs.html', tpl_vars)

@login_required
def export_group (request, group_id):
    group = get_object_or_404 (Group, pk = group_id)
    contacts = []
    members = group.members.all ()
    members = members.order_by ('last_name')

    for it in members:
        ctype = ''
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
            contacts.append ((it, ctype, org_name, c))

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
        csv.writerow ((p.first_name, p.middle_name, p.last_name,
                       ctype, org_name,
                       c.line_1, c.line_2, c.line_3, c.town, c.postcode,
                       c.telephone, c.mobile, c.fax, c.email, c.website,
                       str (c.addr_order), str (c.addr_suborder)))

    csv.set_file_name ('%s-%d' % (group.name.replace (' ', '_'),
                                  group.fair.date.year))

    return csv.response

@login_required
def export_programme (request):
    def istr (value):
        if value:
            return str (value)
        else:
            return ''

    csv = CSVFileResponse (('name', 'description',
                            'time', 'until', 'age_min', 'age_max', 'location',
                            'line_1', 'line_2', 'line_3', 'postcode', 'town',
                            'telephone', 'mobile', 'fax', 'email',
                            'website', 'order', 'sub-order'))

    events = FairEvent.objects.filter (status = Record.ACTIVE)
    events = events.filter (fair__current = True)

    listing = get_listing_id (request)
    if listing > 0:
        events = events.filter (etype = listing)
        listing_obj = get_object_or_404 (FairEventType, pk = listing)
        csv.set_file_name ("Programme_%s" %
                           listing_obj.name.replace (' ', '_'))
    elif listing == 0:
        events = events.filter (etype__isnull = True)
        csv.set_file_name ("Programme_Default")
    else:
        csv.set_file_name ("Programme")

    for e in events:
        c = e.get_composite_contact ()
        csv.writerow ((e.name, e.description,
                       istr (e.time), istr (e.end_time),
                       istr (e.age_min), istr (e.age_max), e.location,
                       c['line_1'], c['line_2'], c['line_3'],
                       c['postcode'], c['town'], c['telephone'], c['mobile'],
                       c['fax'], c['email'], c['website'],
                       str (c['addr_order']), str (c['addr_suborder'])))

    return csv.response
