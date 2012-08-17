from django import template
from django.core.urlresolvers import reverse
from cams.models import Contactable, Player

register = template.Library()

@register.simple_tag
def abook_url(obj, cmd=None):
    if cmd:
        base = '_'.join([cmd, obj.type_str])
    else:
        base = obj.type_str
    return reverse(':'.join(['abook', base]), args=[obj.id])

@register.simple_tag
def player_link(user):
    player = Player.objects.filter(user=user)
    if len(player) > 0:
        person = player[0].person
        url = reverse('abook:person', args=[person.id])
        return u"<a href=\"{}\">{}</a>".format(url, person.__unicode__())
    return "Unknown user"

@register.simple_tag
def appli_link(obj):
    if obj.type == Contactable.PERSON:
        apps = obj.person.appli_person.all()
        if len(apps) > 0:
            app = apps[0]
            url = reverse('appli_detail',
                          args=[app.faireventapplication.subtype, app.id])
            return '<a href={0}>{1}</a> ({2})'. \
                format(url, app.event, app.faireventapplication.type_str)
    return ''

@register.simple_tag
def field_row(f, empty=False):
    if f.field.required and not empty:
        req = '*'
    else:
        req = ''
    label = '<th class="apply-label">{0}{1}</th>'.format(f.label_tag(), req)
    if f.errors and not empty:
        field = '{0}{1}'.format(f.errors, f)
    else:
        field = f
    if f.help_text:
        full = '<td>{0}</td><td class="apply-help">{1}</td>'.format \
            (field, f.help_text)
    else:
        full = '<td colspan="2">{0}</td>'.format(field)
    return '<tr>{0}{1}</tr>'.format(label, full)

@register.simple_tag
def form_title_row(title, h):
    return \
        '<tr><td class="apply-title" colspan="3"><h{0}>{1}</h{0}></td></tr>' \
        .format(h, title)
