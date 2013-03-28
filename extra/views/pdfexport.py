# -*- coding: UTF-8
#
# MRWF - extra/public/views/pdfexport.py
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

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from copy import deepcopy
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Image, Paragraph, Spacer,
                                PageBreak)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from cams.models import Contactable, Person, Organisation, Group
from cams.libcams import make_group_file_name
from cams.pdftools import append_org_form
from django.conf import settings

@login_required
def group_org_pdf(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    orgs = group.members.filter(type=Contactable.ORGANISATION)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachement; filename=\"%s\"' % \
        (make_group_file_name(group, '-org-forms') + '.pdf')

    buf = StringIO()
    styles = getSampleStyleSheet()
    page_size = A4
    doc = SimpleDocTemplate(buf, pagesize=page_size)
    flow = []

    image_w = 1056
    image_h = 270
    w = page_size[0] * 0.4
    h = w * image_h / image_w
    letterhead = Image(settings.STATIC_ROOT
                       + '/img/mrwf_master_logo_black.png',
                       width=w, height=h)

    head_style = deepcopy(styles["Normal"])
    head_style.fontSize = 10
    head_style.alignment = TA_CENTER
    head_txt = Paragraph('Postal Address: c/o AL AMIN, 100 Mill Road CB1 2BD',
                         head_style)
    head_email = Paragraph('Chair@millroadwinterfair.org', head_style)

    instr_style = deepcopy(styles["Normal"])
    instr_style.fontSize = 10
    instr_style.alignment = TA_LEFT
    instr = Paragraph("""Please write any changes on this form or tick the box
at the bottom to show that it is correct.  Then, drop it in at the Post Office
at Al-Amin's.""", instr_style)

    img = '<img src="%s" width="%d" height="%d" />' % \
        (settings.STATIC_ROOT + '/img/checkbox.png', 10, 10)
    check = Paragraph(img +
                      '  Please check this box if all details are correct.',
                      instr_style)

    spacer = Spacer(0, inch/2)
    page_break = PageBreak()

    for o in orgs:
        flow.append(letterhead)
        flow.append(head_txt)
        flow.append(head_email)
        flow.append(spacer)
        flow.append(instr)
        flow.append(spacer)
        org = Organisation.objects.get(pk=o)
        append_org_form(org, flow, page_size)
        flow.append(spacer)
        flow.append(check)
        flow.append(page_break)

    doc.build(flow)
    pdf = buf.getvalue()
    buf.close()
    response.write(pdf)

    return response
