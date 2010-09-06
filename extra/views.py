import datetime
import urllib
from django import forms
from django.db.models.query import Q
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden)
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from cams.libcams import CAMS_VERSION, Page, get_user_pages, str2list
from cams.models import (Person, Member, Organisation, PersonContact,
                         MemberContact, OrganisationContact, Event, Actor,
                         Fair, Participant, Group, Role, EventComment)
from mrwf.extra.models import (FairEvent)

from django import VERSION

PAGE_LIST = [
    Page ('home',    '',                   'welcome',      Page.OPEN),
    Page ('profile', 'profile/',           'user profile', Page.OPEN),
    Page ('abook',   'abook/',             'address book', Page.OPEN),
    Page ('parts',   'cams/participants/', 'participants', Page.OPEN),
    Page ('prep',    'cams/prep/',         'preparation',  Page.OPEN),
    Page ('prog',    'cams/prog/',         'programme',    Page.OPEN),
    Page ('fairs',   'cams/fairs/',        'winter fairs', Page.OPEN),
    Page ('admin',   'admin/',             'admin',        Page.ADMIN),
    Page ('logout',  'accounts/logout/',   'log out',      Page.OPEN)]


class SearchForm (forms.Form):
    match = forms.CharField (required = True, max_length = 64)


class CommentForm (forms.Form):
    attrs = {'cols': '80', 'rows': '5'}
    content = forms.CharField (widget = forms.Textarea (attrs = attrs))


# -----------------------------------------------------------------------------
# Address Book views

def search_people (keywords):
    people = Person.objects.all ()

    for kw in keywords:
        people = people.filter (Q (first_name__icontains = kw) |
                                Q (middle_name__icontains = kw) |
                                Q (last_name__icontains = kw) |
                                Q (nickname__icontains = kw))

    return people.values ('first_name', 'middle_name',
                          'last_name', 'nickname', 'id')

def search_orgs (keywords):
    orgs = Organisation.objects.all ()

    for kw in keywords:
        orgs = orgs.filter (Q (name__icontains = kw) |
                            Q (nickname__icontains = kw))

    return orgs.values ('name', 'nickname', 'id')

def search_all (request, match):
    keywords = str2list (match)
    people = search_people (keywords)
    orgs = search_orgs (keywords)

    return {'people': people, 'orgs': orgs}

def render_common (request, template, tpl_vars = {}):
    if 'match' in request.GET:
        match = request.GET['match']
    else:
        match = ''

    if match:
        found = search_all (request, match)
        # ToDo: get the url directly encoded from instead of re-encoding it ?
        urlmatch = urllib.urlencode ((('match', match), ))
        people = found['people']
        orgs = found['orgs']
    else:
        urlmatch = ''
        people = None
        orgs = None

    form = SearchForm ({'match': match})

    tpl_vars['pages'] = get_user_pages (PAGE_LIST, request.user)
    tpl_vars['current_page'] = 'abook'
    tpl_vars['form'] = form
    tpl_vars['urlmatch'] = urlmatch
    tpl_vars['people'] = people
    tpl_vars['orgs'] = orgs
    tpl_vars['px'] = settings.URL_PREFIX
    tpl_vars['page_title'] = 'Address Book'
    tpl_vars['user'] = request.user

    return render_to_response (template, tpl_vars)

# -----------------------------------------------------------------------------

@login_required
def search (request):
    return render_common (request, 'abook/search.html')

@login_required
def person (request, person_id):
    try:
        person = Person.objects.get (pk = person_id)
    except Person.DoesNotExist:
        raise Http404

    contacts = PersonContact.objects.filter (person = person)

    # workaround until better member contact support is implemented
    if not contacts:
        member = Member.objects.filter (person = person)
        if member:
            contacts = MemberContact.objects.filter (member = member[0])

    tpl_vars = {'person': person, 'contacts': contacts}

    return render_common (request, 'abook/person.html', tpl_vars)

@login_required
def org (request, org_id):
    try:
        org = Organisation.objects.get (pk = org_id)
    except Organisation.DoesNotExist:
        raise Http404

    contacts = OrganisationContact.objects.filter (org = org)

    tpl_vars = {'org': org, 'contacts': contacts}

    return render_common (request, 'abook/org.html', tpl_vars)

# -----------------------------------------------------------------------------
# CAMS views

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

def add_common_tpl (request, tpl_vars, cpage, obj_list = None, n = 20):
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

    part = get_object_or_404 (Participant, user = request.user)
    ev = get_object_or_404 (Event, pk = event_id)

    try:
        actor = Actor.objects.get (participant = part, event = ev)
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
    add_common_tpl (request, tpl_vars, 'home')
    return render_to_response ('home.html', tpl_vars)

@login_required
def profile (request):
    part = get_object_or_404 (Participant, user = request.user)
    roles = Role.objects.filter (participant = part)
    contacts = PersonContact.objects.filter (person = part.person)

    if contacts:
        contact = contacts[0]
    else:
        contact = None

    if request.user.is_staff:
        django_version = "v%d.%d.%d" % (VERSION[0], VERSION[1], VERSION[2])
        cams_version = "v%d.%d.%d" % (CAMS_VERSION[0], CAMS_VERSION[1],
                                      CAMS_VERSION[2])
    else:
        django_version = None
        cams_version = None

    tpl_vars = {'page_title': 'User Profile', 'part': part, 'roles': roles,
                'contact': contact, 'django_version': django_version,
                'cams_version': cams_version}
    add_common_tpl (request, tpl_vars, 'profile')
    return render_to_response ('profile.html', tpl_vars)

@login_required
def participants (request):
    show_all = get_show_all (request)

    if show_all:
        groups = Group.objects.all ()
    else:
        part = get_object_or_404 (Participant, user = request.user)
        groups = part.group_set

    fair = get_object_or_404 (Fair, current = True)
    groups = groups.filter (Q (fair = fair) | Q (fair__isnull = True))
    groups = groups.order_by ('name')
    tpl_vars = {'page_title': 'Participants', 'url': 'cams/participants/',
                'show_all': show_all}
    add_common_tpl (request, tpl_vars, 'parts', groups)
    return render_to_response ('cams/participants.html', tpl_vars)

@login_required
def group (request, group_id):
    group = get_object_or_404 (Group, pk = group_id)
    roles = Role.objects.filter (group = group)
    roles = roles.order_by ('participant__person__last_name')
    tpl_vars = {'page_title': 'Group members', 'group': group,
                'url': 'cams/participants/group/%d/' % group.id}
    add_common_tpl (request, tpl_vars, 'parts', roles)
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
    part = get_object_or_404 (Participant, user = request.user)
    if not request.user.is_staff:
        try:
            actor = Actor.objects.get (participant = part, event = ev)
        except Actor.DoesNotExist:
            return HttpResponseForbidden ("you are not allowed to post here",
                                          mimetype = 'text/plain')

    cmt = EventComment (author = part, event = ev,
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
        part = get_object_or_404 (Participant, user = request.user)
        acts = Actor.objects.filter (participant = part)
        acts = acts.order_by ('event__date', 'event__time')
        tpl = 'cams/preparation.html'

    # ToDo: filter past events and add option to see them
    tpl_vars = {'page_title': 'Preparation', 'url': 'cams/prep/',
                'show_all': show_all}
    add_common_tpl (request, tpl_vars, 'prep', acts)
    return render_to_response (tpl, tpl_vars)

@login_required
def prep_event (request, event_id):
    ev = get_object_or_404 (Event, pk = event_id)
    form = get_form_if_actor (request, event_id)
    tpl_vars = {'page_title': 'Event', 'ev': ev, 'form': form,
                'url': 'cams/prep/%d/' % ev.id}
    add_common_tpl (request, tpl_vars, 'prep', get_comments (ev), 4)
    return render_to_response ('cams/prep_event.html', tpl_vars,
                               context_instance = RequestContext (request),)

@login_required
def prep_event_cmt (request, event_id):
    return post_event_cmt (request, event_id, prep_event)

@login_required
def programme (request):
    fair = get_object_or_404 (Fair, current = True)
    prog = FairEvent.objects.filter (fair = fair)
    prog = prog.order_by ('name')
    tpl_vars = {'page_title': 'Programme', 'url': 'cams/prog/'}
    add_common_tpl (request, tpl_vars, 'prog', prog)
    return render_to_response ('cams/programme.html', tpl_vars)

@login_required
def prog_event (request, event_id):
    ev = get_object_or_404 (FairEvent, pk = event_id)
    form = get_form_if_actor (request, event_id)
    tpl_vars = {'page_title': 'Fair Event', 'ev': ev, 'form': form,
                'url': 'cams/prog/%d/' % ev.id}
    add_common_tpl (request, tpl_vars, 'prog', get_comments (ev), 4)
    return render_to_response ('cams/prog_event.html', tpl_vars,
                               context_instance = RequestContext (request))

@login_required
def prog_event_cmt (request, event_id):
    return post_event_cmt (request, event_id, prog_event)

@login_required
def fairs (request):
    fair = get_object_or_404 (Fair, current = True)
    tpl_vars = {'page_title': 'Fairs', 'fair': fair}
    add_common_tpl (request, tpl_vars, 'fairs')
    return render_to_response ('cams/fairs.html', tpl_vars)

@login_required
def export_group (request, group_id):
    group = get_object_or_404 (Group, pk = group_id)
    contacts = []
    members = group.members.all ()
    members = members.order_by ('person__last_name')

    for it in members:
        ctype = ''
        org_name = ''
        c = PersonContact.objects.filter (person = it.person)
        if c:
            c = c[0]
            ctype = 'person'

        if not c:
            member = Member.objects.filter (person = it.person)
            if member:
                member = member[0]
                org_name = member.organisation.name
                c = MemberContact.objects.filter (member = member)
                if c:
                    c = c[0]
                    ctype = 'member'

                if not c:
                    c = OrganisationContact.objects.filter (
                        org = member.organisation)
                    if c:
                        c = c[0]
                        ctype = 'org'

        if c:
            contacts.append ((it.person, ctype, org_name, c))

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
