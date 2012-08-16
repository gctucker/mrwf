from urllib import urlencode
from django import forms
from django.http import (HttpResponse, HttpResponseServerError,
                         HttpResponseRedirect)
from django.template import RequestContext, Context, loader as template_loader
from django.core.urlresolvers import reverse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from cams.libcams import get_user_email
from cams.models import Record, Contact, Fair, Application
from mrwf.extra.models import (StallEvent, FairEventApplication,
                               FairEventType, Listener)
from mrwf.extra.forms import (PersonForm, ApplicationContactForm as ContactForm,
                              StallForm)

class InvoicePersonForm(PersonForm):
    def __init__(self, *args, **kwargs):
        kwargs.update({'prefix': 'invoice'})
        super(InvoicePersonForm, self).__init__(*args, **kwargs)


class InvoiceContactForm(ContactForm):
    def __init__(self, *args, **kwargs):
        kwargs.update({'prefix': 'invoice'})
        super(InvoiceContactForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Contact
        fields = ['line_1', 'line_2', 'line_3', 'town', 'postcode', 'email']


class StallApplicationForm ():
    def __init__ (self, p = PersonForm (), c = ContactForm (),
                  ip = InvoicePersonForm (), ic = InvoiceContactForm (),
                  s = StallForm ()):
        self.p = p
        self.c = c
        self.ip = ip
        self.ic = ic
        self.s = s
        self._is_valid = None
        self._has_errors = None
        self._main_contact = None

    def is_valid (self):
        if self._is_valid is None:
            self._is_valid = \
                bool (self.p.is_valid () and self.c.is_valid () and
                      (self.ip.is_empty () or self.ip.is_valid ()) and
                      (self.ic.is_empty () or self.ic.is_valid ()) and
                      self.s.is_valid ())
        return self._is_valid

    def has_errors (self):
        if self._has_errors is None:
            self._has_errors = \
                bool (self.p.errors or self.c.errors or
                      (not self.ip.is_empty () and self.ip.errors) or
                      (not self.ic.is_empty () and self.ic.errors) or
                      self.s.errors)
        return self._has_errors

    def save (self):
        # save personal details
        self.p.instance.status = 0
        self.p.save ()

        # save contact details
        self.c.instance.status = 0
        self.c.instance.obj = self.person
        self.c.save ()

        # save invoice person
        if not self.ip.is_empty ():
            self.ip.instance.status = 0
            self.ip.save ()
            self.s.instance.invoice_person = self.invoice_person

        # save invoice contacts
        if not self.ic.is_empty ():
            self.ic.instance.status = 0
            if not self.ip.is_empty ():
                self.ic.instance.obj = self.invoice_person
            else:
                self.ic.instance.obj = self.person
            self.ic.save ()
            self.s.instance.invoice_contact = self.invoice_contact

        # save stall event
        self.s.instance.status = Record.NEW
        self.s.instance.owner = self.person
        # ToDo: do not hard-code this (Market and Craft Stalls)
        MARKET_STALL_PK = 1
        FOOD_FAIR_PK = 2
        self.s.instance.etype = FairEventType.objects.get(pk=1)
        self.s.save ()

        # save application
        ea = FairEventApplication ()
        ea.person = self.person
        ea.status = Application.PENDING
        ea.event = self.stall
        ea.subtype = FairEventApplication.STALLHOLDER
        ea.org_name = self.s.cleaned_data['org_name']
        ea.save ()
        self._ea = ea

    def send_admin_notification(self, rcpts):
        stall = self.stall
        contact = self.contact

        if rcpts:
            subject = u"Stallholder application - %s" % self.person
            msg  = u"Date:           %s\n" % self.application.created
            msg += u"Person:         %s\n" % self.person
            msg += u"Line 1:         %s\n" % contact.line_1
            msg += u"Line 2:         %s\n" % contact.line_2
            msg += u"Line 3:         %s\n" % contact.line_3
            msg += u"Town:           %s\n" % contact.town
            msg += u"Postcode:       %s\n" % contact.postcode
            msg += u"E-mail:         %s\n" % contact.email
            msg += u"Website:        %s\n" % contact.website
            msg += u"Telephone:      %s\n" % contact.telephone
            msg += u"Mobile:         %s\n" % contact.mobile
            msg += u"Organisation:   %s\n" % self._ea.org_name
            msg += u"Stall name:     %s\n" % stall.name
            msg += u"Main contact:   %s\n" % self.main_contact
            msg += u"Media usage:    %s\n" % stall.media_usage
            msg += u"Description:    %s\n" % stall.description.strip()
            msg += u"Comments:       %s\n" % stall.comments
            msg += u"Spaces:         %d\n" % stall.n_spaces
            msg += u"Plot:           %s\n" % stall.plot_type_str
            msg += u"Infrastructure: %s\n" % stall.infrastructure
            msg += u"Tombola gift:   %s\n" % stall.tombola_gift
            msg += u"Prize:          %s\n" % stall.tombola_description
            send_mail (subject, msg, "no-reply@mangoz.org", rcpts)

    def send_confirmation(self, rcpts):
        ctx = Context({'title': 'Thank you', 'form': self, 'ea': self._ea,
                       'fair': Fair.get_current()})
        tpl_txt = template_loader.get_template('public/thank-you-email.txt')
        tpl_html = template_loader.get_template('public/thank-you-email.html')
        subject = "MRWF - Stallholder application"
        from_email = "stalls@millroadwinterfair.org"
        text = tpl_txt.render(ctx)
        html = tpl_html.render(ctx)
        email = EmailMultiAlternatives(subject, text, from_email, rcpts)
        email.attach_alternative(html, 'text/html')
        email.send()

    @property
    def main_contact(self):
        if self._main_contact is None:
            stall = self.stall
            if stall.main_contact == StallEvent.TELEPHONE:
                self._main_contact = \
                    'telephone: {}'.format(self.contact.telephone)
            elif stall.main_contact == StallEvent.EMAIL:
                self._main_contact = \
                    'email: {}'.format(self.contact.email)
            elif stall.main_contact == StallEvent.WEBSITE:
                self._main_contact = \
                    'website: {}'.format(self.contact.website)
            else:
                self._main_contact = 'none'
        return self._main_contact

    @property
    def person(self):
        return self.p.instance

    @property
    def stall(self):
        return self.s.instance

    @property
    def contact(self):
        return self.c.instance

    @property
    def invoice_person(self):
        return self.ip.instance

    @property
    def invoice_contact(self):
        return self.ic.instance

    @property
    def application(self):
        return self._ea

    @property
    def has_invoice_person(self):
        return not self.ip.is_empty()

    @property
    def has_invoice_contact(self):
        return not self.ic.is_empty()

# -----------------------------------------------------------------------------

def post_error (msg):
    return HttpResponseServerError (msg, mimetype = 'text/plain')


def stallholder_form (request, form):
    tpl_vars = {'title': 'Stallholder Application',
                'px': settings.URL_PREFIX, 'form': form,
                'fair': Fair.get_current()}
    return render_to_response ('public/apply.html', tpl_vars,
                               context_instance = RequestContext (request))

# -----------------------------------------------------------------------------

def post (request):
    if request.method != 'POST':
        return post_error ("ERROR: %s instead of POST" % request.method)

    form = StallApplicationForm (PersonForm (request.POST),
                                 ContactForm (request.POST),
                                 InvoicePersonForm (request.POST),
                                 InvoiceContactForm (request.POST),
                                 StallForm (request.POST))

    if not form.is_valid ():
        return stallholder_form (request, form)
    form.save()

    rcpts = []
    for l in Listener.objects.filter \
            (trigger=Listener.STALL_APPLICATION_RECEIVED):
        email = get_user_email (l.user)
        if email:
            rcpts.append (email)
    form.send_admin_notification(rcpts)
    email = str(form.c.instance.email)
    form.send_confirmation([email])
    url = '?'.join([reverse(thank_you), urlencode((('email', email),))])
    return HttpResponseRedirect (url)


def stallholder (request):
    return stallholder_form (request, StallApplicationForm ())


def thank_you (request):
    email = request.GET.get('email')
    tpl_vars = {'title': 'Thank you', 'px': settings.URL_PREFIX,
                'email': email}
    return render_to_response ('public/thank-you.html', tpl_vars)
