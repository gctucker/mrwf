from django.contrib import admin
from cams.models import (Person, Organisation, Member, Group, Fair, Role,
                         Participant, Event, Actor, EventComment,
                         ApplicationType, EventApplication)
from cams.admin import (PersonAdmin, OrganisationAdmin, MemberAdmin,
                        GroupAdmin, FairAdmin, ParticipantAdmin, EventAdmin,
                        ActorAdmin, EventCommentAdmin,
                        ApplicationTypeAdmin, EventApplicationAdmin)
from mrwf.extra.models import (FairEventType, FairEvent, StallEvent,
                               StallApplication)

class FairEventAdmin (EventAdmin):
    fieldsets = (('Event', {'fields': ('status',
                                       'name',
                                       'description',
                                       ('date', 'end_date'),
                                       ('time', 'end_time'),
                                       'org',
                                       'location',
                                       'owner')}),
                 ('Programme info', {'fields': ('fair', 'etype', 'image',
                                           ('age_min', 'age_max'))}))


class StallEventAdmin (FairEventAdmin):
    stall_fs = (('Stall info', {'fields': (('n_spaces', 'n_tables'),
                                           'main_contact')}), )
    fieldsets = stall_fs + FairEventAdmin.fieldsets


# -- CAMS admin --
admin.site.register (Person, PersonAdmin)
admin.site.register (Organisation, OrganisationAdmin)
admin.site.register (Member, MemberAdmin)
admin.site.register (Group, GroupAdmin)
admin.site.register (Fair, FairAdmin)
admin.site.register (Participant, ParticipantAdmin)
admin.site.register (Event, EventAdmin)
admin.site.register (Actor, ActorAdmin)
admin.site.register (EventComment, EventCommentAdmin)
#admin.site.register (ApplicationType, ApplicationTypeAdmin)
admin.site.register (EventApplication, EventApplicationAdmin)

# -- extra admin --
admin.site.register (FairEvent, FairEventAdmin)
admin.site.register (FairEventType)
admin.site.register (StallEvent, StallEventAdmin)
admin.site.register (StallApplication, EventApplicationAdmin)
