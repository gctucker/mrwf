from django import template
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def abook_url(obj):
    return reverse(':'.join(['abook', obj.type_str]), args=[obj.id])

@register.simple_tag
def field_row(f):
    if f.field.required:
        req = '*'
    else:
        req = ''
    label = '<th>{0}{1}</th>'.format(f.label_tag(), req)
    field = '{0}{1}'.format(f.errors, f)
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
