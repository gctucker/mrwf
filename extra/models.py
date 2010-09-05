from django.db import models
from django.db.models import (CharField, DateField,
                              PositiveIntegerField, PositiveSmallIntegerField,
                              ForeignKey, OneToOneField,
                              ImageField)
from cams.models import Item, Event, Fair

class FairEventType (models.Model):
    name = CharField (max_length = 63)

    def __unicode__ (self):
        return self.name


class FairEvent (Event):
    etype = ForeignKey (FairEventType, blank = True, null = True,
                        verbose_name = "Event type")
    # Bug fix to clear the image (file) field in admin:
    # http://code.djangoproject.com/ticket/7048
    # http://code.djangoproject.com/ticket/4979
    image = ImageField (upload_to = 'img', blank = True, null = True)
    age_min = PositiveIntegerField (blank = True, null = True)
    age_max = PositiveIntegerField (blank = True, null = True)


class StallEvent (FairEvent):
    n_spaces = PositiveSmallIntegerField (default = 0)
    n_tables = PositiveSmallIntegerField (default = 0)
    main_contact = CharField (max_length = 63, blank = True)
