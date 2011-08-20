from django import template

register = template.Library()

@register.simple_tag
def field_row(f):
    if f.field.required:
        req = '*'
    else:
        req = ''
    return '<tr><th>{0}{1}</th><td>{2}{3}</td></tr>'.format \
        (f.label_tag(), req, f.errors, f)
