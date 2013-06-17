# MRWF - extra/public/views/abook.py
#
# Copyright (C) 2009, 2010, 2011, 2012, 2013
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

import main, abook, mgmt
import copy
from urllib import urlencode
from django import forms
from django.forms.models import modelformset_factory
from django.db.models.query import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from cams import libcams
from cams.models import (Record, Contactable, Person, Organisation, Member,
                         Contact, Group, Role)
from mrwf.extra.views.main import SiteView
from mrwf.extra.forms import (PersonForm, OrganisationForm, ContactForm,
                              ConfirmForm, StatusForm)

def reverse_ab(url, **kwargs):
    return reverse(':'.join(['abook', url]), **kwargs)

def obj_url(obj, cmd=None):
    if cmd:
        url_name = '_'.join([cmd, obj.type_str])
    else:
        url_name = obj.type_str
    return reverse_ab(url_name, args=[obj.id])

def abook_classes():
    from django.contrib.auth.models import User
    from cams import models
    cls_list = [User, models.Person, models.Organisation, models.Member,
                models.Contact]
    classes = dict()
    for cls in cls_list:
        classes[cls.__name__] = cls
    return classes

def clone_obj(obj):
    new_obj = obj.__class__()
    for f in obj._meta.fields:
        setattr(new_obj, f.name, getattr(obj, f.name))
    return new_obj

def merge_obj(obj, new_obj):
    for f in obj._meta.fields:
        if not f.primary_key:
            new_obj_f = getattr(new_obj, f.name)
            if new_obj_f:
                setattr(obj, f.name, new_obj_f)

class SearchHelper(object):
    def __init__(self, request):
        self.form = SearchHelper.SearchForm(request.GET)
        self._objs = []
        if self.form.is_valid():
            self._match = self.form.cleaned_data['match']
            self._keywords = libcams.str2list(self._match)
            self._opt_reverse = self.form.cleaned_data['opt_reverse']
            self._opt_disabled = self.form.cleaned_data['opt_disabled']
            self._urlopt = (('match', self._match),
                            ('opt_reverse', self._opt_reverse),
                            ('opt_disabled', self._opt_disabled))
            self._urlmatch = urlencode(self._urlopt)
        else:
            self._match = ''
            self._keywords = []
            self._opt_reverse = False
            self._opt_disabled = False
            self._urlopt = tuple()
            self._urlmatch = ''

    @property
    def match_str(self):
        return self._match

    @property
    def urlopt(self):
        return self._urlopt

    @property
    def urlmatch(self):
        return self._urlmatch

    @property
    def opt_disabled(self):
        return self._opt_disabled

    @property
    def opt_reverse(self):
        return self._opt_reverse

    @property
    def objs(self):
        return self._objs

    @property
    def has_results(self):
        return True if self._objs else False

    def do_search(self, search_p=True, search_o=True):
        if not self._match:
            return
        elif self._opt_reverse:
            self._reverse_search()
        else:
            self.__search(search_p, search_o)

    def __search(self, search_p, search_o):
        search_q = Q()
        if search_p:
            search_q |= Q(type=Contactable.PERSON)
        if search_o:
            search_q |= Q(type=Contactable.ORGANISATION)
        objs = Contactable.objects.filter(search_q)
        status_q = Q(status=Record.ACTIVE)
        if self._opt_disabled:
            status_q = (status_q | Q(status=Record.DISABLED))
        objs = objs.filter(status_q)
        for kw in self._keywords:
            objs = objs.filter(basic_name__icontains=kw)
        self._objs = objs

    def _reverse_search(self):
        # Note: There may be several matching contacts related to the same
        # person/org, so that person/org will be in the results several
        # times (with a different contact preview though)

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
        self._objs = contacts.filter(tel_q | q).filter(status=Record.ACTIVE)

    class SearchForm(forms.Form):
        match = forms.CharField(required=True, max_length=64,
                                widget=forms.TextInput(attrs={'size':'40'}))
        opt_reverse = forms.BooleanField(required=False,
                                         label="reverse search")
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
        ctx['urlopt'] = self.search.urlopt
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
        src_obj_id = request.GET.get('src_obj_id', None)
        if src_obj_id:
            self.src_obj = get_object_or_404(Contactable, pk=int(src_obj_id))
        else:
            self.src_obj = None
        return super(BaseObjView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(BaseObjView, self).get_context_data(**kwargs)
        ctx.update({'obj': self.obj, 'contacts': self.obj.contact_set.all(),
                    'src_obj': self.src_obj})
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
        roles = self.obj.current_roles
        ctx.update({'members': members, 'roles': roles})
        self._set_list_page(ctx, members, 5)
        return ctx

    def get_template_names(self):
        return 'abook/{0}.html'.format(self.obj.type_str)


class BaseEditView(BaseObjView):
    perms = BaseObjView.perms + ['cams.abook_edit']

    def get(self, *args, **kwargs):
        self._cf = self._make_contact_forms()
        return super(BaseEditView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._build_post_data()
        if self._is_post_data_valid():
            self._save_post_data()
            return self.redirect()
        return super(BaseEditView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(BaseEditView, self).get_context_data(**kwargs)
        ctx.update({'cf_list': self._cf})
        return ctx

    def redirect(self):
        if self.src_obj:
            return super(BaseEditView, self).redirect(obj_url(self.src_obj))
        return super(BaseEditView, self).redirect(obj_url(self._objf.instance))

    def _build_post_data(self):
        self._cf = self._make_contact_forms(self.request.POST)

    def _is_post_data_valid(self):
        return self._cf.is_valid()

    def _save_post_data(self, force_save=False):
        for f in self._cf:
            if f.is_empty() and f.instance.pk:
                self.history.delete(self.request.user, f.instance)
                f.instance.delete()
            elif force_save or f.has_changed():
                f.save()
                self.history.edit_form(self.request.user, f)

    def _make_contact_forms(self, post=None):
        ContactFormSet = modelformset_factory(Contact, form=ContactForm)
        return ContactFormSet(post, queryset=self.obj.contact_set.all())


class EditView(BaseEditView):
    template_name = 'abook/edit.html'

    def get(self, *args, **kwargs):
        self._objf = self._make_obj_form()
        return super(EditView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(EditView, self).get_context_data(**kwargs)
        ctx.update({'objf': self._objf})
        return ctx

    def _build_post_data(self):
        super(EditView, self)._build_post_data()
        self._objf = self._make_obj_form(self.request.POST)

    def _is_post_data_valid(self):
        return (super(EditView, self)._is_post_data_valid()
                and self._objf.is_valid())

    def _save_post_data(self, force_save=False):
        super(EditView, self)._save_post_data(force_save)
        if force_save or self._objf.has_changed():
            self._objf.save()
            self._update_history()

    def _update_history(self):
        self.history.edit_form(self.request.user, self._objf)

    def _make_obj_form(self, post=None):
        return self.form_cls(post, instance=self.obj)


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
            return self.redirect()
        return super(StatusEditView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(StatusEditView, self).get_context_data(**kwargs)
        ctx.update({'form': self._form, 'action': self.action,
                    'cmd': self.status_edit_cmd})
        return ctx

    def redirect(self):
        return super(StatusEditView, self).redirect(reverse_ab('search'))


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


class ChooseMergeView(BaseObjView):
    template_name = 'abook/choose-merge.html'

    def get(self, *args, **kwargs):
        objs = self.obj.__class__.objects.filter(Q(status=Record.ACTIVE))
        q1 = Q()
        q2 = Q()
        for m in self.merge_search_fields:
            q_kw = dict()
            q_kw['{0}__icontains'.format(m)] = getattr(self.obj, m)
            q = Q(**q_kw)
            q1 &= q
            q2 |= q
        self._choice = list(objs.filter(q1)) + list(objs.filter(q2 & ~q1))
        return super(ChooseMergeView, self).get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(ChooseMergeView, self).get_context_data(*args, **kwargs)
        self._set_list_page(ctx, self._choice, 10)
        return ctx


class MergeView(EditView):
    template_name = 'abook/merge.html'

    def dispatch(self, request, *args, **kwargs):
        merge_id = int(kwargs['merge_id'])
        self._merge_obj = get_object_or_404(Contactable, pk=merge_id).subobj
        return super(EditView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        return super(MergeView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return super(MergeView, self).post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(MergeView, self).get_context_data(*args, **kwargs)
        ctx['merge_obj'] = self._merge_obj
        ctx['original_obj'] = self._original_obj
        ctx['details_template'] = 'abook/{0}-details.html'.format(
            self.obj.type_str)
        return ctx

    def redirect(self):
        return super(BaseEditView, self).redirect(obj_url(self.obj))

    def _make_obj_form(self, post=None):
        self._original_obj = clone_obj(self.obj)
        merge_obj(self.obj, self._merge_obj)
        return self.form_cls(post, instance=self.obj)

    def _make_contact_forms(self, post=None):
        # ToDo: expand to all contact entries
        new_c = clone_obj(self.obj.contact)
        merge_obj(new_c, self._merge_obj.contact)
        new_c.obj = self.obj
        ContactFormSet = modelformset_factory(
            Contact, form=ContactForm, extra=0)
        if post is not None:
            return ContactFormSet(post)
        else:
            data = {
                'form-TOTAL_FORMS': u'1',
                'form-INITIAL_FORMS': u'1',
                }
            for f in new_c._meta.fields:
                data['form-0-{0}'.format(f.name)] = getattr(new_c, f.name)
            return ContactFormSet(data)

    def _save_post_data(self):
        super(MergeView, self)._save_post_data(True)
        self._merge_obj.delete()

    def _update_history(self):
        self.history.edit_changed(self.request.user, self._original_obj,
                                  self._objf)


class ChooseMemberView(BaseObjView):
    template_name = 'abook/choose-member.html'
    perms = BaseObjView.perms + ['cams.abook_edit', 'cams.abook_add']

    def get_context_data(self, *args, **kw):
        ctx = super(ChooseMemberView, self).get_context_data(*args, **kw)
        self._do_search() # ToDo: exclude existing members
        ctx.update({'form': self.search.form, 'other_type': self.other_type})
        self._set_list_page(ctx, self.search.objs, 10)
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


class GroupsView(BaseObjView):
    template_name = 'abook/groups.html'
    perms = BaseObjView.perms
    RoleFormSet = modelformset_factory(
        Role, fields=('role',), can_delete=True, extra=0)

    class AddRoleForm(forms.Form):
        def __init__(self, obj, *args, **kw):
            super(GroupsView.AddRoleForm, self).__init__(*args, **kw)
            new_groups = Group.objects.filter(board__isnull=True)
            for r in obj.current_roles:
                new_groups = new_groups.exclude(pk=r.group.pk)
            self.fields['group'] = forms.ChoiceField(\
                choices=[(g.pk, g.__unicode__()) for g in new_groups])
            self.fields['role'] = forms.CharField(max_length=63,required=False)

    def get(self, *args, **kw):
        self._roles = GroupsView.RoleFormSet(queryset=self.obj.current_roles)
        self._add_form = GroupsView.AddRoleForm(self.obj)
        return super(GroupsView, self).get(*args, **kw)

    def post(self, *args, **kw):
        cmd = self.request.POST['cmd']
        if cmd == 'add':
            resp = self._add_role(*args, **kw)
        elif cmd == 'update':
            resp = self._update_roles(*args, **kw)
        else:
            resp = None
        if resp:
            return resp
        else:
            return super(GroupsView, self).get(*args, **kw)

    def _add_role(self, *args, **kw):
        self._roles = GroupsView.RoleFormSet(queryset=self.obj.current_roles)
        self._add_form = GroupsView.AddRoleForm(self.obj, self.request.POST)
        if not self._add_form.is_valid():
            return False
        group_id = int(self._add_form.cleaned_data['group'])
        group = Group.objects.get(pk=group_id)
        role_title = self._add_form.cleaned_data['role']
        role = Role(contactable=self.obj, group=group, role=role_title)
        role.save()
        self.history.create(self.request.user, role,
                            ['contactable', 'group', 'role'])
        return HttpResponseRedirect(obj_url(self.obj, 'groups'))

    def _update_roles(self, *args, **kw):
        self._add_form = GroupsView.AddRoleForm(self.obj)
        self._roles = GroupsView.RoleFormSet(self.request.POST,
                                             queryset=self.obj.current_roles)
        if not self._roles.is_valid():
            return False
        for f in self._roles.deleted_forms:
            self.history.delete(self.request.user, f.instance)
        for f in self._roles.forms:
            if f.changed_data and 'DELETE' not in f.changed_data:
                self.history.edit_form(self.request.user, f)
        self._roles.save()
        return HttpResponseRedirect(obj_url(self.obj))

    def get_context_data(self, *args, **kw):
        ctx = super(GroupsView, self).get_context_data(*args, **kw)
        form_empty = (len(self._add_form.fields['group'].choices) == 0)
        ctx.update({'add_form': self._add_form, 'form_empty': form_empty,
                    'roles_formset': self._roles})
        return ctx


class PersonMixin(object):
    merge_search_fields = ['first_name', 'last_name']
    form_cls = PersonForm

    @property
    def members(self):
        return self.obj.members_list.order_by('organisation__name')


class OrgMixin(object):
    merge_search_fields = ['name', 'nickname']
    form_cls = OrganisationForm

    @property
    def members(self):
        return self.obj.members_list.order_by('person__last_name')

# -----------------------------------------------------------------------------
# entry points from URL's

class SearchView(AbookView):
    template_name = 'abook/search.html'

    def get_context_data(self, **kwargs):
        ctx = super(SearchView, self).get_context_data(**kwargs)
        self.search.do_search()
        n_new = Contactable.objects.filter(status=Record.NEW).count()
        ctx.update({'form': self.search.form, 'n_new': n_new,
                    'reverse': self.search.opt_reverse})
        self._set_list_page(ctx, self.search.objs, 10)
        return ctx

    def _log(self, opts):
        opts.append(u'search: {}'.format(self.search.match_str))
        super(SearchView, self)._log(opts)


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

class PersonChooseMergeView(ChooseMergeView, PersonMixin):
    pass

class PersonMergeView(MergeView, PersonMixin):
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

class PersonGroupsView(GroupsView):
    pass


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

class OrgGroupsView(GroupsView):
    pass


class MemberEditView(BaseEditView):
    template_name = 'abook/edit-member.html'


class MemberRemoveView(DeleteView):
    template_name = 'abook/member-status-edit.html'

    def redirect(self):
        return super(StatusEditView, self).redirect(obj_url(self.src_obj))


class HistoryView(AbookView):
    template_name = 'abook/history.html'
    title = 'History'
    menu_name = 'abook:search'

    def get(self, request, *args, **kwargs):
        self._page_n = int(request.GET.get('page', 1))
        return super(HistoryView, self).get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(HistoryView, self).get_context_data(*args, **kwargs)
        h = libcams.HistoryParser(settings.HISTORY_PATH, abook_classes())
        n = 20
        ctx['page'] = self._abook_history(h, self._page_n, n)
        if len(ctx['page']) < n:
            ctx['last_page'] = True
        else:
            ctx['next_page'] = self._page_n + 1
        if self._page_n == 1:
            ctx['first_page'] = True
        else:
            ctx['prev_page'] = self._page_n - 1
        return ctx

    def _abook_history(self, hist, page_n, n):
        def get_contact_obj(obj):
            subobj = obj.obj.subobj
            arg_str = ['contact']
            if isinstance(subobj, Member):
                subobj = subobj.person
                arg_str.append('member')
            return subobj, arg_str

        def get_member_obj(obj):
            return obj.person, ['member']

        abook = []
        filters = {Contact: get_contact_obj, Member: get_member_obj}
        first = (page_n - 1) * n
        m = 0
        hist.open()
        for it in hist:
            if len(abook) == n:
                break
            if it.obj.__class__ not in (Person, Organisation, Contact, Member):
                continue
            m += 1
            if m <= first:
                continue
            fil = filters.get(it.obj.__class__, None)
            if fil:
                it = copy.copy(it)
                it.obj, arg_str = fil(it.obj)
                it.args = ': '.join([it.action.lower()] + arg_str)
                it.action = 'EDIT'
            abook.append(it)
        hist.close()

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
        members = self.obj.members_list.all()
        objs += members
        for m in members:
            objs += m.contact_set.all()
        obj_hist = list()
        objs += self.obj.contact_set.all()
        hist.open()
        for it in hist:
            if it.obj in objs:
                obj_hist.append(it)
        hist.close()
        for it in obj_hist:
            if isinstance(it.obj, Contactable):
                it.target = it.obj.type_str
            elif it.obj.__class__ == Contact:
                if isinstance(it.obj.obj.subobj, Member):
                    it.target = 'member contact'
                else:
                    it.target = 'contact'
        return obj_hist
