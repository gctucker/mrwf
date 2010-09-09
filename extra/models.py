from django.db import models
from django.contrib.auth.models import User
from django.db.models import (CharField, DateField,
                              PositiveIntegerField, PositiveSmallIntegerField,
                              ForeignKey, OneToOneField,
                              ImageField)
from cams.models import Item, Event, Fair, EventApplication

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


class StallApplication (EventApplication):
    @property
    def stall (self):
        return self.event


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
