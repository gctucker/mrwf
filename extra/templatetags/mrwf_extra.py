# MRWF - extra/public/templatetags/mrwf_extra.py
#
# Copyright (C) 2009, 2010, 2011. 2012, 2013
# Guillaume Tucker <guillaume@mangoz.org>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

from django import template
from django.core.urlresolvers import reverse
from cams.models import Contactable, Player

register = template.Library()

@register.simple_tag
def abook_url(obj, cmd=None, extra_arg=None):
    if cmd:
        base = '_'.join([cmd, obj.type_str])
    else:
        base = obj.type_str
    args = [obj.pk]
    if extra_arg is not None:
        args.append(extra_arg)
    return reverse(':'.join(['abook', base]), args=args)

@register.simple_tag
def abook_add_url(obj):
    return reverse(':'.join(['abook', 'add_{0}'.format(obj.type_str)]))

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
    if f.is_hidden:
        return f

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
