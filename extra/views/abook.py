from urllib import urlencode
from django import forms
from django.db.models.query import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.urlresolvers import reverse
from cams.libcams import str2list
from cams.models import (Record, Contactable, Person, Organisation, Member,
                         Contact)
from mrwf.extra.views.main import SiteView, get_list_page
from mrwf.extra.forms import (PersonForm, OrganisationForm, ContactForm,
                              ConfirmForm)

def reverse_ab(url, **kwargs):
    return reverse(':'.join(['abook', url]), **kwargs)

class SearchHelper(object):
    def __init__(self, request):
        self.form = SearchHelper.SearchForm(request.GET)
        self._objs = []
        if self.form.is_valid():
            self._match = self.form.cleaned_data['match']
            self._keywords = str2list(self._match)
            self._opt_contacts = self.form.cleaned_data['opt_contacts']
            self._opt_disabled = self.form.cleaned_data['opt_disabled']
            self._urlmatch = urlencode((('match', self._match),
                                        ('opt_contacts', self._opt_contacts),
                                        ('opt_disabled', self._opt_disabled)))
        else:
            self._match = ''
            self._keywords = []
            self._opt_contacts = False
            self._opt_disabled = False
            self._urlmatch = ''

    @property
    def urlmatch(self):
        return self._urlmatch

    @property
    def objs(self):
        return self._objs

    @property
    def has_results(self):
        if self._objs:
            return True
        return False

    def do_search(self):
        if not self._match:
            return
        elif self._opt_contacts:
            self._search_in_contacts()
        else:
            self._search_in_names()

    def _search_in_names(self):
        p_list = list(self._search_people())[:30]
        o_list = list(self._search_orgs())[:30]

        for p in p_list:
            c = p.contact_set.all()
            if c.count() == 0:
                m = Member.objects.filter(person = p)
                if m.count() > 0:
                    c = m[0].contact_set.all()
            self._append_obj(p, 'person', c)

        for o in o_list:
            c = o.contact_set.all()
            if c.count() == 0:
                m = Member.objects.filter(organisation = o)
                if m.count() > 0:
                    c = m[0].contact_set.all()
            self._append_obj(o, 'org', c)

    def _search_in_contacts(self):
        # Note: There may be several matching contacts related to the same
        # person/org, so that person/org will be in the results several
        # times (with a different contact preview though)
        contacts = list(self._search_contacts())[:40]

        for c in contacts:
            obj = Contactable.objects.get(pk=c.obj_id)
            # ToDo: transform (cast) a Contactable to its subclass...
            if obj.type == Contactable.ORGANISATION:
                # ToDo: check whether that reads the Contactable data again
                # when fetching the sub-class data
                self._append_obj(obj.organisation, 'org', (c,))
            elif obj.type == Contactable.PERSON:
                self._append_obj(obj.person, 'person', (c,))
            elif obj.type == Contactable.MEMBER:
                self._append_obj(obj.member.person, 'person', (c,))

    def _append_obj(self, obj, obj_type, c):
        self._objs.append({'obj': obj,
                           'type': obj_type,
                           'url': reverse_ab(obj_type, args=[obj.id]),
                           'contacts': c})

    def _search_people(self):
        people = Person.objects.all()
        for kw in self._keywords:
            people = people.filter(Q(first_name__icontains=kw) |
                                   Q(middle_name__icontains=kw) |
                                   Q(last_name__icontains=kw) |
                                   Q(nickname__icontains=kw))
        return self._filter_status(people)

    def _search_orgs(self):
        orgs = Organisation.objects.all()
        for kw in self._keywords:
            orgs = orgs.filter(Q(name__icontains=kw) |
                               Q(nickname__icontains=kw))
        return self._filter_status(orgs)

    def _search_contacts(self):
        contacts = Contact.objects.all()

        tel_re = None
        for c in self._match.strip():
            if c.isdigit():
                if tel_re:
                    tel_re = ''.join([tel_re, r'[^0-9]*', c])
                elif c != '0':
                    tel_re = c
        if tel_re:
            tel_q = (Q(telephone__regex=tel_re) |
                     Q(mobile__regex=tel_re) |
                     Q(fax__regex=tel_re))
        else:
            tel_q = Q()

        q = Q()
        for kw in self._keywords:
            q = (q & (Q(line_1__icontains=kw) |
                      Q(line_2__icontains=kw) |
                      Q(line_3__icontains=kw) |
                      Q(town__icontains=kw) |
                      Q(postcode__icontains=kw) |
                      Q(country__icontains=kw) |
                      Q(email__icontains=kw) |
                      Q(website__icontains=kw) |
                      Q(addr_order__icontains=kw)))

        # ToDo: handle disabled and new contact entries
        return contacts.filter(tel_q | q).filter(status=Record.ACTIVE)

    def _filter_status(self, qset):
        q = Q(status=Record.ACTIVE)
        if self._opt_disabled:
            q = (q | Q(status=Record.DISABLED))
        return qset.filter(q)

    class SearchForm(forms.Form):
        match = forms.CharField(required=True, max_length=64,
                                widget=forms.TextInput(attrs={'size':'40'}))
        opt_contacts = forms.BooleanField(required=False,
                                          label="look into contacts")
        opt_disabled = forms.BooleanField(required=False,
                                          label="show disabled entries")


class AbookView(SiteView):
    title = 'Address Book'
    menu_name = 'abook'

    def get(self, request, *args, **kwargs):
        self.search = SearchHelper(request)
        return super(AbookView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(AbookView, self).get_context_data(**kwargs)
        ctx['urlmatch'] = self.search.urlmatch
        return ctx


class AddView(AbookView):
    template_name = 'abook/add.html'
    perms = AbookView.perms + ['cams.abook_edit', 'cams.abook_add']

    def get(self, request, *args, **kwargs):
        self._objf = self._make_new_obj_form()
        self._cf = ContactForm()
        return super(AddView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._objf = self._make_new_obj_form(request.POST)
        self._cf = ContactForm(request.POST)
        if self._objf.is_valid() and self._cf.is_valid():
            self._objf.save()
            if not self._cf.is_empty:
                self._cf.instance.obj = self._objf.instance
                self._cf.save()
            return HttpResponseRedirect(self._get_search_url())
        return super(AddView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(AddView, self).get_context_data(**kwargs)
        ctx.update({'objf': self._objf, 'cf': self._cf,
                    'add_title': self.add_title, 'url': self._get_add_url()})
        return ctx

    def _get_search_url(self):
        return reverse_ab(self.obj_type, args=[self._objf.instance.id])

    def _get_add_url(self):
        return reverse_ab('_'.join(['add', self.obj_type]))


class ObjView(AbookView):
    def dispatch(self, *args, **kwargs):
        self.obj_id = kwargs['obj_id']
        return super(ObjView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ObjView, self).get_context_data(**kwargs)
        contacts = Contact.objects.filter(obj=self.obj)
        ctx.update({'url': self.url, 'obj': self.obj, 'contacts': contacts})
        return ctx

    def redirect(self, url, request):
        search = SearchHelper(request)
        if search.urlmatch:
            url = '?'.join([url, search.urlmatch])
        return HttpResponseRedirect(url)


class EditView(ObjView):
    template_name = 'abook/edit.html'
    perms = ObjView.perms + ['cams.abook_edit']

    def get(self, request, *args, **kwargs):
        self._objf = self.make_obj_form()
        self._cf = []
        for c in self.obj.contact_set.all():
            self._cf.append(ContactForm(instance=c))
        if not self._cf: # at least one contact in the form
            self._cf.append(ContactForm())
        return super(EditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._objf = self.make_obj_form(self.request.POST)
        self._cf = []
        cf_valid = True
        for c in self.obj.contact_set.all():
            cf = ContactForm(request.POST, instance=c)
            if not cf.is_valid():
                cf_valid = False
            self._cf.append(cf)
        if not self._cf: # at least one contact in the form
            c = ContactForm(request.POST)
            if not c.is_empty:
                c.instance.obj = self.obj
                if not c.is_valid():
                    cf_valid = False
                self._cf.append(c)
        if cf_valid and self._objf.is_valid():
            self._objf.save()
            for cf in self._cf:
                if cf.is_empty:
                    cf.instance.delete()
                else:
                    cf.save()
            return self.redirect(self.url, request)
        return super(EditView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(EditView, self).get_context_data(**kwargs)
        ctx.update({'objf': self._objf, 'cf_list': self._cf})
        return ctx


class RemoveView(ObjView):
    template_name = "abook/remove.html"
    perms = ObjView.perms + ['cams.abook_edit']

    def get(self, request, *args, **kwargs):
        self._form = ConfirmForm()
        return super(RemoveView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._form = ConfirmForm(self.request.POST)
        if self._form.is_valid():
            self.remove_obj()
            return self.redirect(reverse_ab('search'), request)
        return super(RemoveView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(RemoveView, self).get_context_data(**kwargs)
        ctx.update({'form': self._form, 'action': self.action,
                    'remove_cmd': self.remove_cmd})
        return ctx


class DisableView(RemoveView):
    action = "Disable entry"
    remove_cmd = 'disable'

    def remove_obj(self):
        self.obj.status = Record.DISABLED;
        self.obj.save()


class DeleteView(RemoveView):
    action = "Delete entry"
    remove_cmd = 'delete'
    perms = RemoveView.perms + ['cams.abook_delete']

    def remove_obj(self):
        self.obj.delete()


class PersonMixin(object):
    @property
    def obj(self):
        if not hasattr(self, '_person'):
            self._person = get_object_or_404(Person, pk=self.obj_id)
        return self._person

    @property
    def url(self):
        return reverse_ab('person', args=[self._person.id])

    def make_obj_form(self, post=None):
        return PersonForm(post, instance=self.obj)


class OrgMixin(object):
    @property
    def obj(self):
        if not hasattr(self, '_org'):
            self._org = get_object_or_404(Organisation, pk=self.obj_id)
        return self._org

    @property
    def url(self):
        return reverse_ab('org', args=[self._org.id])

    def make_obj_form(self, post=None):
        return OrganisationForm(post, instance=self.obj)

# -----------------------------------------------------------------------------
# entry points from url's

class SearchView(AbookView):
    template_name = 'abook/search.html'

    def get_context_data(self, **kwargs):
        ctx = super(SearchView, self).get_context_data(**kwargs)
        self.search.do_search()

        if self.search.has_results:
            results = SearchView.PaginatorStub(self.search.objs)
            results.limit_list(40)
        else:
            results = None

        ctx.update({'form': self.search.form, 'page': results})
        return ctx

    class PaginatorStub(object):
        def __init__(self, object_list=[]):
            self._object_list = object_list

        def limit_list(self, max_objects):
            if len(self._object_list) > max_objects:
                self._object_list = self._object_list[:max_objects]

        @property
        def num_pages(self):
            if len(self.object_list):
                return 1
            else:
                return 0

        @property
        def object_list(self):
            return self._object_list


class PersonView(ObjView, PersonMixin):
    template_name = 'abook/person.html'

    def get_context_data(self, **kwargs):
        ctx = super(PersonView, self).get_context_data(**kwargs)
        members = Member.objects.filter(person=self._person)
        members = members.filter(status=Record.ACTIVE)
        ctx.update({'members': members,
                    'page': get_list_page(self.request, members, 10)})
        return ctx


class PersonAddView(AddView):
    add_title = 'a person'
    obj_type = 'person'

    def _make_new_obj_form(self, post=None):
        return PersonForm(post)


class PersonEditView(EditView, PersonMixin):
    pass

class PersonDisableView(DisableView, PersonMixin):
    pass

class PersonDeleteView(DeleteView, PersonMixin):
    pass

class OrgView(ObjView, OrgMixin):
    template_name = 'abook/org.html'

    def get_context_data(self, **kwargs):
        ctx = super(OrgView, self).get_context_data(**kwargs)
        members = Member.objects.filter(organisation=self._org)
        members = members.filter(status=Record.ACTIVE)
        ctx.update({'members': members,
                    'page': get_list_page(self.request, members, 10)})
        return ctx


class OrgAddView(AddView):
    add_title = 'an organisation'
    obj_type = 'org'

    def _make_new_obj_form(self, post=None):
        return OrganisationForm(post)


class OrgEditView(EditView, OrgMixin):
    pass

class OrgDisableView(DisableView, OrgMixin):
    pass

class OrgDeleteView(DeleteView, OrgMixin):
    pass
