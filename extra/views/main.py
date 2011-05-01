from sys import version_info
from smtplib import SMTPException
from django import get_version as get_django_version
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.edit import ProcessFormView, FormMixin
from cams.libcams import CAMS_VERSION, Page, get_user_pages
from cams.models import Contact, Player, get_user_email
from mrwf.extra.forms import UserNameForm, PersonForm, ContactForm

PAGE_LIST = [
    Page('home',    '',                   'welcome',      Page.COMMON),
    Page('profile', 'profile/',           'user profile', Page.COMMON),
    Page('abook',   'abook/',             'address book', Page.COMMON),
    Page('parts',   'cams/participant/',  'groups',       Page.COMMON),
#    Page('prep',    'cams/prep/',         'preparation',  Page.COMMON),
    Page('prog',    'cams/prog/',         'programme',    Page.COMMON),
    Page('appli',   'cams/application/',  'applications', Page.ADMIN),
    Page('invoice', 'cams/invoice/',      'invoices',     Page.ADMIN),
#    Page('fairs',   'cams/fair/',         'winter fairs', Page.COMMON),
    Page('admin',   'admin/',             'admin',        Page.ADMIN),
    Page('logout',  'accounts/logout/',   'log out',      Page.COMMON)]

# Note: this is about list pagination, not site pages...
# ToDo: rename to remove ambiguity
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
    # ToDo: rename pages -> nav (avoid confusion with page in paginator)
    tpl_vars['pages'] = get_user_pages (PAGE_LIST, request.user)
    tpl_vars['current_page'] = cpage

    if obj_list:
        page = get_page (request, obj_list, n)
        tpl_vars['page'] = page

class SiteView(TemplateView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SiteView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(SiteView, self).get_context_data(**kwargs)
        ctx['px'] = settings.URL_PREFIX # ToDo: use {% url ... %} tag instead
        ctx['user'] = self.request.user
        ctx['pages'] = get_user_pages(PAGE_LIST, self.request.user)

        if self.title:
            ctx['page_title'] = self.title

        if self.page_name:
            ctx['current_page'] = self.page_name

        return ctx


class PlayerMixin(object):
    def set_player(self):
        self.player = get_object_or_404(Player, user=self.request.user)
        self.contacts = Contact.objects.filter(obj=self.player.person)


# -----------------------------------------------------------------------------
# entry points from url's

class HomeView(SiteView):
    template_name = 'home.html'
    title = 'Home'
    page_name = 'home'


class ProfileView(SiteView, PlayerMixin):
    template_name = 'profile.html'
    title = 'User profile'
    page_name = 'profile'

    def get_context_data(self, **kwargs):
        ctx = super(ProfileView, self).get_context_data(**kwargs)
        self.set_player()

        if self.contacts.count() > 0:
            ctx['contact'] = self.contacts[0]

        vstring = lambda v: 'v{:d}.{:d}.{:d}'.format(v[0], v[1], v[2])
        ctx.update({'python_version': vstring(version_info),
                    'django_version': get_django_version(),
                    'cams_version': vstring(CAMS_VERSION),
                    'person': self.player.person})
        return ctx


class ProfileEditView(SiteView, PlayerMixin):
    template_name = 'profile_edit.html'
    title = 'Edit user profile'
    page_name = 'profile'

    def get(self, request, *args, **kwargs):
        self.set_player()
        self._uf = UserNameForm(instance=self.request.user, prefix='user')
        self._pf = PersonForm(instance=self.player.person)

        if self.contacts.count() > 0:
            self._cf = ContactForm(instance=self.contacts[0])
        else:
            self._cf = ContactForm()

        return super(ProfileEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.set_player()
        self._uf = UserNameForm(self.request.POST, instance=self.request.user,
                                prefix='user')
        self._pf = PersonForm(self.request.POST, instance=self.player.person)

        if self.contacts.count() > 0:
            self._cf = ContactForm(self.request.POST,
                                   instance=self.contacts[0])
        else:
            self._cf = ContactForm(self.request.POST)
            self._cf.instance.person = self.player.person

        if self._uf.is_valid() and self._pf.is_valid() and self._cf.is_valid():
            self._uf.save()
            self._pf.save()
            self._cf.save()
            # ToDo: reverse('profile')
            return HttpResponseRedirect('/profile/')

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
    page_name = 'profile'

    def get(self, request, *args, **kwargs):
        self._fpwd = PasswordChangeForm(request.user)
        return super(PasswordEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._fpwd = PasswordChangeForm(request.user, request.POST)

        if self._fpwd.is_valid():
            self._fpwd.save()
            return HttpResponseRedirect('/profile/')

        return super(PasswordEditView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PasswordEditView, self).get_context_data(**kwargs)
        ctx.update({'f_pwd': self._fpwd})
        return ctx


class EmailTestView(SiteView):
    template_name = 'email_test.html'
    title = 'E-mail test'
    page_name = 'profile'

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
