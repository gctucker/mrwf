import datetime
import urllib
from django import forms
from django.db.models.query import Q
from django.http import (HttpResponse, HttpResponseRedirect, Http404,
                         HttpResponseForbidden)
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from cams.libcams import CAMS_VERSION, Page, get_user_pages, str2list
from cams.models import (Record, Person, Member, Organisation, Contact, Event,
                         Actor, Fair, Player, Group, Role, EventComment,
                         get_user_email)
from mrwf.extra.models import (FairEvent, StallEvent, FairEventApplication)
from mrwf.extra.forms import UserNameForm, PersonForm, ContactForm

from django import VERSION

PAGE_LIST = [
    Page ('home',    '',                   'welcome',      Page.OPEN),
    Page ('profile', 'profile/',           'user profile', Page.OPEN),
    Page ('abook',   'abook/',             'address book', Page.OPEN),
    Page ('parts',   'cams/participant/',  'participants', Page.OPEN),
#    Page ('prep',    'cams/prep/',         'preparation',  Page.OPEN),
    Page ('prog',    'cams/prog/',         'programme',    Page.OPEN),
    Page ('appli',   'cams/application/',  'applications', Page.ADMIN),
#    Page ('fairs',   'cams/fair/',         'winter fairs', Page.OPEN),
    Page ('admin',   'admin/',             'admin',        Page.ADMIN),
    Page ('logout',  'accounts/logout/',   'log out',      Page.OPEN)]


class SearchForm (forms.Form):
    match = forms.CharField (required = True, max_length = 64)


class CommentForm (forms.Form):
    attrs = {'cols': '80', 'rows': '5'}
    content = forms.CharField (widget = forms.Textarea (attrs = attrs))


def add_common_tpl_vars (request, tpl_vars, cpage, obj_list = None, n = 20):
    tpl_vars['px'] = settings.URL_PREFIX
    tpl_vars['user'] = request.user
    # ToDo: rename pages -> nav (avoid confusion with page in paginator)
    tpl_vars['pages'] = get_user_pages (PAGE_LIST, request.user)
    tpl_vars['current_page'] = cpage

    if obj_list:
        page = get_page (request, obj_list, n)
        tpl_vars['page'] = page

# -----------------------------------------------------------------------------
# Address Book views

def search_people (keywords):
    people = Person.objects.all ()

    for kw in keywords:
        people = people.filter (Q (first_name__icontains = kw) |
                                Q (middle_name__icontains = kw) |
                                Q (last_name__icontains = kw) |
                                Q (nickname__icontains = kw))
        people = people.filter (status = Record.ACTIVE)

    return people.values ('first_name', 'middle_name',
                          'last_name', 'nickname', 'id')

def search_orgs (keywords):
    orgs = Organisation.objects.all ()

    for kw in keywords:
        orgs = orgs.filter (Q (name__icontains = kw) |
                            Q (nickname__icontains = kw))
        orgs = orgs.filter (status = Record.ACTIVE)

    return orgs.values ('name', 'nickname', 'id')

def search_all (request, match):
    keywords = str2list (match)
    people = search_people (keywords)
    orgs = search_orgs (keywords)

    return {'people': people, 'orgs': orgs}

class PaginatorStub:
    def __init__ (self):
        self.object_list = []

    def add_list (self, items, type_name):
        for it in items:
            it['type'] = type_name
        self.object_list += items

    @property
    def num_pages (self):
        if len (self.object_list):
            return 1
        else:
            return 0

def add_common_tpl_vars_abook (request, tpl_vars, obj_list = None, n = 20):
    if 'match' in request.GET:
        match = request.GET['match']
    else:
        match = ''

    if match:
        # ToDo: get the url directly encoded instead of re-encoding it ?
        urlmatch = urllib.urlencode ((('match', match), ))
    else:
        urlmatch = ''

    add_common_tpl_vars (request, tpl_vars, 'abook', obj_list, n)
    tpl_vars['urlmatch'] = urlmatch
    tpl_vars['page_title'] = 'Address Book'

    return match

# -----------------------------------------------------------------------------

@login_required
def search (request):
    tpl_vars = {}
    match = add_common_tpl_vars_abook (request, tpl_vars)

    if match:
        found = search_all (request, match)
        people = list (found['people'])
        for p in people:
            p['contacts'] = Contact.objects.filter (object = p['id'])
        orgs = list (found['orgs'])
        for o in orgs:
            o['contacts'] = Contact.objects.filter (object = o['id'])
        results = PaginatorStub ()
        results.add_list (people, 'person')
        results.add_list (orgs, 'org')
    else:
        results = None

    form = SearchForm ({'match': match})
    tpl_vars['form'] = form
    tpl_vars['page'] = results

    return render_to_response ('abook/search.html', tpl_vars)

@login_required
def person (request, person_id):
    person = get_object_or_404 (Person, pk = person_id)
    contacts = Contact.objects.filter (object = person)
    members = Member.objects.filter (person = person)
    members = members.filter (status = Record.ACTIVE)
    tpl_vars = {'person': person, 'contacts': contacts, 'members': members,
                'url': 'abook/person/%d/' % person.id}
    add_common_tpl_vars_abook (request, tpl_vars, members, 10)
    return render_to_response ('abook/person.html', tpl_vars)

@login_required
def org (request, org_id):
    org = get_object_or_404 (Organisation, pk = org_id)
    contacts = Contact.objects.filter (object = org)
    members = Member.objects.filter (organisation = org)
    members = members.filter (status = Record.ACTIVE)
    tpl_vars = {'org': org, 'contacts': contacts, 'members': members,
                'url': 'abook/org/%d/' % org.id}
    add_common_tpl_vars_abook (request, tpl_vars, members, 10)
    return render_to_response ('abook/org.html', tpl_vars)

# -----------------------------------------------------------------------------
# Managment views

def get_page (request, list, n):
    pagin = Paginator (list, n)

    if 'page' in request.GET:
        try:
            page_n = int (request.GET['page'])
        except ValueError:
            page_n = 1
    else:
        page_n = 1

    try:
        page = pagin.page (page_n)
    except (InvalidPage, EmptyPage):
        page = pagin.page (pagin.num_pages)

    return page

def add_common_tpl_vars (request, tpl_vars, cpage, obj_list = None, n = 20):
    tpl_vars['px'] = settings.URL_PREFIX
    tpl_vars['user'] = request.user
    tpl_vars['pages'] = get_user_pages (PAGE_LIST, request.user)
    tpl_vars['current_page'] = cpage

    if obj_list:
        page = get_page (request, obj_list, n)
        tpl_vars['page'] = page

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

# -----------------------------------------------------------------------------

@login_required
def home (request):
    tpl_vars = {'page_title': 'Home'}
    add_common_tpl_vars (request, tpl_vars, 'home')
    return render_to_response ('home.html', tpl_vars)

@login_required
def profile (request):
    player = get_object_or_404 (Player, user = request.user)
    person = player.person
    contacts = Contact.objects.filter (object = person)

    if contacts.count () > 0:
        c = contacts[0]
    else:
        c = None

    tpl_vars = {'page_title': 'User Profile', 'person': person, 'contact': c}
    add_common_tpl_vars (request, tpl_vars, 'profile')
    return render_to_response ('profile.html', tpl_vars)

@login_required
def profile_edit (request):
    player = get_object_or_404 (Player, user = request.user)
    person = player.person
    contacts = Contact.objects.filter (object = person)

    if request.method == 'POST':
        u_form = UserNameForm (request.POST, instance = request.user,
                               prefix = 'user')
        p_form = PersonForm (request.POST, instance = person)

        if contacts.count () > 0:
            c_form = ContactForm (request.POST, instance = contacts[0])
        else:
            c_form = ContactForm (request.POST)
            c_form.instance.person = person

        if u_form.is_valid () and p_form.is_valid () and c_form.is_valid ():
            u_form.save ()
            p_form.save ()
            c_form.save ()
            return HttpResponseRedirect (reverse (profile))

    else:
        u_form = UserNameForm (instance = request.user, prefix = 'user')
        p_form = PersonForm (instance = person)

        if contacts.count () > 0:
            c_form = ContactForm (instance = contacts[0])
        else:
            c_form = ContactForm ()

    if request.user.is_staff:
        django_version = "v%d.%d.%d" % (VERSION[0], VERSION[1], VERSION[2])
        cams_version = "v%d.%d.%d" % (CAMS_VERSION[0], CAMS_VERSION[1],
                                      CAMS_VERSION[2])
    else:
        django_version = None
        cams_version = None

    tpl_vars = {'page_title': 'User Profile',
                'f_user': u_form, 'c_form': c_form,
                'p_form': p_form, 'django_version': django_version,
                'cams_version': cams_version}
    add_common_tpl_vars (request, tpl_vars, 'profile')
    return render_to_response ('profile_edit.html', tpl_vars,
                               context_instance = RequestContext(request))

@login_required
def password (request):
    if request.method == 'POST':
        f_passwd = PasswordChangeForm (request.user, request.POST)

        if f_passwd.is_valid ():
            f_passwd.save ()
            return HttpResponseRedirect (reverse (profile))
    else:
        f_passwd = PasswordChangeForm (request.user)

    tpl_vars = {'page_title': 'Change password', 'f_passwd': f_passwd}
    add_common_tpl_vars (request, tpl_vars, 'profile')
    return render_to_response ('password.html', tpl_vars,
                               context_instance = RequestContext (request))

@login_required
def email_test (request):
    email = get_user_email (request.user)
    if email:
        try:
            send_mail ("CAMS e-mail test",
                       "Your email is properly configured.",
                       "no-reply@mangoz.org", [email])
            all_good = True
        except smtplib.SMTPException:
            all_good = False
    else:
        all_good = False

    tpl_vars = {'page_title': 'Email test', 'all_good': all_good,
                'email': email}
    add_common_tpl_vars (request, tpl_vars, 'profile')
    return render_to_response ('email_test.html', tpl_vars)

@login_required
def participants (request):
    groups = Group.objects.all ()
    fair = get_object_or_404 (Fair, current = True)
    groups = groups.filter (Q (fair = fair) | Q (fair__isnull = True))
    groups = groups.order_by ('name')
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
    fair = get_object_or_404 (Fair, current = True)
    prog = FairEvent.objects.filter (fair = fair)
    if not request.user.is_staff:
        prog = prog.filter (status = Record.ACTIVE)
    prog = prog.order_by ('name')
    tpl_vars = {'page_title': 'Programme', 'url': 'cams/prog/'}
    add_common_tpl_vars (request, tpl_vars, 'prog', prog)
    return render_to_response ('cams/programme.html', tpl_vars)

@login_required
def prog_event (request, event_id):
    ev = get_object_or_404 (FairEvent, pk = event_id)
    if (not request.user.is_staff) and (ev.status != Record.ACTIVE):
        raise Http404
    form = get_form_if_actor (request, event_id)
    tpl_vars = {'page_title': 'Fair Event', 'ev': ev, 'form': form,
                'url': 'cams/prog/%d/' % ev.id}
    add_common_tpl_vars (request, tpl_vars, 'prog', get_comments (ev), 4)
    return render_to_response ('cams/prog_event.html', tpl_vars,
                               context_instance = RequestContext (request))

@login_required
def prog_event_cmt (request, event_id):
    return post_event_cmt (request, event_id, prog_event)

@login_required
def applications (request):
    applis = FairEventApplication.objects.all ()
    cats = FairEventApplication.xtypes
    tpl_vars = {'page_title': 'Applications', 'cats': cats}
    add_common_tpl_vars (request, tpl_vars, 'appli')
    return render_to_response ('cams/applications.html', tpl_vars)

@login_required
def appli_type (request, type_id):
    type_id = int (type_id)
    applis = FairEventApplication.objects.filter (subtype = type_id)
    type_name = FairEventApplication.xtypes[type_id][1]
    tpl_vars = {'page_title': 'Applications: %ss' % type_name,
                'applis': applis, 'type_id': type_id}
    add_common_tpl_vars (request, tpl_vars, 'appli', applis)
    template = "cams/appli_list.html"
    return render_to_response (template, tpl_vars)

@login_required
def appli_detail (request, type_id, appli_id):
    type_id = int (type_id)
    appli_id = int (appli_id)
    appli = get_object_or_404 (FairEventApplication, pk = appli_id)

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
        c = Contact.objects.filter (object = it)
        if c:
            c = c[0]
            ctype = 'person'

        if not c:
            member = Member.objects.filter (person = it)
            if member:
                member = member[0]
                org_name = member.organisation.name
                c = Contact.objects.filter (object = member)
                if c:
                    c = c[0]
                    ctype = 'member'

                if not c:
                    c = Contact.objects.filter (object = member.organisation)
                    if c:
                        c = c[0]
                        ctype = 'org'

        if c:
            contacts.append ((it, ctype, org_name, c))

    response = HttpResponse (mimetype = 'text/csv')
    response.write ("first_name,middle_name,last_name,contact_type,org," +
                    "line_1,line_2,line_3,town,postcode,country," +
                    "telephone,mobile,fax,order,suborder,email,website\n")
    for it in contacts:
        p = it[0]
        ctype = it[1]
        org_name = it[2]
        c = it[3]
        response.write (("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"," +
                         "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"," +
                         "\"%s\",\"%s\",\"%s\",%d,%d,\"%s\",\"%s\"\n") % (
            p.first_name, p.middle_name, p.last_name, ctype, org_name,
            c.line_1, c.line_2, c.line_3, c.town, c.postcode, c.country,
            c.telephone, c.mobile, c.fax, c.addr_order, c.addr_suborder,
            c.email, c.website))

    now = datetime.datetime.today ()
    fname = "%s-%d_%d-%02d-%02d:%02d-%02d-%02d.csv" % (
        group.name.replace (' ', '_'), group.fair.date.year,
        now.year, now.month, now.day, now.hour, now.minute, now.second)
    response['Content-Disposition'] = 'attachement; filename=\"%s\"' % fname
    return response
