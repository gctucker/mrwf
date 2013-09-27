# MRWF - extra/public/views/main.py
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

import logging
from sys import version_info
from smtplib import SMTPException
from django import get_version as get_django_version
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from cams import libcams
from cams.models import Person, Player
from mrwf.extra.forms import UserNameForm, PersonForm, ContactForm

def get_list_page(request, obj_list, n):
    pagin = Paginator(obj_list, n)

    if 'page' in request.GET:
        try:
            page_n = int(request.GET['page'])
        except ValueError:
            page_n = 1
    else:
        page_n = 1

    try:
        page = pagin.page(page_n)
    except (InvalidPage, EmptyPage):
        page = pagin.page(pagin.num_pages)

    return page

def make_menu():
    from mrwf.urls import urlpatterns as urls
    from mrwf.extra.abook_urls import urlpatterns as abook_urls
    from mrwf.extra.mgmt_urls import urlpatterns as mgmt_urls
    from cams.libcams import Menu

    m = Menu()
    m.add(urlpatterns=urls, items=[ \
            Menu.Item('home', 'welcome'),
            Menu.Item('profile', 'profile')])
    m.add(urlpatterns=abook_urls, namespace='abook', items=[ \
            Menu.Item('search', 'address book')])
    m.add(urlpatterns=mgmt_urls, items=[ \
            Menu.Item('groups'),
            Menu.Item('programme'),
            Menu.Item('applications'),
            Menu.Item('invoices')])
    m.add(namespace='admin', items=[ \
            Menu.StaffItem('index', 'admin')])
    m.add(items=[ \
            Menu.Item('logout', 'log out')])
    return m

def add_common_tpl_vars(request, tpl_vars, menu_name, obj_list=None, n=20):
    tpl_vars['px'] = settings.URL_PREFIX
    tpl_vars['user'] = request.user
    menu = make_menu()
    menu.set_current(menu_name)
    tpl_vars['menu'] = menu.get_user_items(request.user)

    if obj_list:
        page = get_list_page(request, obj_list, n)
        tpl_vars['page'] = page


class SiteView(TemplateView):
    perms = []

    def __init__(self, *args, **kwargs):
        super(SiteView, self).__init__(*args, **kwargs)
        self.history = libcams.HistoryLogger('cams.history', 'cams')
        self.log = logging.getLogger('cams')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        log_opts = [request.user.username, request.method, request.path]
        self._log(log_opts)
        if not self.check_perms(request.user):
            return HttpResponseForbidden("Access denied")
        return super(SiteView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(SiteView, self).get_context_data(**kwargs)
        menu = make_menu()
        menu.set_current(self.menu_name)
        ctx.update({'px': settings.URL_PREFIX,
                    'title': self.title,
                    'user': self.request.user,
                    'menu': menu.get_user_items(self.request.user)})
        return ctx

    def check_perms(self, user, perms=None):
        if not perms:
            perms = self.perms
        for p in perms:
            if not user.has_perm(p):
                return False
        return True

    def _set_list_page(self, ctx, obj_list, n=20):
        ctx['page'] = get_list_page(self.request, obj_list, n)

    def _log(self, opts):
        self.log.info(u' '.join(opts))


class PlayerMixin(object):
    @property
    def contacts(self):
        if not hasattr(self, '_contacts'):
            self._contacts = self.request.user.player.person.contact_set.all()
        return self._contacts

# -----------------------------------------------------------------------------
# entry points from url's

def login(request, *args, **kwargs):
    from django.contrib.auth.views import login as django_login
    resp = django_login(request, *args, **kwargs)
    log = logging.getLogger('cams')
    msg = ['login', request.method]
    if request.method == 'POST':
        msg.append(request.POST['username'])
        if request.user.is_authenticated():
            msg.append('OK')
            player = Player.objects.filter(user=request.user)
            if len(player) > 0:
                msg.append(player[0].__unicode__())
        else:
            msg.append('ERROR')
    log.info(u' '.join(msg))
    return resp

def logout(request, *args, **kwargs):
    log = logging.getLogger('cams')
    log.info(u' '.join(['logout', request.user.username]))
    from django.contrib.auth.views import logout as django_logout
    return django_logout(request, *args, **kwargs)


class HomeView(SiteView):
    template_name = 'home.html'
    title = 'Welcome'
    menu_name = 'home'


class ProfileView(SiteView, PlayerMixin):
    template_name = 'profile.html'
    title = 'User profile'
    menu_name = 'profile'

    def get(self, request, *args, **kwargs):
        player = Player.objects.filter(user=request.user)
        if len(player) == 0:
            person = Person()
            person.first_name = request.user.username.capitalize()
            person.save()
            p = Player()
            p.user = request.user
            p.person = person
            p.save()
            return HttpResponseRedirect(reverse('edit_profile'))
        return super(ProfileView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ProfileView, self).get_context_data(**kwargs)

        if self.contacts.count() > 0:
            ctx['contact'] = self.contacts[0]

        vstring = lambda ver: '.'.join([str(x) for x in ver])
        ctx.update({'python_version': vstring(version_info),
                    'django_version': get_django_version(),
                    'cams_version': vstring(libcams.CAMS_VERSION),
                    'person': self.request.user.player.person})
        return ctx


class ProfileEditView(SiteView, PlayerMixin):
    template_name = 'profile_edit.html'
    title = 'Edit profile'
    menu_name = 'profile'

    def get(self, request, *args, **kwargs):
        self._uf = UserNameForm(instance=request.user, prefix='user')
        self._pf = PersonForm(instance=request.user.player.person)

        if self.contacts.count() > 0:
            self._cf = ContactForm(instance=self.contacts[0])
        else:
            self._cf = ContactForm()

        return super(ProfileEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._uf = UserNameForm(request.POST, instance=request.user,
                                prefix='user')
        self._pf = PersonForm(request.POST,instance=request.user.player.person)

        # ToDo: move the logic to save contacts and delete empty ones into
        # the contactable model or form
        if self.contacts.count() > 0:
            self._cf = ContactForm(request.POST, instance=self.contacts[0])
            if self._cf.is_empty():
                self._cf.instance.delete()
                self._cf = None
        else:
            self._cf = ContactForm(request.POST)
            if self._cf.is_empty():
                self._cf = None
            else:
                self._cf.instance.obj = request.user.player.person

        if (self._uf.is_valid() and self._pf.is_valid() and
            (self._cf is None or self._cf.is_valid())):
            self._uf.save()
            self._pf.save()
            self.history.edit_form(self.request.user, self._pf)
            if self._cf is not None:
                self._cf.save()
                self.history.edit_form(self.request.user, self._cf)
            return HttpResponseRedirect(reverse('profile'))

        return super(ProfileEditView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ProfileEditView, self).get_context_data(**kwargs)
        ctx.update({'f_user': self._uf,
                    'c_form': self._cf,
                    'p_form': self._pf})
        return ctx


class PasswordEditView(SiteView):
    template_name = 'password.html'
    title = 'Change password'
    menu_name = 'profile'

    def get(self, request, *args, **kwargs):
        self._fpwd = PasswordChangeForm(request.user)
        return super(PasswordEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._fpwd = PasswordChangeForm(request.user, request.POST)

        if self._fpwd.is_valid():
            self._fpwd.save()
            return HttpResponseRedirect(reverse('profile'))

        return super(PasswordEditView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PasswordEditView, self).get_context_data(**kwargs)
        ctx.update({'f_pwd': self._fpwd})
        return ctx


class EmailTestView(SiteView):
    template_name = 'email_test.html'
    title = 'E-mail test'
    menu_name = 'profile'

    def get(self, request, *args, **kwargs):
        self._email = libcams.get_user_email(request.user)
        self._result = False
        self._err_str = None

        if self._email:
            try:
                send_mail("CAMS e-mail test",
                          "Your email is properly configured.",
                          "no-reply@mangoz.org", [self._email])
                self._result = True
            except SMTPException, e:
                self._err_str = str(e)

        return super(EmailTestView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(EmailTestView, self).get_context_data(**kwargs)
        ctx.update({'result': self._result, 'email': self._email,
                    'error': self._err_str})
        return ctx
