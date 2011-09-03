from django import forms
from django.http import (HttpResponse, HttpResponseServerError,
                         HttpResponseRedirect)
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from cams.models import Record, Contact, Fair, Application, get_user_email
from mrwf.extra.models import (StallEvent, FairEventType, FairEventApplication,
                               Listener)
from mrwf.extra.forms import IsEmptyMixin, PersonForm, ContactForm, StallForm

class InvoicePersonForm(PersonForm):
    def __init__(self, *args, **kwargs):
        kwargs.update({'prefix': 'invoice'})
        super(InvoicePersonForm, self).__init__(*args, **kwargs)


class InvoiceContactForm(forms.ModelForm, IsEmptyMixin):
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

    def save (self, rcpts):
        # save personal details
        person = self.p.instance
        person.status = 0
        self.p.save ()

        # save contact details
        self.c.instance.status = 0
        self.c.instance.obj = person
        self.c.save ()

        # save invoice person
        if not self.ip.is_empty ():
            self.ip.instance.status = 0
            self.ip.save ()
            self.s.instance.invoice_person = self.ip.instance

        # save invoice contacts
        if not self.ic.is_empty ():
            self.ic.instance.status = 0
            if not self.ip.is_empty ():
                self.ic.instance.obj = self.ip.instance
            else:
                self.ic.instance.obj = self.p.instance
            self.ic.save ()
            self.s.instance.invoice_contact = self.ic.instance

        # save stall event
        self.s.instance.status = Record.NEW
        self.s.instance.owner = self.p.instance
        # ToDo: do not hard-code this (Market and Craft Stalls)
        self.s.instance.etype = FairEventType.objects.get(pk=1)
        self.s.save ()

        # save application
        ea = FairEventApplication ()
        ea.person = person
        ea.status = Application.PENDING
        ea.event = self.s.instance
        ea.subtype = FairEventApplication.STALLHOLDER
        ea.org_name = self.s.cleaned_data['org_name']
        ea.save ()

        stall = self.s.instance
        contact = self.c.instance

        if stall.main_contact == None:
            main_contact = 'none'
        elif stall.main_contact == StallEvent.TELEPHONE:
            main_contact = 'telephone'
        elif stall.main_contact == StallEvent.EMAIL:
            main_contact = 'email'
        elif stall.main_contact == StallEvent.WEBSITE:
            main_contact = 'website'
        else:
            main_contact = "unknown (%d)" % stall.main_contact

        if rcpts:
            subject = "Stallholder application - %s" % person
            msg = "Date:         %s\n" % ea.created
            msg += "Person:       %s\n" % person
            msg += "Line 1:       %s\n" % contact.line_1
            msg += "Line 2:       %s\n" % contact.line_2
            msg += "Line 3:       %s\n" % contact.line_3
            msg += "Town:         %s\n" % contact.town
            msg += "Postcode:     %s\n" % contact.postcode
            msg += "E-mail:       %s\n" % contact.email
            msg += "Website:      %s\n" % contact.website
            msg += "Telephone:    %s\n" % contact.telephone
            msg += "Mobile:       %s\n" % contact.mobile
            msg += "Stall name:   %s\n" % stall.name
            msg += "Spaces:       %d\n" % stall.n_spaces
            msg += "Main contact: %s\n" % main_contact
            msg += "Description:  %s\n" % stall.description
            msg += "Comments:     %s\n" % stall.comments
            send_mail (subject, msg, "no-reply@mangoz.org", rcpts)

# -----------------------------------------------------------------------------

def post_error (msg):
    return HttpResponseServerError (msg, mimetype = 'text/plain')


def stallholder_form (request, form):
    tpl_vars = {'page_title': 'Stallholder Application',
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

    rcpts = []
    for l in Listener.objects.filter \
            (trigger=Listener.STALL_APPLICATION_RECEIVED):
        email = get_user_email (l.user)
        if email:
            rcpts.append (email)
    form.save (rcpts)
    return HttpResponseRedirect (reverse (application))


def stallholder (request):
    return stallholder_form (request, StallApplicationForm ())


def application (request):
    tpl_vars = {'page_title': 'Application', 'px': settings.URL_PREFIX}
    return render_to_response ('public/application.html', tpl_vars)
