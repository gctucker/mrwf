try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from reportlab.lib.pagesizes import A5
from reportlab.platypus import SimpleDocTemplate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from cams.models import Contactable, Person, Organisation, Group
from cams.libcams import make_group_file_name
from cams.pdftools import append_org_page

@login_required
def group_org_pdf (request, group_id):
    group = get_object_or_404 (Group, pk = group_id)
    orgs = group.members.filter (type = Contactable.ORGANISATION)

    response = HttpResponse (mimetype = 'application/pdf')
    response['Content-Disposition'] = 'attachement; filename=\"%s\"' % \
        (make_group_file_name (group, '-org-forms') + '.pdf')

    buf = StringIO ()
    page_size = A5
    doc = SimpleDocTemplate(buf, pagesize=page_size)
    flow = []

    for o in orgs:
        org = Organisation.objects.get (pk = o)
        append_org_page (org, flow, page_size)

    doc.build (flow)
    pdf = buf.getvalue ()
    buf.close ()
    response.write (pdf)

    return response
