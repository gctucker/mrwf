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
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from cams.libcams import CAMS_VERSION, Menu, get_user_email
from mrwf.extra.forms import UserNameForm, PersonForm, ContactForm

MENU_ITEMS = [
    Menu.Item('home',    '',                 'welcome',      Menu.Item.COMMON),
    Menu.Item('profile', 'profile/',         'user profile', Menu.Item.COMMON),
    Menu.Item('abook',   'abook/',           'address book', Menu.Item.COMMON),
    Menu.Item('parts',   'cams/participant/','groups',       Menu.Item.COMMON),
#   Menu.Item('prep',    'cams/prep/',       'preparation',  Menu.Item.COMMON),
    Menu.Item('prog',    'cams/prog/',       'programme',    Menu.Item.COMMON),
    Menu.Item('appli',   'cams/application/','applications', Menu.Item.ADMIN),
    Menu.Item('invoice', 'cams/invoice/',    'invoices',     Menu.Item.ADMIN),
#   Menu.Item('fairs',   'cams/fair/',       'winter fairs', Menu.Item.COMMON),
    Menu.Item('admin',   'admin/',           'admin',        Menu.Item.ADMIN),
    Menu.Item('logout',  'accounts/logout/', 'log out',      Menu.Item.COMMON)]

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

def add_common_tpl_vars(request, tpl_vars, menu_name, obj_list=None, n=20):
    tpl_vars['px'] = settings.URL_PREFIX
    tpl_vars['user'] = request.user
    menu = Menu(MENU_ITEMS)
    menu.set_current(menu_name)
    tpl_vars['menu'] = menu.get_user_entries(request.user)

    if obj_list:
        page = get_list_page(request, obj_list, n)
        tpl_vars['page'] = page

class SiteView(TemplateView):
    perms = []

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_perms(request.user):
            return HttpResponseForbidden("Access denied")
        return super(SiteView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(SiteView, self).get_context_data(**kwargs)
        menu = Menu(MENU_ITEMS)
        menu.set_current(self.menu_name)
        ctx.update({'px': settings.URL_PREFIX,
                    'title': self.title,
                    'user': self.request.user,
                    'menu': menu.get_user_entries(self.request.user)})
        return ctx

    def check_perms(self, user):
        for p in self.perms:
            if not user.has_perm(p):
                return False
        return True

    def _set_list_page(self, ctx, obj_list, n=20):
        ctx['page'] = get_list_page(self.request, obj_list, n)


class PlayerMixin(object):
    @property
    def contacts(self):
        if not hasattr(self, '_contacts'):
            self._contacts = self.request.user.player.person.contact_set.all()
        return self._contacts

# -----------------------------------------------------------------------------
# entry points from url's

class HomeView(SiteView):
    template_name = 'home.html'
    title = 'Welcome'
    menu_name = 'home'


class ProfileView(SiteView, PlayerMixin):
    template_name = 'profile.html'
    title = 'User profile'
    menu_name = 'profile'

    def get_context_data(self, **kwargs):
        ctx = super(ProfileView, self).get_context_data(**kwargs)

        if self.contacts.count() > 0:
            ctx['contact'] = self.contacts[0]

        vstring = lambda v: 'v{:d}.{:d}.{:d}'.format(v[0], v[1], v[2])
        ctx.update({'python_version': vstring(version_info),
                    'django_version': get_django_version(),
                    'cams_version': vstring(CAMS_VERSION),
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

        if self.contacts.count() > 0:
            self._cf = ContactForm(request.POST,instance=self.contacts[0])
        else:
            self._cf = ContactForm(request.POST)
            self._cf.instance.person = request.user.player.person

        if self._uf.is_valid() and self._pf.is_valid() and self._cf.is_valid():
            self._uf.save()
            self._pf.save()
            self._cf.save()
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
        self._email = get_user_email(request.user)
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
