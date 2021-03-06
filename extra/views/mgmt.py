# MRWF - extra/public/views/mgmt.py
#
# Copyright (C) 2009, 2010, 2011. 2012, 2013
# Guillaume Tucker <guillaume@mangoz.org>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
from urllib import urlencode
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
from cams.models import (Record, PinBoard, Player, Fair, Group, Actor,
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

def get_stall_invoice_address(inv, sep=u'\n'):
    if inv.stall.invoice_person:
        p = inv.stall.invoice_person
    else:
        p = inv.stall.owner

    address_list = [p.__unicode__()]
    c_address = None

    if inv.stall.invoice_contact:
        c = inv.stall.invoice_contact
    else:
        c = inv.stall.owner.contact

    if c:
        c_address = c.get_address(sep)
        if not c_address:
            c = None

    if not c and inv.stall.org:
        address_list.append(inv.stall.org.name)
        c = inv.stall.org.contact
        if c:
            c_address = c.get_address(sep)

    if c_address:
        address_list.append(c_address)

    return sep.join(address_list)

def get_filter_name(request, filters, filter_id, filter_arg='filter'):
    filter_name = request.GET.get(filter_arg)
    if filter_name is not None:
        if not filter_name in filters:
            filter_name = filters[0]
        request.session[filter_id] = filter_name
    else:
        filter_name = request.session.get(filter_id)
        if filter_name is None:
            filter_name = filters[0]
    return filter_name

# -----------------------------------------------------------------------------
# entry points from url's

class GroupsBaseView(SiteView):
    menu_name = 'groups'


class GroupsView(GroupsBaseView):
    template_name = 'cams/groups.html'
    title = "Groups"

    def get_context_data(self, **kw):
        ctx = super(GroupsView, self).get_context_data(**kw)
        board_id = kw.get('board_id', None)
        if board_id is None:
            board = None
            groups = Group.objects.filter(board__isnull=True)
        else:
            board = get_object_or_404(PinBoard, pk=int(board_id))
            groups = Group.objects.filter(board=board)
        ctx.update({'boards': Group.get_boards(), 'board': board})
        self._set_list_page(ctx, groups, 20)
        return ctx


class GroupBaseView(GroupsBaseView):

    def _get_group_and_title(self, **kw):
        group_id = int(kw['group_id'])
        self._group = get_object_or_404(Group, pk=group_id)
        self.title = self._group

    def get(self, *args, **kw):
        self._get_group_and_title(**kw)
        return super(GroupBaseView, self).get(*args, **kw)


class GroupView(GroupBaseView):
    template_name = 'cams/group.html'

    def get_context_data(self, **kw):
        ctx = super(GroupView, self).get_context_data(**kw)
        roles = Role.objects.filter(group=self._group)
        roles = roles.filter(contactable__status=Record.ACTIVE)
        roles = roles.order_by('contactable')
        ctx.update({'group': self._group})
        self._set_list_page(ctx, roles, 20)
        return ctx


class PinDownGroupView(GroupBaseView):
    template_name = 'cams/pindown_group.html'

    class Form(forms.Form):
        def __init__(self, group, *args, **kw):
            super(PinDownGroupView.Form, self).__init__(*args, **kw)
            boards = set(PinBoard.objects.all())
            for v in group.get_versions():
                if v.board in boards:
                    boards.remove(v.board)
            self.fields['board'] = forms.ChoiceField( \
                choices=[(b.pk, b.__unicode__()) for b in boards])

    def post(self, *args, **kw):
        self._get_group_and_title(**kw)
        form = PinDownGroupView.Form(self._group, self.request.POST)
        if not form.is_valid():
            return HttpResponseServerError("Form is not valid",
                                           mimetype='text/plain')
        board_id = form.cleaned_data['board']
        board = PinBoard.objects.get(pk=board_id)
        self._group.pin_down(board)
        return HttpResponseRedirect(reverse('group', args=[self._group.pk]))

    def get_context_data(self, **kw):
        ctx = super(PinDownGroupView, self).get_context_data(**kw)
        form = PinDownGroupView.Form(self._group)
        ctx.update({'group': self._group, 'form': form})
        return ctx


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
        urlmatch = urlencode((('match', match),))
    else:
        match = ''
        urlmatch = ''

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
                'search_form': search_form, 'urlmatch': urlmatch}
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
    # Only 1 type of applications for now...
    return HttpResponseRedirect(reverse('appli_type', args=[0]))

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
    filters = ('Pending', 'Accepted', 'Rejected', 'All')
    filter_name = get_filter_name(request, filters, 'appli_type_filter')
    if filter_name != 'All':
        for filter_id, filter_id_str in Application.xstatus:
            if filter_id_str == filter_name:
                break
        applis = applis.filter(status=filter_id)
    tpl_vars = {'title': 'Applications: %ss' % type_name,
                'url': 'cams/application/%d/' % type_id,
                'applis': applis, 'type_id': type_id, 'type_name': type_name,
                'filters': filters, 'filter': filter_name}
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
            appli.event.status = Record.ACTIVE
            appli.event.save()
        elif action == 'reject':
            appli.status = Application.REJECTED
            appli.save ()
            appli.event.status = Record.DISABLED
            appli.event.save()
        else:
            raise Http404
        return HttpResponseRedirect(reverse('applications'))

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

    def get_context_data(self, **kw):
        ctx = super(InvoicesView, self).get_context_data(**kw)

        filters = ('All', 'Pending', 'Paid')
        filter_name = get_filter_name(self.request, filters, 'invoice_filter')
        fair = Fair.get_current()
        invoices = StallInvoice.objects.filter(stall__event__fair=fair)
        if filter_name == 'Pending':
            invoices = invoices.exclude(status=Invoice.PAID)
        elif filter_name == 'Paid':
            invoices = invoices.filter(status=Invoice.PAID)

        self._set_list_page(ctx, invoices, 10)
        ctx.update({'filters': filters, 'filter': filter_name})
        return ctx


class SelectInvoiceView(DefaultInvoiceView):
    template_name = 'cams/select_stall_invoice.html'
    perms = DefaultInvoiceView.perms + ['extra.invoices_add']
    title = "Invoice"

    def get_context_data(self, **kw):
        ctx = super(SelectInvoiceView, self).get_context_data(**kw)
        stalls = StallEvent.objects.filter(stallinvoice__isnull=True)
        stalls = stalls.filter(status=Record.ACTIVE)
        self._set_list_page(ctx, stalls)
        return ctx


class AddInvoiceView(DefaultInvoiceView):
    template_name = 'cams/add_invoice.html'
    perms = DefaultInvoiceView.perms + ['extra.invoices_add']

    class StallInvoiceForm(forms.ModelForm):
        class Meta:
            model = StallInvoice
            exclude = ['stall', 'sent', 'paid', 'cancelled']

    def dispatch(self, *args, **kw):
        stall_id = int(kw['stall_id'])
        self._stall = get_object_or_404(StallEvent, pk=stall_id)
        return super(AddInvoiceView, self).dispatch(*args, **kw)

    def post(self, *args, **kw):
        self._form = self.StallInvoiceForm(self.request.POST)
        if self._form.is_valid():
            self._form.instance.stall = self._stall
            self._form.save()
            self.history.create_form(self.request.user, self._form, ['stall'])
            return HttpResponseRedirect(reverse('invoices'))
        return super(AddInvoiceView, self).get(*args, **kw)

    def _OFF_get(self, *args, **kw):
        # ToDo: do not hard-code this, use a database table
        SPACE_PRICE = 25
        amount = self._stall.n_spaces * SPACE_PRICE
        self._form = self.StallInvoiceForm(
            initial={'amount': amount, 'reference': self._gen_reference()})
        return super(AddInvoiceView, self).get(*args, **kw)

    def get(self, *args, **kw):
        if self._stall.mc_stall_option is not None:
            prices = {StallEvent.MC_STALL_OPT_INSIDE_1: 30,
                      StallEvent.MC_STALL_OPT_INSIDE_2: 60,
                      StallEvent.MC_STALL_OPT_OUTSIDE: 25}
            amount = prices[self._stall.mc_stall_option]
        elif self._stall.plot_type is not None:
            prices = {StallEvent.PLOT_A: 50,
                      StallEvent.PLOT_B: 75,
                      StallEvent.PLOT_C: 85}
            amount = prices[self._stall.plot_type]
        else:
            amount = 0 # should never get here in principle...
        self._form = self.StallInvoiceForm(
            initial={'amount': amount, 'reference': self._gen_reference()})
        return super(AddInvoiceView, self).get(*args, **kw)

    def get_context_data(self, **kw):
        ctx = super(AddInvoiceView, self).get_context_data(**kw)
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

    def get_context_data(self, **kw):
        ctx = super(BaseInvoiceView, self).get_context_data(**kw)
        ctx.update({'inv': self._invoice})
        return ctx


class StallInvoiceView(BaseInvoiceView):
    template_name = 'cams/stall_invoice.html'
    status_kw = ((Invoice.SENT, 'sent'), (Invoice.PAID, 'paid'),
                 (Invoice.CANCELLED, 'cancelled'))

    def post(self, *args, **kw):
        status_str = self.request.POST.get('set')
        if status_str is not None:
            for stat in self.status_kw:
                if stat[1] == status_str:
                    self._invoice.update_status(stat[0])
                    self._invoice.save()
                    self.history.edit(self.request.user, self._invoice,
                                      ['status'])
                    url = reverse('stall_invoice', args=[self._invoice.id])
                    return HttpResponseRedirect(url)
        return super(StallInvoiceView, self).get(*args, **kw)

    def get_context_data(self, **kw):
        ctx = super(StallInvoiceView, self).get_context_data(**kw)
        stat_cmd_list = []
        for trans in self._invoice.stat_trans:
            for stat in self.status_kw:
                if stat[0] == trans:
                    stat_cmd_list.append(stat[1])
        ctx.update({'stat_cmd_list': stat_cmd_list})
        return ctx

class EditInvoiceView(BaseInvoiceView):
    template_name = 'cams/edit_invoice.html'
    perms = BaseInvoiceView.perms + ['extra.invoices_edit']
    title = "Edit invoice"

    class StallInvoiceEditForm(forms.ModelForm):
        class Meta:
            model = StallInvoice
            fields = ['amount', 'reference']

    def post(self, *args, **kw):
        self._form = self.StallInvoiceEditForm(self.request.POST,
                                               instance=self._invoice)
        if self._form.is_valid():
            self._form.save()
            self.history.edit_form(self.request.user, self._form)
            url = reverse('stall_invoice', args=[self._invoice.id])
            return HttpResponseRedirect(url)
        return super(EditInvoiceView, self).get(*args, **kw)

    def get(self, *args, **kw):
        self._form = self.StallInvoiceEditForm(instance=self._invoice)
        return super(EditInvoiceView, self).get(*args, **kw)

    def get_context_data(self, **kw):
        ctx = super(EditInvoiceView, self).get_context_data(**kw)
        ctx.update({'form': self._form, 'inv': self._invoice})
        return ctx


# ToDo: use GET method instead of POST for the form
class InvoiceHTMLView(BaseInvoiceView):
    title = "Stall invoice"

    class HTMLForm(forms.Form):
        address = forms.CharField \
            (required=True,
             widget=forms.Textarea(attrs={'cols': '40', 'rows': '5'}))
        date = forms.DateField(required=True, widget=SelectDateWidget)
        details = forms.CharField \
            (required=True,
             widget=forms.Textarea(attrs={'cols': '40', 'rows': '3'}))

    def dispatch(self, *args, **kw):
        self._invoice_ready = False
        return super(InvoiceHTMLView, self).dispatch(*args, **kw)

    def post(self, *args, **kw):
        self._form = self.HTMLForm(self.request.POST)
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
        return super(InvoiceHTMLView, self).get(*args, **kw)

    def get(self, *args, **kw):
        self._form = self._make_html_form()
        return super(InvoiceHTMLView, self).get(*args, **kw)

    def get_context_data(self, **kw):
        ctx = super(InvoiceHTMLView, self).get_context_data(**kw)
        if self._invoice_ready:
            self.template_name = 'cams/invoice_html.html'
            ctx.update({'address': self._address, 'details': self._details})
        else:
            self.template_name = 'cams/invoice_edit_html.html'
            ctx.update({'form': self._form})
        return ctx

    def _make_html_form(self):
        inv = self._invoice

        address = get_stall_invoice_address(inv)

        inv_details = ''

        if inv.stall.etype:
            inv_details += "{}\n".format(inv.stall.etype)

        if inv.stall.n_spaces:
            inv_details += "{} x spaces\n".format(inv.stall.n_spaces)

        if inv.stall.n_tables:
            inv_details += "{} x table hire\n".format(inv.stall.n_tables)

        if inv.stall.mc_stall_option:
            inv_details += "{0}\n".format(inv.stall.mc_stall_option_str)

        if inv.stall.plot_type:
            inv_details += "{0}\n".format(inv.stall.plot_type_str)

        return self.HTMLForm(initial={'address': address,
                                      'date': datetime.date.today(),
                                      'details': inv_details})
