from django.db import models
from django.contrib.auth.models import User
from django.db.models import (CharField, TextField, DateField, BooleanField,
                              PositiveIntegerField, PositiveSmallIntegerField,
                              ForeignKey, OneToOneField, ManyToManyField,
                              ImageField)
from cams.models import (Record, Contact, Event, Fair, Person,
                         Application, EventApplication, Invoice)
from cams.libcams import get_obj_address
from mrwf.settings import IMG_MAX_D, IMG_MAX_d
from mrwf.extra import imaging

# WORKAROUND for temporary fix with the event contacts
from django.db.models import EmailField, URLField, IntegerField
from cams.models import Contact

class FairEventType(models.Model):
    name = CharField(max_length=63)
    tag = CharField(max_length=3)

    def __unicode__(self):
        return self.name

    class Meta(object):
        verbose_name = 'Fair event listing'
        ordering = ['name']


class FairEventCategory(models.Model):
    word = CharField(max_length=31)

    def __unicode__(self):
        return self.word

    class Meta(object):
        verbose_name_plural = 'Fair event categories'


class FairEvent(Event):
    event = OneToOneField(Event, parent_link=True)
    etype = ForeignKey(FairEventType, blank=True, null=True,
                       verbose_name="Listing")
    categories = ManyToManyField(FairEventCategory, null=True, blank=True)

    # Bug fix to clear the image (file) field in admin:
    # http://code.djangoproject.com/ticket/7048
    # http://code.djangoproject.com/ticket/4979
    image = ImageField(upload_to='img', blank=True, null=True)
    age_min = PositiveIntegerField(blank=True, null=True)
    age_max = PositiveIntegerField(blank=True, null=True)

    # WORKAROUND
    # Temporary fix to get a practical solution for the event contact details.
    # This can be used to override the organisation contact details.
    line_1 = CharField(max_length=63, blank=True)
    line_2 = CharField(max_length=63, blank=True)
    line_3 = CharField(max_length=63, blank=True)
    town = CharField(max_length=63, blank=True)
    postcode = CharField(max_length=15, blank=True)
    country = CharField(max_length=63, blank=True)
    email = EmailField(blank=True, max_length=127, help_text =
                       Contact.email_help_text, verbose_name="E-mail")
    website = URLField(max_length=255, verify_exists=False, blank=True,
                        help_text=Contact.website_help_text)
    telephone = CharField(max_length=127, blank=True)
    mobile = CharField(max_length=127, blank=True)
    fax = CharField(max_length=31, blank=True)
    addr_order = IntegerField("Order", blank=True, default=0, help_text=
                              "Order of the premises on Mill Road.")
    addr_suborder = IntegerField("Sub-order", blank=True, default=0,
                                 help_text=
                     "Order of the premises on side streets around Mill Road.")
    ignore_org_c = BooleanField(default=False, verbose_name =
                                "Ignore organisation contacts")

    def save(self, *args, **kwargs):
        if not self.fair:
            self.fair = Fair.objects.get(current=True)
        if not self.date:
            self.date = self.fair.date
        if self.image:
            imaging.scale_down(self.image, IMG_MAX_D, IMG_MAX_d)
        super(FairEvent, self).save(args, kwargs)

    # WORKAROUND to make the event contacts more flexible
    def get_composite_contact(self):
        class CompositeContact(object):
            def __init__(self, event):
                attrs = ['line_1', 'line_2', 'line_3', 'postcode', 'town',
                         'country', 'email', 'website', 'telephone', 'mobile',
                         'fax', 'addr_order', 'addr_suborder']

                if event.ignore_org_c:
                    for att in attrs:
                        setattr(self, att, getattr(event, att, ''))
                else:
                    if event.org and event.org.contact_set.count() > 0:
                        org_c = event.org.contact_set.all()[0]
                    else:
                        org_c = None

                    for att in attrs:
                        value = getattr(event, att, '')

                        if org_c and not value:
                            value = getattr(org_c, att, '')

                        setattr(self, att, value)

            def get_address(self, *args):
                return get_obj_address(self, *args)

        return CompositeContact(self)

    @classmethod
    def get_for_fair(cls, event_id, fair):
        base_event = super(FairEvent, cls).get_for_fair(event_id, fair)
        if base_event:
            return cls.objects.get(pk=base_event.pk)
        return None

class StallEvent(FairEvent):
    TELEPHONE = 0
    EMAIL = 1
    WEBSITE = 2

    xcontact = ((TELEPHONE, 'telephone'),
                (EMAIL, 'email'),
                (WEBSITE, 'website'))

    n_spaces = PositiveSmallIntegerField \
        (default=1, verbose_name="Number of spaces")
    n_tables = PositiveSmallIntegerField \
        (default=0, verbose_name="Number of tables")
    invoice_person = ForeignKey(Person, blank=True, null=True)
    invoice_contact = ForeignKey(Contact, blank=True, null=True)
    main_contact = PositiveSmallIntegerField \
        (choices=xcontact, blank=True, null=True)
    extra_web_contact = TextField(blank=True)
    comments = TextField(blank=True)

    def get_main_contact_value(self):
        value = None

        if self.main_contact:
            p = self.event.owner.person
            c = Contact.objects.filter(obj=p)

            if c.count() > 0:
                if self.main_contact == StallEvent.TELEPHONE:
                    value = c[0].telephone
                elif self.main_contact == StallEvent.EMAIL:
                    value = c[0].email
                elif self.main_contact == StallEvent.WEBSITE:
                    value = c[0].website

        if not value:
            value = '[not provided]'

        return value


class FairEventApplication(EventApplication):
    STALLHOLDER = 0
    ADVERTISER = 1
    SPONSOR = 2
    OTHER = 3

    xtypes = ((STALLHOLDER, 'stallholder'), (ADVERTISER, 'advertiser'),
              (SPONSOR, 'sponsor'), (OTHER, 'other'))

    subtype = PositiveSmallIntegerField(choices=xtypes)
    org_name = CharField \
        (max_length=128, blank=True, verbose_name="Organisation name")

    @property
    def type_str(self):
        return FairEventApplication.xtypes[self.subtype][1]

    def save(self, *args, **kwargs):
        if (self.status == Application.REJECTED):
            self.event.status = Record.DISABLED
            self.event.save()
        elif (self.status == Application.PENDING):
            self.event.status = Record.NEW
            self.event.save()
        super(FairEventApplication, self).save(args, kwargs)


class Listener(models.Model):
    STALL_APPLICATION_RECEIVED = 0
    STALL_APPLICATION_ACCEPTED = 1
    STALL_APPLICATION_REJECTED = 2

    xtrigger = ((STALL_APPLICATION_RECEIVED, 'stall application received'),
                (STALL_APPLICATION_ACCEPTED, 'stall application accepted'),
                (STALL_APPLICATION_REJECTED, 'stall application rejected'))

    trigger = PositiveSmallIntegerField(choices=xtrigger)
    user = ForeignKey(User)

    def __unicode__(self):
        return '{0} upon {1}'.format \
            (self.user, Listener.xtrigger[self.trigger][1])


class StallInvoice(Invoice):
    stall = ForeignKey(StallEvent, unique=True)

    def __unicode__(self):
        return self.stall.__unicode__()

    class Meta(Invoice.Meta):
        ordering = ['stall__name']
