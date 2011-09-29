import copy
from urllib import urlencode
from django import forms
from django.db.models.query import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from cams import libcams
from cams.models import (Record, Contactable, Person, Organisation, Member,
                         Contact)
from mrwf.extra.views.main import SiteView
from mrwf.extra.forms import (PersonForm, OrganisationForm, ContactForm,
                              ConfirmForm, StatusForm)

def reverse_ab(url, **kwargs):
    return reverse(':'.join(['abook', url]), **kwargs)

def obj_url(obj):
    return reverse_ab(obj.type_str, args=[obj.id])

def abook_classes():
    from django.contrib.auth.models import User
    from cams import models
    cls_list = [User, models.Person, models.Organisation, models.Member,
                models.Contact]
    classes = dict()
    for cls in cls_list:
        classes[cls.__name__] = cls
    return classes

class SearchHelper(object):
    def __init__(self, request):
        self.form = SearchHelper.SearchForm(request.GET)
        self._objs = []
        if self.form.is_valid():
            self._match = self.form.cleaned_data['match']
            self._keywords = libcams.str2list(self._match)
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
    def match_str(self):
        return self._match

    @property
    def urlmatch(self):
        return self._urlmatch

    @property
    def opt_disabled(self):
        return self._opt_disabled

    @property
    def objs(self):
        return self._objs

    @property
    def has_results(self):
        if self._objs:
            return True
        return False

    def do_search(self, search_p=True, search_o=True):
        if not self._match:
            return
        elif self._opt_contacts:
            self._search_in_contacts()
        else:
            self._search_in_names(search_p, search_o)

    def _search_in_names(self, search_p, search_o):
        obj_list = []
        if search_p:
            obj_list += list(self._search_people())[:30]
        if search_o:
            obj_list += list(self._search_orgs())[:30]
        for obj in obj_list:
            c = obj.contact_set.all()
            if c.count() == 0:
                m = obj.members_list.all()
                if m.count() > 0:
                    c = m[0].contact_set.all()
            self._append_obj(obj, c)

    def _search_in_contacts(self):
        # Note: There may be several matching contacts related to the same
        # person/org, so that person/org will be in the results several
        # times (with a different contact preview though)
        contacts = list(self._search_contacts())[:40]

        for c in contacts:
            if c.obj.type == Contactable.MEMBER:
                self._append_obj(c.obj.member.person, (c,))
            else:
                self._append_obj(c.obj.subobj, (c,))

    def _append_obj(self, obj, c):
        self._objs.append({'obj': obj, 'contacts': c})

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
    menu_name = 'abook:search'

    def dispatch(self, request, *args, **kwargs):
        self.search = SearchHelper(request)
        return super(AbookView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(AbookView, self).get_context_data(**kwargs)
        ctx['urlmatch'] = self.search.urlmatch
        return ctx


class AddView(AbookView):
    template_name = 'abook/add.html'
    perms = AbookView.perms + ['cams.abook_edit', 'cams.abook_add']

    def get(self, *args, **kwargs):
        self._objf = self._make_new_obj_form()
        self._stf = StatusForm()
        self._cf = ContactForm()
        return super(AddView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._objf = self._make_new_obj_form(self.request.POST)
        self._stf = StatusForm(self.request.POST)
        self._cf = ContactForm(self.request.POST)
        if self._objf.is_valid() and self._stf.is_valid() \
                and self._cf.is_valid():
            self._objf.instance.status = self._stf.cleaned_data['status']
            self._objf.save()
            f = self._objf.fields.keys() + self._stf.fields.keys()
            self.history.create(self.request.user, self._objf.instance, f)
            if not self._cf.is_empty():
                self._cf.instance.obj = self._objf.instance
                self._cf.save()
                self.history.create(self.request.user, self._cf.instance,
                                    self._cf.fields.keys() + ['obj'])
            return HttpResponseRedirect(self._get_details_url())
        return super(AddView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(AddView, self).get_context_data(**kwargs)
        ctx.update({'objf': self._objf, 'cf': self._cf, 'stf': self._stf,
                    'add_title': self.add_title, 'url': self._get_add_url()})
        return ctx

    def _get_details_url(self):
        return obj_url(self._objf.instance)

    def _get_add_url(self):
        type_str = Contactable.xtype[self.type_id][1]
        return reverse_ab('_'.join(['add', type_str]))


class BaseObjView(AbookView):
    def dispatch(self, request, *args, **kwargs):
        obj_id = int(kwargs['obj_id'])
        self.obj = get_object_or_404(Contactable, pk=obj_id).subobj
        return super(BaseObjView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(BaseObjView, self).get_context_data(**kwargs)
        ctx.update({'obj': self.obj, 'contacts': self.obj.contact_set.all()})
        return ctx

    def redirect(self, url):
        search = SearchHelper(self.request)
        if search.urlmatch:
            url = '?'.join([url, search.urlmatch])
        return HttpResponseRedirect(url)

    def check_perms(self, user):
        if self.obj.status == Record.NEW:
            perms = self.perms + ['cams.abook_edit']
        else:
            perms = self.perms
        return super(BaseObjView, self).check_perms(user, perms)

    def _log(self, opts):
        opts.append(self.obj.__unicode__())
        super(BaseObjView, self)._log(opts)


class ObjView(BaseObjView):
    def get_context_data(self, **kwargs):
        ctx = super(ObjView, self).get_context_data(**kwargs)
        q = Q(status=Record.ACTIVE)
        if self.obj.status == Record.DISABLED or self.search.opt_disabled:
            q = q | Q(status=Record.DISABLED)
        if self.request.user.has_perm('cams.abook_edit'):
            q = q | Q(status=Record.NEW)
        members = self.members.filter(q)
        ctx.update({'members': members})
        self._set_list_page(ctx, members, 5)
        return ctx

    def get_template_names(self):
        return 'abook/{0}.html'.format(self.obj.type_str)


class BaseEditView(BaseObjView):
    perms = BaseObjView.perms + ['cams.abook_edit']

    def get(self, *args, **kwargs):
        self._cf = []
        for c in self.obj.contact_set.all():
            self._cf.append(ContactForm(instance=c))
        if not self._cf: # at least one contact in the form
            self._cf.append(ContactForm())
        return super(BaseEditView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._build_post_data()
        if self._is_post_data_valid():
            self._save_post_data()
            return self._redirect()
        return super(BaseEditView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(BaseEditView, self).get_context_data(**kwargs)
        ctx.update({'cf_list': self._cf})
        return ctx

    def _build_post_data(self):
        self._cf = []
        cf_valid = True
        for c in self.obj.contact_set.all():
            cf = ContactForm(self.request.POST, instance=c)
            if not cf.is_valid():
                cf_valid = False
            self._cf.append(cf)
        if not self._cf: # at least one contact in the form
            c = ContactForm(self.request.POST)
            if not c.is_empty():
                c.instance.obj = self.obj
                if not c.is_valid():
                    cf_valid = False
                self._cf.append(c)
        self._cf_valid = cf_valid

    def _is_post_data_valid(self):
        return self._cf_valid

    def _save_post_data(self, *args, **kwargs):
        for cf in self._cf:
            if cf.is_empty():
                self.history.delete(self.request.user, cf.instance)
                cf.instance.delete()
            elif cf.has_changed():
                cf.save()
                self.history.edit_form(self.request.user, cf)


class EditView(BaseEditView):
    template_name = 'abook/edit.html'

    def get(self, *args, **kwargs):
        self._objf = self.make_obj_form()
        return super(EditView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(EditView, self).get_context_data(**kwargs)
        ctx.update({'objf': self._objf})
        return ctx

    def _build_post_data(self):
        super(EditView, self)._build_post_data()
        self._objf = self.make_obj_form(self.request.POST)

    def _is_post_data_valid(self):
        if not super(EditView, self)._is_post_data_valid():
            return False
        return self._objf.is_valid()

    def _save_post_data(self):
        super(EditView, self)._save_post_data()
        if self._objf.has_changed():
            self._objf.save()
            self.history.edit_form(self.request.user, self._objf)

    def _redirect(self):
        return self.redirect(obj_url(self._objf.instance))


class StatusEditView(BaseObjView):
    template_name = 'abook/status-edit.html'
    perms = ObjView.perms + ['cams.abook_edit']

    def get(self, *args, **kwargs):
        self._form = ConfirmForm()
        return super(StatusEditView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._form = ConfirmForm(self.request.POST)
        if self._form.is_valid():
            self._edit_obj_status()
            return self._redirect()
        return super(StatusEditView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(StatusEditView, self).get_context_data(**kwargs)
        ctx.update({'form': self._form, 'action': self.action,
                    'cmd': self.status_edit_cmd})
        return ctx

    def _redirect(self):
        return self.redirect(reverse_ab('search'))


class ActivateView(StatusEditView):
    action = "Activate entry"
    status_edit_cmd = "activate"
    perms = ObjView.perms + ['cams.abook_edit']

    def _edit_obj_status(self):
        self.obj.status = Record.ACTIVE;
        self.obj.save()
        self.history.edit(self.request.user, self.obj, ['status'])


class DisableView(StatusEditView):
    action = "Disable entry"
    status_edit_cmd = 'disable'

    def _edit_obj_status(self):
        self.obj.status = Record.DISABLED;
        self.obj.save()
        self.history.edit(self.request.user, self.obj, ['status'])


class DeleteView(StatusEditView):
    action = "Delete entry"
    status_edit_cmd = 'delete'
    perms = StatusEditView.perms + ['cams.abook_delete']

    def _edit_obj_status(self):
        self.history.delete(self.request.user, self.obj)
        self.obj.delete()


class ChooseMemberView(BaseObjView):
    template_name = 'abook/choose-member.html'
    perms = BaseObjView.perms + ['cams.abook_edit', 'cams.abook_add']

    def get_context_data(self, *args, **kw):
        ctx = super(ChooseMemberView, self).get_context_data(*args, **kw)
        self._do_search() # ToDo: exclude existing members
        if self.search.has_results:
            results = SearchView.PaginatorStub(self.search.objs)
            results.limit_list(40)
        else:
            results = None
        ctx.update({'form': self.search.form, 'other_type': self.other_type,
                    'page': results})
        return ctx


class SaveMemberView(BaseObjView):
    template_name = 'abook/save-member.html'
    perms = BaseObjView.perms + ['cams.abook_edit', 'cams.abook_add']

    def dispatch(self, request, *args, **kw):
        member_obj_id = int(request.GET['member_obj_id'])
        self.member_obj = get_object_or_404(Contactable, pk=member_obj_id)
        return super(SaveMemberView, self).dispatch(request, *args, **kw)

    def get(self, *args, **kwargs):
        self._cf = ContactForm()
        return super(SaveMemberView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._cf = ContactForm(self.request.POST)
        if self._cf.is_empty() or self._cf.is_valid():
            member = Member(person=self.person_obj, organisation=self.org_obj)
            member.save()
            self.history.create(self.request.user, member,
                                ['person', 'organisation'])
            if not self._cf.is_empty():
                self._cf.instance.obj = member
                self._cf.save()
                self.history.create(self.request.user, self._cf.instance,
                                    self._cf.fields.keys() + ['obj'])
            return HttpResponseRedirect(obj_url(self.obj))
        return super(SaveMemberView, self).get(*args, **kwargs)

    def get_context_data(self, *args, **kw):
        ctx = super(SaveMemberView, self).get_context_data(*args, **kw)
        ctx.update({'member_obj': self.member_obj, 'cf': self._cf})
        return ctx


class PersonMixin(object):
    @property
    def members(self):
        return self.obj.members_list.order_by('organisation__name')

    def make_obj_form(self, post=None):
        return PersonForm(post, instance=self.obj)


class OrgMixin(object):
    @property
    def members(self):
        return self.obj.members_list.order_by('person__last_name')

    def make_obj_form(self, post=None):
        return OrganisationForm(post, instance=self.obj)

# -----------------------------------------------------------------------------
# entry points from URL's

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

        n_new = Contactable.objects.filter(status=Record.NEW).count()
        ctx.update({'form': self.search.form, 'page': results, 'n_new': n_new})
        return ctx

    def _log(self, opts):
        opts.append(u'search: {}'.format(self.search.match_str))
        super(SearchView, self)._log(opts)

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


class BrowseNewView(AbookView):
    template_name = 'abook/browse_new.html'
    perms = AbookView.perms + ['cams.abook_edit']

    def get_context_data(self, **kwargs):
        ctx = super(BrowseNewView, self).get_context_data(**kwargs)
        new_entries = Contactable.objects.filter(status=Record.NEW)
        new_entries = new_entries.order_by('-created')
        self._set_list_page(ctx, new_entries)
        return ctx


class PersonAddView(AddView):
    add_title = 'a person'
    type_id = Contactable.PERSON

    def _make_new_obj_form(self, post=None):
        return PersonForm(post)

class PersonView(ObjView, PersonMixin):
    pass

class PersonEditView(EditView, PersonMixin):
    pass

class PersonActivateView(ActivateView, PersonMixin):
    pass

class PersonDisableView(DisableView, PersonMixin):
    pass

class PersonDeleteView(DeleteView, PersonMixin):
    pass

class PersonChooseMemberView(ChooseMemberView):
    def _do_search(self):
        self.search.do_search(search_p=False, search_o=True)

    @property
    def other_type(self):
        return Contactable.xtype[Contactable.ORGANISATION][1]

class PersonSaveMemberView(SaveMemberView):
    @property
    def person_obj(self):
        return self.obj.person

    @property
    def org_obj(self):
        return self.member_obj.organisation


class OrgAddView(AddView):
    add_title = 'an organisation'
    type_id = Contactable.ORGANISATION

    def _make_new_obj_form(self, post=None):
        return OrganisationForm(post)

class OrgView(ObjView, OrgMixin):
    pass

class OrgEditView(EditView, OrgMixin):
    pass

class OrgActivateView(ActivateView, OrgMixin):
    pass

class OrgDisableView(DisableView, OrgMixin):
    pass

class OrgDeleteView(DeleteView, OrgMixin):
    pass

class OrgChooseMemberView(ChooseMemberView):
    def _do_search(self):
        self.search.do_search(search_p=True, search_o=False)

    @property
    def other_type(self):
        return Contactable.xtype[Contactable.PERSON][1]

class OrgSaveMemberView(SaveMemberView):
    @property
    def person_obj(self):
        return self.member_obj.person

    @property
    def org_obj(self):
        return self.obj.organisation


class MemberEditView(BaseEditView):
    template_name = 'abook/edit-member.html'

    def dispatch(self, request, *args, **kwargs):
        src_obj_id = int(request.GET['src_obj_id'])
        self.src_obj = get_object_or_404(Contactable, pk=src_obj_id)
        return super(MemberEditView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(MemberEditView, self).get_context_data(*args, **kwargs)
        ctx.update({'src_obj': self.src_obj})
        return ctx

    def _redirect(self):
        return self.redirect(obj_url(self.src_obj))

class MemberRemoveView(DeleteView):
    template_name = 'abook/member-status-edit.html'

    def dispatch(self, request, *args, **kw):
        src_obj_id = int(request.GET['src_obj_id'])
        self.src_obj = get_object_or_404(Contactable, pk=src_obj_id)
        return super(MemberRemoveView, self).dispatch(request, *args, **kw)

    def get_context_data(self, *args, **kwargs):
        ctx = super(MemberRemoveView, self).get_context_data(*args, **kwargs)
        ctx.update({'src_obj': self.src_obj})
        return ctx

    def _redirect(self):
        return self.redirect(obj_url(self.src_obj))


class HistoryView(AbookView):
    template_name = 'abook/history.html'
    title = 'History'
    menu_name = 'abook:search'

    def get_context_data(self, *args, **kwargs):
        ctx = super(HistoryView, self).get_context_data(*args, **kwargs)
        h = libcams.HistoryParser(settings.HISTORY_PATH, abook_classes())
        self._set_list_page(ctx, self._abook_history(h), 50)
        return ctx

    def _abook_history(self, hist):
        abook = []

        def get_contact_obj(obj):
            subobj = obj.obj.subobj
            arg_str = ['contact']
            if isinstance(subobj, Member):
                subobj = subobj.person
                arg_str.append('member')
            return subobj, arg_str

        def get_member_obj(obj):
            return obj.person, ['member']

        filters = {Contact: get_contact_obj, Member: get_member_obj}

        for it in hist.data:
            if it.obj.__class__ not in (Person, Organisation, Contact, Member):
                continue
            fil = filters.get(it.obj.__class__, None)
            if fil:
                it = copy.copy(it)
                it.obj, arg_str = fil(it.obj)
                it.args = ': '.join([it.action.lower()] + arg_str)
                it.action = 'EDIT'
                fil = filters.get(it.obj.__class__, None)
            abook.append(it)

        return abook


class ObjHistoryView(BaseObjView):
    template_name = 'abook/obj-history.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super(ObjHistoryView, self).get_context_data(*args, **kwargs)
        h = libcams.HistoryParser(settings.HISTORY_PATH, abook_classes())
        self._set_list_page(ctx, self._obj_history(h), 50)
        return ctx

    def _obj_history(self, hist):
        objs = [self.obj]
        objs += self.obj.members_list.all()
        objs += self.obj.contact_set.all()
        obj_hist = hist.get_obj_data(objs)
        for it in obj_hist:
            if isinstance(it.obj, Contactable):
                it.target = it.obj.type_str
            elif it.obj.__class__ == Contact:
                it.target = 'contact'
        return obj_hist
