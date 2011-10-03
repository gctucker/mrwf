import datetime
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.core.urlresolvers import reverse
from django.http import (HttpResponseForbidden, HttpResponseRedirect,
                         Http404, HttpResponseServerError)
from django.template import RequestContext
from django.db.models.query import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from mrwf.extra.views.main import add_common_tpl_vars, SiteView
from cams.libcams import str2list
from cams.models import (Record, Player, Fair, Group, Actor,
                         Role, Event, EventComment, Application, Invoice)
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
    tpl_vars = {'title': 'Groups', 'url': 'cams/participant/'}
    add_common_tpl_vars (request, tpl_vars, 'groups', groups)
    return render_to_response ('cams/participants.html', tpl_vars)

@login_required
def group (request, group_id):
    group = get_object_or_404 (Group, pk = group_id)
    roles = Role.objects.filter (group = group)
    roles = roles.filter (contactable__status = Record.ACTIVE)
    # ToDo: sort alphabetically... without fetching the 2 full tables for
    # people and orgs!
    tpl_vars = {'title': group, 'group': group,
                'url': 'cams/participant/group/%d/' % group.id}
    add_common_tpl_vars (request, tpl_vars, 'groups', roles)
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

    tpl_vars = {'title': 'Programme', 'url': 'cams/prog/',
                'listings': listings, 'current': listing,
                'search_form': search_form}
    add_common_tpl_vars (request, tpl_vars, 'programme', prog, 8)
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

    tpl_vars = {'title': 'Fair Event', 'ev': ev, 'form': form,
                'url': 'cams/prog/%d/' % ev.id, 'admin_type': admin_type}
    add_common_tpl_vars (request, tpl_vars, 'programme', get_comments (ev), 4)
    return render_to_response ('cams/prog_event.html', tpl_vars,
                               context_instance = RequestContext (request))

@login_required
def prog_event_cmt (request, event_id):
    return post_event_cmt (request, event_id, prog_event)

@login_required
def applications (request):
    fair = Fair.get_current()
    cats = []
    all_applis = FairEventApplication.objects.filter (event__fair = fair)
    for cat_id, cat_name in FairEventApplication.xtypes:
        cat_type = {'id': cat_id, 'name': cat_name}
        applis = all_applis.filter (subtype = cat_id)
        pending = applis.filter (status = Application.PENDING)
        accepted = applis.filter (status = Application.ACCEPTED)
        rejected = applis.filter (status = Application.REJECTED)
        stats = {'pending': pending.count (), 'accepted': accepted.count (),
                 'rejected': rejected.count (), 'total': applis.count ()}
        cats.append ((cat_type, stats))
    tpl_vars = {'title': 'Applications', 'cats': cats}
    add_common_tpl_vars (request, tpl_vars, 'applications')
    return render_to_response ('cams/applications.html', tpl_vars)

@login_required
def appli_type (request, type_id):
    type_id = int (type_id)
    applis = FairEventApplication.objects.filter (subtype = type_id)
    applis = FairEventApplication.objects.filter \
        (event__fair = Fair.get_current())
    applis = applis.order_by('event__name')
    type_name = FairEventApplication.xtypes[type_id][1]
    tpl_vars = {'title': 'Applications: %ss' % type_name,
                'url': 'cams/application/%d/' % type_id,
                'applis': applis, 'type_id': type_id}
    add_common_tpl_vars (request, tpl_vars, 'applications', applis, 10)
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

    tpl_vars = {'title': 'Application', 'type_id': type_id,
                'appli': appli, 'detail': detail}
    add_common_tpl_vars (request, tpl_vars, 'applications')
    type_name = FairEventApplication.xtypes[type_id][1]
    template = "cams/appli_%s.html" % type_name
    return render_to_response (template, tpl_vars)

class DefaultInvoiceView(SiteView):
    perms = ['extra.invoices_view']
    menu_name = 'invoices'
    title = "Invoices"


class InvoicesView(DefaultInvoiceView):
    template_name = 'cams/invoices.html'

    def get_context_data(self, *args, **kw):
        ctx = super(InvoicesView, self).get_context_data(*args, **kw)

        filters = ('All', 'Pending', 'Banked')
        filter_name = self.request.GET.get('filter')
        if filter_name is not None:
            if not filter_name in filters:
                filter_name = filters[0]
            self.request.session['invoice_filter'] = filter_name
        else:
            filter_name = self.request.session.get('invoice_filter')
            if filter_name is None:
                filter_name = filters[0]

        fair = Fair.get_current()
        invoices = StallInvoice.objects.filter(stall__event__fair=fair)
        if filter_name == 'Pending':
            invoices = invoices.exclude(status=Invoice.BANKED)
        elif filter_name == 'Banked':
            invoices = invoices.filter(status=Invoice.BANKED)

        self._set_list_page(ctx, invoices, 10)
        ctx.update({'filters': filters, 'filter': filter_name})
        return ctx


class SelectInvoiceView(DefaultInvoiceView):
    template_name = 'cams/select_stall_invoice.html'
    perms = DefaultInvoiceView.perms + ['extra.invoices_add']
    title = "Invoice"

    def get_context_data(self, *args, **kw):
        ctx = super(SelectInvoiceView, self).get_context_data(*args, **kw)
        stalls = StallEvent.objects.filter (stallinvoice__isnull = True)
        stalls = stalls.filter (status = Record.ACTIVE)
        self._set_list_page(ctx, stalls)
        return ctx


class AddInvoiceView(DefaultInvoiceView):
    template_name = 'cams/add_invoice.html'
    perms = DefaultInvoiceView.perms + ['extra.invoices_add']

    class StallInvoiceForm(forms.ModelForm):
        class Meta:
            model = StallInvoice
            exclude = ['stall', 'sent', 'paid', 'banked']

    def dispatch(self, *args, **kw):
        stall_id = int(kw['stall_id'])
        self._stall = get_object_or_404(StallEvent, pk=stall_id)
        return super(AddInvoiceView, self).dispatch(*args, **kw)

    def post(self, *args, **kw):
        self._form = self.StallInvoiceForm(self.request.POST)
        if self._form.is_valid():
            self._form.instance.stall = self._stall
            self._form.save()
            return HttpResponseRedirect(reverse('invoices'))
        return super(AddInvoiceView, self).get(*args, **kw)

    def get(self, *args, **kw):
        # ToDo: do not hard-code this, use a database table
        SPACE_PRICE = 25
        amount = self._stall.n_spaces * SPACE_PRICE
        self._form = self.StallInvoiceForm \
            (initial={'amount': amount, 'reference': self._gen_reference()})
        return super(AddInvoiceView, self).get(*args, **kw)

    def get_context_data(self, *args, **kw):
        ctx = super(AddInvoiceView, self).get_context_data(*args, **kw)
        ctx.update({'form': self._form, 'stall': self._stall})
        return ctx

    def _gen_reference(self):
        fair = Fair.get_current()
        inv = StallInvoice.objects.filter(stall__fair=fair)
        inv = inv.filter(stall__etype=self._stall.etype)
        n = 1 + inv.count()
        return '{:d}{:s}{:03d}'.format(fair.date.year, self._stall.etype.tag,n)


class BaseInvoiceView(DefaultInvoiceView):
    def dispatch(self, *args, **kw):
        inv_id = int(kw['inv_id'])
        self._invoice = get_object_or_404(StallInvoice, pk=inv_id)
        return super(BaseInvoiceView, self).dispatch(*args, **kw)

    def get_context_data(self, *args, **kw):
        ctx = super(BaseInvoiceView, self).get_context_data(*args, **kw)
        ctx.update({'inv': self._invoice})
        return ctx


class StallInvoiceView(BaseInvoiceView):
    template_name = 'cams/stall_invoice.html'

    def get(self, *args, **kw):
        # ToDo: that should happen with POST
        status_set = self.request.GET.get('set')
        if status_set is not None:
            status_keywords = {'sent': Invoice.SENT, 'paid': Invoice.PAID,
                               'banked': Invoice.BANKED}
            status = status.keywords.get(status_set)
            if status is not None:
                if self._invoice.status < status:
                    self._invoice.status = status
                    self._invoice.save()
        return super(StallInvoiceView, self).get(*args, **kw)


class EditInvoiceView(BaseInvoiceView):
    template_name = 'cams/edit_invoice.html'
    perms = BaseInvoiceView.perms + ['extra.invoices_edit']
    title = "Edit invoice"

    class StallInvoiceEditForm(forms.ModelForm):
        class Meta:
            model = StallInvoice
            fields = ['amount', 'status', 'reference']

    def post(self, *args, **kw):
        self._form = self.StallInvoiceEditForm(self.request.POST,
                                               instance=self._invoice)
        if self._form.is_valid():
            self._form.save()
            url = reverse('stall_invoice', args=[self._invoice.id])
            return HttpResponseRedirect(url)
        return super(EditInvoiceView, self).get(*args, **kw)

    def get(self, *args, **kw):
        self._form = self.StallInvoiceEditForm(instance=self._invoice)
        return super(EditInvoiceView, self).get(*args, **kw)

    def get_context_data(self, *args, **kw):
        ctx = super(EditInvoiceView, self).get_context_data(*args, **kw)
        ctx.update({'form': self._form, 'inv': self._invoice})
        return ctx


# ToDo: PDF instead?
# ToDo: use GET method instead of POST for the form
class InvoiceHardCopyView(BaseInvoiceView):
    title = "Stall invoice"

    class HardCopyForm (forms.Form):
        address = forms.CharField \
            (required=True,
             widget=forms.Textarea(attrs={'cols': '40', 'rows': '5'}))
        date = forms.DateField(required=True, widget=SelectDateWidget)
        details = forms.CharField \
            (required=True,
             widget=forms.Textarea(attrs={'cols': '40', 'rows': '3'}))

    def dispatch(self, *args, **kw):
        self._invoice_ready = False
        return super(InvoiceHardCopyView, self).dispatch(*args, **kw)

    def post(self, *args, **kw):
        self._form = self.HardCopyForm(self.request.POST)
        if self._form.is_valid():
            details = [("Date", self._form.cleaned_data['date'])]
            if self._invoice.reference:
                details.append(('Invoice number', self._invoice.reference))
            details.append(("Details", self._form.cleaned_data['details']))
            details.append(("Amount",
                            '&#163;{:2f}'.format(self._invoice.amount)))
            self._address = self._form.cleaned_data['address']
            self._details = details
            self._invoice_ready = True
        return super(InvoiceHardCopyView, self).get(*args, **kw)

    def get(self, *args, **kw):
        self._form = self._make_hard_copy_form()
        return super(InvoiceHardCopyView, self).get(*args, **kw)

    def get_context_data(self, *args, **kw):
        ctx = super(InvoiceHardCopyView, self).get_context_data(*args, **kw)
        if self._invoice_ready:
            self.template_name = 'cams/invoice_hard_copy.html'
            ctx.update({'address': self._address, 'details': self._details})
        else:
            self.template_name = 'cams/invoice_edit_hard_copy.html'
            ctx.update({'form': self._form})
        return ctx

    def _make_hard_copy_form(self):
        inv = self._invoice

        address_list = [inv.stall.owner.__unicode__()]

        c = inv.stall.owner.contact
        if c:
            c_address = c.get_address('\n')
            if not c_address:
                c = None

        if not c and inv.stall.org:
            address_list.append(inv.stall.org.name)
            c = inv.stall.org.contact
            if c:
                c_address = c.get_address('\n')

        if c_address:
            address_list.append(c_address)

        address = '\n'.join(address_list)

        if inv.stall.etype:
            listing = "{}:\n".format(inv.stall.etype)
        else:
            listing = ''

        inv_details = "{}{} x Stall space".format(listing, inv.stall.n_spaces)
        if inv.stall.n_tables:
            inv_details += " and {} x table hire".format(inv.stall.n_tables)

        return self.HardCopyForm(initial={'address': address,
                                          'date': datetime.date.today(),
                                          'details': inv_details})
