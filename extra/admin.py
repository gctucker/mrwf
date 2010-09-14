from django.contrib import admin
from cams.models import (Person, Organisation, Member, Group, Fair, Role,
                         Participant, Event, Actor, EventComment)
from cams.admin import (PersonAdmin, OrganisationAdmin, MemberAdmin,
                        GroupAdmin, FairAdmin, ParticipantAdmin, EventAdmin,
                        ActorAdmin, EventCommentAdmin)
from mrwf.extra.models import (FairEventType, FairEvent, StallEvent, Listener)

class FairEventAdmin (EventAdmin):
    event_fields = ('Event', {'fields': ('status',
                                         'name',
                                         'description',
                                         ('time', 'end_time'),
                                         'owner',
                                         'org',
                                         'location')})

    prog_event_fields = ('Programme info', {'fields': ('etype', 'image',
                                           ('age_min', 'age_max'))})

    fieldsets = (event_fields, prog_event_fields)


class StallEventAdmin (FairEventAdmin):
    stall_fields = ('Stall info', {'fields': (('n_spaces', 'n_tables'),
                                              'main_contact')})

    fieldsets = (FairEventAdmin.event_fields, stall_fields,
                 FairEventAdmin.prog_event_fields)


class ListenerAdmin (admin.ModelAdmin):
    list_display = ['user', 'trigger']


# -- CAMS admin --
admin.site.register (Person, PersonAdmin)
admin.site.register (Organisation, OrganisationAdmin)
admin.site.register (Member, MemberAdmin)
admin.site.register (Group, GroupAdmin)
#admin.site.register (Fair, FairAdmin)
admin.site.register (Participant, ParticipantAdmin)
#admin.site.register (Event, EventAdmin)
#admin.site.register (Actor, ActorAdmin)
#admin.site.register (EventComment, EventCommentAdmin)

# -- extra admin --
admin.site.register (FairEvent, FairEventAdmin)
#admin.site.register (FairEventType)
admin.site.register (StallEvent, StallEventAdmin)
admin.site.register (Listener, ListenerAdmin)
