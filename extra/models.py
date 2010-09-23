from django.db import models
from django.contrib.auth.models import User
from django.db.models import (CharField, DateField,
                              PositiveIntegerField, PositiveSmallIntegerField,
                              ForeignKey, OneToOneField,
                              ImageField)
from cams.models import Contact, Item, Event, Fair, EventApplication

# for temporary fix with the event contacts
from django.db.models import EmailField, URLField, IntegerField
from cams.models import Contact

class FairEventType (models.Model):
    name = CharField (max_length = 63)

    def __unicode__ (self):
        return self.name

    class Meta:
        ordering=['name']


class FairEvent (Event):
    event = OneToOneField (Event, parent_link = True)
    etype = ForeignKey (FairEventType, blank = True, null = True,
                        verbose_name = "Event type")
    # Bug fix to clear the image (file) field in admin:
    # http://code.djangoproject.com/ticket/7048
    # http://code.djangoproject.com/ticket/4979
    image = ImageField (upload_to = 'img', blank = True, null = True)
    age_min = PositiveIntegerField (blank = True, null = True)
    age_max = PositiveIntegerField (blank = True, null = True)

    # Temporary fix to get a practical solution for the event contact details.
    # This can be used to override the organisation contact details.
    line_1 = CharField (max_length = 63, blank = True)
    line_2 = CharField (max_length = 63, blank = True)
    line_3 = CharField (max_length = 63, blank = True)
    town = CharField (max_length = 63, blank = True)
    postcode = CharField (max_length = 15, blank = True)
    country = CharField (max_length = 63, blank = True)
    email = EmailField (blank = True, max_length = 127, help_text =
                        Contact.email_help_text, verbose_name = "E-mail")
    website = URLField (max_length = 255, verify_exists = False, blank = True,
                        help_text = Contact.website_help_text)
    telephone = CharField (max_length = 127, blank = True)
    mobile = CharField (max_length = 127, blank = True)
    fax = CharField (max_length = 31, blank = True)
    addr_order = IntegerField ("Order", blank = True, default = 0, help_text =
                               "Order of the premises on Mill Road.")
    addr_suborder = IntegerField ("Sub-order", blank = True, default = 0,
                                  help_text =
                     "Order of the premises on side streets around Mill Road.")

    def save (self, *args, **kwargs):
        if not self.fair:
            self.fair = Fair.objects.get (current = True)
        if not self.date:
            self.date = self.fair.date
        super (FairEvent, self).save (args, kwargs)


class StallEvent (FairEvent):
    TELEPHONE = 0
    EMAIL = 1
    WEBSITE = 2

    xcontact = ((TELEPHONE, 'telephone'),
                (EMAIL, 'email'),
                (WEBSITE, 'website'))

    n_spaces = PositiveSmallIntegerField (default = 1, verbose_name =
                                          "Number of spaces")
    n_tables = PositiveSmallIntegerField (default = 0, verbose_name =
                                          "Number of tables")
    main_contact = PositiveSmallIntegerField (choices = xcontact,
                                              blank = True, null = True,
                                              help_text =
                                          "Main contact used in the programme")

    def get_main_contact_value (self):
        value = None

        if self.main_contact:
            p = self.event.owner.person
            c = Contact.objects.filter (obj = p)

            if c.count () > 0:
                if self.main_contact == StallEvent.TELEPHONE:
                    value = c[0].telephone
                elif self.main_contact == StallEvent.EMAIL:
                    value = c[0].email
                elif self.main_contact == StallEvent.WEBSITE:
                    value = c[0].website

        if not value:
            value = '[not provided]'

        return value


class FairEventApplication (EventApplication):
    STALLHOLDER = 0
    PERFORMER = 1
    ADVERTISER = 2
    SPONSOR = 3
    VOLUNTEER = 4
    STEWARD = 5

    xtypes = ((STALLHOLDER, 'stallholder'), (PERFORMER, 'performer'),
              (ADVERTISER, 'advertiser'), (SPONSOR, 'sponsor'),
              (VOLUNTEER, 'volunteer'), (STEWARD, 'steward'))

    subtype = PositiveSmallIntegerField (choices = xtypes)

    @property
    def type_name (self):
        return xtypes[self.subtype][1]


class Listener (models.Model):
    STALL_APPLICATION_RECEIVED = 0
    STALL_APPLICATION_ACCEPTED = 1
    STALL_APPLICATION_REJECTED = 2

    xtrigger = ((STALL_APPLICATION_RECEIVED, 'stall application received'),
                (STALL_APPLICATION_ACCEPTED, 'stall application accepted'),
                (STALL_APPLICATION_REJECTED, 'stall application rejected'))

    trigger = PositiveSmallIntegerField (choices = xtrigger)
    user = ForeignKey (User)

    def __unicode__ (self):
        return "%s upon %s" % (self.user, Listener.xtrigger[self.trigger][1])
