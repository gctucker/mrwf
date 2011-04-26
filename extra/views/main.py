from sys import version_info
from django import VERSION
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from cams.libcams import CAMS_VERSION, Page, get_user_pages
from cams.models import Contact, Player, get_user_email
from mrwf.extra.forms import UserNameForm, PersonForm, ContactForm

PAGE_LIST = [
    Page ('home',    '',                   'welcome',      Page.OPEN),
    Page ('profile', 'profile/',           'user profile', Page.OPEN),
    Page ('abook',   'abook/',             'address book', Page.OPEN),
    Page ('parts',   'cams/participant/',  'groups',       Page.OPEN),
#    Page ('prep',    'cams/prep/',         'preparation',  Page.OPEN),
    Page ('prog',    'cams/prog/',         'programme',    Page.OPEN),
    Page ('appli',   'cams/application/',  'applications', Page.ADMIN),
    Page ('invoice', 'cams/invoice/',      'invoices',     Page.ADMIN),
#    Page ('fairs',   'cams/fair/',         'winter fairs', Page.OPEN),
    Page ('admin',   'admin/',             'admin',        Page.ADMIN),
    Page ('logout',  'accounts/logout/',   'log out',      Page.OPEN)]


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

# -----------------------------------------------------------------------------
# entry points from url's

@login_required
def home (request):
    tpl_vars = {'page_title': 'Home'}
    add_common_tpl_vars (request, tpl_vars, 'home')
    return render_to_response ('home.html', tpl_vars)

@login_required
def profile (request):
    player = get_object_or_404 (Player, user = request.user)
    person = player.person
    contacts = Contact.objects.filter (obj = person)

    if contacts.count () > 0:
        c = contacts[0]
    else:
        c = None

    if request.user.is_staff:
        vstring = lambda v : 'v{:d}.{:d}.{:d}'.format(v[0], v[1], v[2])
        python_version = vstring(version_info)
        django_version = vstring(VERSION)
        cams_version = vstring(CAMS_VERSION)
    else:
        python_version = None
        django_version = None
        cams_version = None

    tpl_vars = {'page_title': 'User Profile', 'person': person, 'contact': c,
                'django_version': django_version, 'cams_version': cams_version,
                'python_version': python_version}
    add_common_tpl_vars (request, tpl_vars, 'profile')
    return render_to_response ('profile.html', tpl_vars)

@login_required
def profile_edit (request):
    player = get_object_or_404 (Player, user = request.user)
    person = player.person
    contacts = Contact.objects.filter (obj = person)

    if request.method == 'POST':
        u_form = UserNameForm (request.POST, instance = request.user,
                               prefix = 'user')
        p_form = PersonForm (request.POST, instance = person)

        if contacts.count () > 0:
            c_form = ContactForm (request.POST, instance = contacts[0])
        else:
            c_form = ContactForm (request.POST)
            c_form.instance.person = person

        if u_form.is_valid () and p_form.is_valid () and c_form.is_valid ():
            u_form.save ()
            p_form.save ()
            c_form.save ()
            return HttpResponseRedirect (reverse (profile))

    else:
        u_form = UserNameForm (instance = request.user, prefix = 'user')
        p_form = PersonForm (instance = person)

        if contacts.count () > 0:
            c_form = ContactForm (instance = contacts[0])
        else:
            c_form = ContactForm ()

    tpl_vars = {'page_title': 'User Profile', 'f_user': u_form,
                'c_form': c_form, 'p_form': p_form}

    add_common_tpl_vars (request, tpl_vars, 'profile')
    return render_to_response ('profile_edit.html', tpl_vars,
                               context_instance = RequestContext(request))

@login_required
def password (request):
    if request.method == 'POST':
        f_passwd = PasswordChangeForm (request.user, request.POST)

        if f_passwd.is_valid ():
            f_passwd.save ()
            return HttpResponseRedirect (reverse (profile))
    else:
        f_passwd = PasswordChangeForm (request.user)

    tpl_vars = {'page_title': 'Change password', 'f_passwd': f_passwd}
    add_common_tpl_vars (request, tpl_vars, 'profile')
    return render_to_response ('password.html', tpl_vars,
                               context_instance = RequestContext (request))

@login_required
def email_test (request):
    email = get_user_email (request.user)
    if email:
        try:
            send_mail ("CAMS e-mail test",
                       "Your email is properly configured.",
                       "no-reply@mangoz.org", [email])
            all_good = True
        except smtplib.SMTPException:
            all_good = False
    else:
        all_good = False

    tpl_vars = {'page_title': 'Email test', 'all_good': all_good,
                'email': email}
    add_common_tpl_vars (request, tpl_vars, 'profile')
    return render_to_response ('email_test.html', tpl_vars)
