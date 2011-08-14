from urllib import urlencode
from django import forms
from django.db.models.query import Q
from django.shortcuts import get_object_or_404
from cams.libcams import str2list
from cams.models import (Record, Contactable, Person, Organisation, Member,
                         Contact)
from mrwf.extra.views.main import SiteView, get_list_page

class SearchHelper(object):
    def __init__(self, request):
        self.form = SearchHelper.SearchForm(request.GET)
        if self.form.is_valid():
            self.match = self.form.cleaned_data['match']
            self.opt_contacts = self.form.cleaned_data['opt_contacts']
            self.urlmatch = urlencode((('match', self.match),
                                       ('opt_contacts',
                                        self.opt_contacts)))
        else:
            self.match = ''
            self.urlmatch = ''
            self.opt_contacts = False

    class SearchForm(forms.Form):
        match = forms.CharField(required=True, max_length=64)
        opt_contacts = forms.BooleanField(required = False,
                                          label = "search within contacts")


def search_people(keywords):
    people = Person.objects.all()

    for kw in keywords:
        people = people.filter(Q(first_name__icontains=kw) |
                               Q(middle_name__icontains=kw) |
                               Q(last_name__icontains=kw) |
                               Q(nickname__icontains=kw))

    return people.filter(status=Record.ACTIVE)

def search_orgs(keywords):
    orgs = Organisation.objects.all()

    for kw in keywords:
        orgs = orgs.filter(Q(name__icontains=kw) |
                           Q(nickname__icontains=kw))

    return orgs.filter(status=Record.ACTIVE)

def search_contacts(keywords):
    contacts = Contact.objects.all()

    for kw in keywords:
        contacts = contacts.filter(Q(line_1__icontains=kw) |
                                   Q(line_2__icontains=kw) |
                                   Q(line_3__icontains=kw) |
                                   Q(town__icontains=kw) |
                                   Q(postcode__icontains=kw) |
                                   Q(country__icontains=kw) |
                                   Q(email__icontains=kw) |
                                   Q(website__icontains=kw) |
                                   Q(telephone__icontains= kw) |
                                   Q(mobile__icontains=kw) |
                                   Q(fax__icontains=kw) |
                                   Q(addr_order__icontains=kw) |
                                   Q(addr_suborder__icontains=kw))

    return contacts.filter(status=Record.ACTIVE)

class AbookView(SiteView):
    title = 'Address Book'
    menu_name = 'abook'

    def get(self, request, *args, **kwargs):
        self.form = SearchHelper.SearchForm(request.GET)
        if self.form.is_valid():
            self.match = self.form.cleaned_data['match']
            self.opt_contacts = self.form.cleaned_data['opt_contacts']
            self.urlmatch = urlencode((('match', self.match),
                                       ('opt_contacts',
                                        self.opt_contacts)))
        else:
            self.match = ''
            self.opt_contacts = False
            self.urlmatch = ''

        return super(AbookView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(AbookView, self).get_context_data(**kwargs)
        ctx['urlmatch'] = self.urlmatch
        return ctx

    class SearchForm(forms.Form):
        match = forms.CharField(required=True, max_length=64)
        opt_contacts = forms.BooleanField(required=False,
                                          label="search within contacts")

# -----------------------------------------------------------------------------
# entry points from url's

class SearchView(AbookView):
    template_name = 'abook/search.html'

    def get_context_data(self, **kwargs):
        ctx = super(SearchView, self).get_context_data(**kwargs)
        self.search = SearchHelper(self.request)

        if self.search.match:
            self.set_search_results()
        else:
            self.results = None

        ctx.update({'form': self.search.form, 'page': self.results})
        return ctx

    def set_search_results(self):
        keywords = str2list(self.search.match)
        self._people = []
        self._orgs = []

        if self.search.opt_contacts:
            self._search_in_contacts(keywords)
        else:
            self._search_in_names(keywords)

        self.results = SearchView.PaginatorStub()
        self.results.add_list(self._people, 'person')
        self.results.add_list(self._orgs, 'org')
        self.results.limit_list(40)

    def _search_in_names(self, keywords):
        p_list = list(search_people(keywords))[:30]
        o_list = list(search_orgs(keywords))[:30]

        for p in p_list:
            c = p.contact_set.all()
            if c.count() == 0:
                m = Member.objects.filter(person = p)
                if m.count() > 0:
                    c = m[0].contact_set.all()
            self._append_person(p, c)

        for o in o_list:
            c = o.contact_set.all()
            if c.count() == 0:
                m = Member.objects.filter(organisation = o)
                if m.count() > 0:
                    c = m[0].contact_set.all()
            self._append_org(o, c)

    def _search_in_contacts(self, keywords):
        # Note: There may be several matching contacts related to the same
        # person/org, so that person/org will be in the results several
        # times (with a different contact preview though)
        contacts = list(search_contacts(keywords))[:40]
        for c in contacts:
            obj = Contactable.objects.get(pk=c.obj_id)
            # ToDo: transform (cast) a Contactable to its subclass...
            if obj.type == Contactable.ORGANISATION:
                # ToDo: check whether that reads the Contactable data again
                self._append_org(obj.organisation, (c,))
            elif obj.type == Contactable.PERSON:
                self._append_person(obj.person, (c,))
            elif obj.type == Contactable.MEMBER:
                self._append_person(obj.member.person, (c,))
            else:
                pass # ToDo: throw exception

    def _append_person(self, p, c):
        self._people.append({'first_name': p.first_name,
                             'middle_name': p.middle_name,
                             'last_name': p.last_name,
                             'nickname': p.nickname,
                             'id': p.id,
                             'contacts': c})

    def _append_org(self, o, c):
        self._orgs.append({'name': o.name,
                           'nickname': o.nickname,
                           'id': o.id,
                           'contacts': c})

    class PaginatorStub(object):
        def __init__(self):
            self.object_list = []

        def add_list(self, items, type_name):
            for it in items:
                it['type'] = type_name
            self.object_list += items

        def limit_list(self, max_objects):
            if len(self.object_list) > max_objects:
                self.object_list = self.object_list[:max_objects]

        @property
        def num_pages(self):
            if len(self.object_list):
                return 1
            else:
                return 0


class PersonView(AbookView):
    template_name = 'abook/person.html'

    def get_context_data(self, **kwargs):
        ctx = super(PersonView, self).get_context_data(**kwargs)
        person = get_object_or_404(Person, pk=kwargs['person_id'])
        contacts = Contact.objects.filter(obj=person)
        members = Member.objects.filter(person=person)
        members = members.filter(status=Record.ACTIVE)
        ctx.update({'person': person,
                    'contacts': contacts,
                    'members': members,
                    'page': get_list_page(self.request, members, 10),
                    'url': 'abook/person/{:d}'.format(person.id)})
        return ctx

class OrgView(AbookView):
    template_name = 'abook/org.html'

    def get_context_data(self, **kwargs):
        ctx = super(OrgView, self).get_context_data(**kwargs)
        org = get_object_or_404(Organisation, pk=kwargs['org_id'])
        contacts = Contact.objects.filter(obj=org)
        members = Member.objects.filter(organisation=org)
        members = members.filter(status=Record.ACTIVE)
        ctx.update({'org': org,
                    'contacts': contacts,
                    'members': members,
                    'page': get_list_page(self.request, members, 10),
                    'url': 'abook/org/{:d}'.format(org.id)})
        return ctx
