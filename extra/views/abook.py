import urllib
from django import forms
from django.db.models.query import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from cams.libcams import str2list
from cams.models import (Record, Contactable, Person, Organisation, Member,
                         Contact)
from mrwf.extra.views.main import add_common_tpl_vars

class SearchHelper:
    def __init__ (self, request):
        self.form = SearchHelper.SearchForm (request.GET)
        if self.form.is_valid ():
            self.match = self.form.cleaned_data['match']
            self.opt_contacts = self.form.cleaned_data['opt_contacts']
            self.urlmatch = urllib.urlencode ((('match', self.match),
                                               ('opt_contacts',
                                                self.opt_contacts)))
        else:
            self.match = ''
            self.urlmatch = ''
            self.opt_contacts = False

    class SearchForm (forms.Form):
        match = forms.CharField (required = True, max_length = 64)
        opt_contacts = forms.BooleanField (required = False,
                                           label = "search within contacts")

class PaginatorStub:
    def __init__ (self):
        self.object_list = []

    def add_list (self, items, type_name):
        for it in items:
            it['type'] = type_name
        self.object_list += items

    def limit_list (self, max_objects):
        if len (self.object_list) > max_objects:
            self.object_list = self.object_list[:max_objects]

    @property
    def num_pages (self):
        if len (self.object_list):
            return 1
        else:
            return 0


def add_common_tpl_vars_abook (request, tpl_vars, ctx, obj_list = None, n=20):
    add_common_tpl_vars (request, tpl_vars, 'abook', obj_list, n)
    tpl_vars['page_title'] = 'Address Book'
    tpl_vars['urlmatch'] = ctx.urlmatch

def search_people (keywords):
    people = Person.objects.all ()

    for kw in keywords:
        people = people.filter (Q (first_name__icontains = kw) |
                                Q (middle_name__icontains = kw) |
                                Q (last_name__icontains = kw) |
                                Q (nickname__icontains = kw))

    return people.filter (status = Record.ACTIVE)

def search_orgs (keywords):
    orgs = Organisation.objects.all ()

    for kw in keywords:
        orgs = orgs.filter (Q (name__icontains = kw) |
                            Q (nickname__icontains = kw))

    return orgs.filter (status = Record.ACTIVE)

def search_contacts (keywords):
    contacts = Contact.objects.all ()

    for kw in keywords:
        contacts = contacts.filter (Q (line_1__icontains = kw) |
                                    Q (line_2__icontains = kw) |
                                    Q (line_3__icontains = kw) |
                                    Q (town__icontains = kw) |
                                    Q (postcode__icontains = kw) |
                                    Q (country__icontains = kw) |
                                    Q (email__icontains = kw) |
                                    Q (website__icontains = kw) |
                                    Q (telephone__icontains = kw) |
                                    Q (mobile__icontains = kw) |
                                    Q (fax__icontains = kw) |
                                    Q (addr_order__icontains = kw) |
                                    Q (addr_suborder__icontains = kw))

    return contacts.filter (status = Record.ACTIVE)

def append_person (list, p, c):
    list.append ({'first_name': p.first_name,
                  'middle_name': p.middle_name,
                  'last_name': p.last_name,
                  'nickname': p.nickname,
                  'id': p.id,
                  'contacts': c})

def append_org (list, o, c):
    list.append ({'name': o.name,
                  'nickname': o.nickname,
                  'id': o.id,
                  'contacts': c})

# -----------------------------------------------------------------------------
# entry points from url's

@login_required
def search (request):
    ctx = SearchHelper (request)
    tpl_vars = {}
    add_common_tpl_vars_abook (request, tpl_vars, ctx)

    if ctx.match:
        keywords = str2list (ctx.match)
        people = []
        orgs = []

        if ctx.opt_contacts:
            # Note: There may be several matching contacts related to the same
            # person/org, so that person/org will be in the results several
            # times (with a different contact preview though)

            contacts = list (search_contacts (keywords))
            for c in contacts:
                obj_id = c.obj_id
                obj = Contactable.objects.get (pk = obj_id)
                # ToDo: transform (cast) a Contactable to its subclass...
                if obj.type == Contactable.ORGANISATION:
                    o = Organisation.objects.get (pk = obj_id)
                    append_org (orgs, o, (c,))
                else:
                    if obj.type == Contactable.PERSON:
                        p = Person.objects.get (pk = obj_id)
                    elif obj.type == Contactable.MEMBER:
                        m = Member.objects.get (pk = obj_id)
                        p = Person.objects.get (pk = m.person)
                    else:
                        p = None

                    if p:
                        append_person (people, p, (c,))
        else:
            p_list = list (search_people (keywords))[:30]
            o_list = list (search_orgs (keywords))[:30]

            for p in p_list:
                c = Contact.objects.filter (obj = p)
                if c.count () == 0:
                    m = Member.objects.filter (person = p)
                    if m.count () > 0:
                        c = Contact.objects.filter (obj = m[0])

                append_person (people, p, c)

            for o in o_list:
                c = Contact.objects.filter (obj = o)
                if c.count () == 0:
                    m = Member.objects.filter (organisation = o)
                    if m.count () > 0:
                        c = Contact.objects.filter (obj = m[0])

                append_org (orgs, o, c)

        results = PaginatorStub ()
        results.add_list (people, 'person')
        results.add_list (orgs, 'org')
        results.limit_list (40)
    else:
        results = None

    tpl_vars['form'] = ctx.form
    tpl_vars['page'] = results

    return render_to_response ('abook/search.html', tpl_vars)

@login_required
def person (request, person_id):
    person = get_object_or_404 (Person, pk = person_id)
    contacts = Contact.objects.filter (obj = person)
    members = Member.objects.filter (person = person)
    members = members.filter (status = Record.ACTIVE)
    ctx = SearchHelper (request)
    tpl_vars = {'person': person, 'contacts': contacts, 'members': members,
                'url': 'abook/person/%d/' % person.id}
    add_common_tpl_vars_abook (request, tpl_vars, ctx, members, 10)
    return render_to_response ('abook/person.html', tpl_vars)

@login_required
def org (request, org_id):
    org = get_object_or_404 (Organisation, pk = org_id)
    contacts = Contact.objects.filter (obj = org)
    members = Member.objects.filter (organisation = org)
    members = members.filter (status = Record.ACTIVE)
    ctx = SearchHelper (request)
    tpl_vars = {'org': org, 'contacts': contacts, 'members': members,
                'url': 'abook/org/%d/' % org.id}
    add_common_tpl_vars_abook (request, tpl_vars, ctx, members, 10)
    return render_to_response ('abook/org.html', tpl_vars)

