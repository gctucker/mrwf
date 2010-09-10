from django import forms
from django.http import (HttpResponse, HttpResponseServerError,
                         HttpResponseRedirect)
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from cams.models import (Person, Contact, PersonContact, Organisation,
                         Fair, Participant, get_user_email)
from mrwf.extra.models import StallEvent, StallApplication, Listener

class PersonForm (forms.ModelForm):
    last_name = forms.CharField (max_length = 127, required = True)

    class Meta:
        model = Person
        exclude = ['nickname', 'alter', 'status']


class PersonContactForm (forms.ModelForm):
    line_1 = forms.CharField (max_length = 63, required = True)
    town = forms.CharField (max_length = 63, required = True)
    postcode = forms.CharField (max_length = 15, required = True)
    email = forms.EmailField (max_length = 127, required = True,
                              help_text = Contact.email_help_text)

    class Meta:
        model = PersonContact
        exclude = ['status', 'person', 'addr_order', 'addr_suborder',
                   'country', 'fax']


def check_ibounds (data, name, imin, imax):
    try:
        val = int (data[name])

        if (val < imin) or (val > imax):
            raise forms.ValidationError (
                "Value out of bounds (min=%d, max=%d)" % (imin, imax))
        else:
            return val

    except ValueError:
        raise forms.ValidationError ("Invalid value for %s" % name)


class StallForm (forms.ModelForm):
    attrs = {'cols': '60', 'rows': '3'}
    description = forms.CharField (widget = forms.Textarea (attrs = attrs))

    class Meta:
        model = StallEvent
        fields = ('name', 'n_spaces', 'n_tables', 'main_contact',
                  'description')

    def clean_n_spaces (self):
        return check_ibounds (self.cleaned_data, 'n_spaces', 1, 3)

    def clean_n_tables (self):
        return check_ibounds (self.cleaned_data, 'n_tables', 0, 3)


class StallApplicationForm ():
    def __init__ (self, p = PersonForm (), c = PersonContactForm (),
                  s = StallForm ()):
        self.p = p
        self.c = c
        self.s = s

    def is_valid (self):
        return self.p.is_valid () and self.s.is_valid () and self.c.is_valid ()

    def save (self, rcpts):
        # save personal details
        self.p.instance.status = 0
        self.p.save ()

        # save contact details
        self.c.instance.status = 0
        self.c.instance.person = self.p.instance
        self.c.save ()

        # save participant
        part = Participant (person = self.p.instance)
        part.status = 0
        part.save ()

        # save stall event
        fair = get_object_or_404 (Fair, current = True)
        self.s.instance.status = 0
        self.s.instance.owner = part
        self.s.instance.date = fair.date
        self.s.save ()

        # save application
        sa = StallApplication (stall = self.s.instance)
        sa.participant = part
        sa.event = self.s.instance
        sa.save ()

        stall = self.s.instance
        contact = self.c.instance

        if stall.main_contact == None:
            main_contact = 'none'
        elif stall.main_contact == 0: # StallEvent.TELEPHONE
            main_contact = 'telephone'
        elif stall.main_contact == 1:
            main_contact = 'email'
        elif stall.main_contact == 2:
            main_contact = 'website'
        else:
            main_contact = "unknown (%d)" % stall.main_contact

        if rcpts:
            subject = "Stallholder application - %s" % part.person
            msg = "Date:         %s\n" % sa.created
            msg += "Person:       %s\n" % part.person
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
            msg += "Tables:       %d\n" % stall.n_tables
            msg += "Main contact: %s\n" % main_contact
            msg += "Description:  %s\n" % stall.description
            send_mail (subject, msg, "no-reply@mangoz.org", rcpts)

# -----------------------------------------------------------------------------

def post_error (msg):
    return HttpResponseServerError (msg, mimetype = 'text/plain')


def stallholder_form (request, form):
    tpl_vars = {'page_title': 'Stallholder Application',
                'px': settings.URL_PREFIX, 'form': form}
    return render_to_response ('public/apply.html', tpl_vars,
                               context_instance = RequestContext (request))

# -----------------------------------------------------------------------------

def post (request):
    if request.method != 'POST':
        return post_error ("ERROR: %s instead of POST" % request.method)

    form = StallApplicationForm (PersonForm (request.POST),
                                 PersonContactForm (request.POST),
                                 StallForm (request.POST))

    if not form.is_valid ():
        return stallholder_form (request, form)
    else:
        rcpts = []
        trigger = Listener.STALL_APPLICATION_RECEIVED
        listeners = Listener.objects.filter (trigger = trigger)
        for l in listeners:
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
