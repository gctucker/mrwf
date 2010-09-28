from django.contrib import admin
from cams.models import (Person, Organisation, Member, Group, Fair, Role,
                         Player, Event, Actor, EventComment)
from cams.admin import (PersonAdmin, OrganisationAdmin, MemberAdmin,
                        GroupAdmin, FairAdmin, PlayerAdmin, EventAdmin,
                        ActorAdmin, EventCommentAdmin)
from mrwf.extra.models import (FairEventType, FairEventCategory, FairEvent,
                               StallEvent, Listener)

# temporary fix for the event contacts
from cams.admin import ContactInline

class FairEventAdmin (EventAdmin):
    event_fields = ('Event',
                    {'fields': ('status',
                                'name',
                                'description',
                                ('time', 'end_time'),
                                'owner',
                                'org',
                                'location')})

    prog_event_fields = ('Programme info',
                         {'fields': ('etype',
                                     'categories',
                                     'image',
                                     ('age_min', 'age_max'))})

    contact_mode_fields = ('Contact mode',
                           {'fields': ('ignore_org_c', )})

    fieldsets = [event_fields, prog_event_fields, contact_mode_fields] \
                + ContactInline.fieldsets
    ordering = ('name', )
    filter_horizontal = ['categories']


class StallEventAdmin (FairEventAdmin):
    stall_fields = ('Stall info', {'fields': (('n_spaces', 'n_tables'),
                                              'main_contact')})

    fieldsets = [FairEventAdmin.event_fields, stall_fields,
                 FairEventAdmin.prog_event_fields,
                 FairEventAdmin.contact_mode_fields] \
                 + ContactInline.fieldsets

class ListenerAdmin (admin.ModelAdmin):
    list_display = ['user', 'trigger']


# -- CAMS admin --
admin.site.register (Person, PersonAdmin)
admin.site.register (Organisation, OrganisationAdmin)
admin.site.register (Member, MemberAdmin)
admin.site.register (Group, GroupAdmin)
admin.site.register (Fair, FairAdmin)
admin.site.register (Player, PlayerAdmin)
#admin.site.register (Event, EventAdmin)
#admin.site.register (Actor, ActorAdmin)
#admin.site.register (EventComment, EventCommentAdmin)

# -- extra admin --
admin.site.register (FairEvent, FairEventAdmin)
admin.site.register (FairEventType)
admin.site.register (FairEventCategory)
admin.site.register (StallEvent, StallEventAdmin)
admin.site.register (Listener, ListenerAdmin)
