import urllib
from django import forms
from django.db.models.query import Q
from cams.models import (Record, Person, Organisation, Member, Contact)

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
