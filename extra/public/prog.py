import datetime
from xml.dom.minidom import getDOMImplementation
from django.http import HttpResponse, Http404
from django.db.models.query import Q
from django.shortcuts import render_to_response, get_object_or_404
from cams.models import (Person, Organisation, OrganisationContact, Event,
                         Fair)
from cams.libcams import str2list
from mrwf.extra.models import FairEvent, FairEventType

def add_date_ele (doc, root, tag, date):
    ele = doc.createElement (tag)
    root.appendChild (ele)
    ele.setAttribute ('year', str (date.year))
    ele.setAttribute ('month', str (date.month))
    ele.setAttribute ('day', str (date.day))

def add_time_ele (doc, root, tag, time):
    ele = doc.createElement (tag)
    root.appendChild (ele)
    ele.setAttribute ('hour', str (time.hour))
    ele.setAttribute ('minute', str (time.minute))

def add_fevent_ele (doc, root, tag, fev):
    ele = doc.createElement (tag)
    root.appendChild (ele)
    ele.setAttribute ('id', str (fev.pk))
    ele.setAttribute ('name', fev.event.name)

def fair_obj (fair):
    f_events = FairEvent.objects.filter (fair = fair)
    f_events = f_events.order_by ('event__organisationcontact__line1')
    f_events = f_events.order_by ('event__time')

    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'events', None)
    root = doc.documentElement
    root.setAttribute ('year', str (fair.date.year))
    root.setAttribute ('month', str (fair.date.month))
    root.setAttribute ('day', str (fair.date.day))

    for it in f_events:
        add_fevent_ele (doc, root, 'event', it)

    return HttpResponse (doc.toprettyxml ('  ', '\n', 'utf-8'),
                         mimetype = 'application/xml')

def event_obj (fair, fevent):
    #if fevent.fair != fair:
    #    print ("wrong fair!")

    event = fevent.event

    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'event', None)
    root = doc.documentElement
    root.setAttribute ('name', event.name)

    if fevent.etype:
        root.setAttribute ('type', fevent.etype.name)

    if fevent.event.location:
        root.setAttribute ('venue', fevent.event.location)
    elif fevent.event.org:
        root.setAttribute ('venue', fevent.event.org.name)

    if fevent.image:
        img = doc.createElement ('image')
        root.appendChild (img)
        img.setAttribute ('url', fevent.image.url)
        img.setAttribute ('width', str (fevent.image.width))
        img.setAttribute ('height', str (fevent.image.height))

    if fevent.age_min or fevent.age_max:
        age = doc.createElement ('age')
        root.appendChild (age)
        if fevent.age_min:
            age.setAttribute ('min', str (fevent.age_min))

        if fevent.age_max:
            age.setAttribute ('max', str (fevent.age_max))

    if event.description:
        desc_ele = doc.createElement ('description')
        root.appendChild (desc_ele)
        desc_txt = doc.createTextNode (event.description)
        desc_ele.appendChild (desc_txt)

    if event.date != fair.date:
        add_date_ele (doc, root, 'date', event.date)

    if event.time:
        add_time_ele (doc, root, 'time', event.time)

    if event.end_date:
        add_date_ele (doc, root, 'end_date', event.end_date)

    if event.end_time:
        add_time_ele (doc, root, 'end_time', event.end_time)

    if event.org:
        org_ele = doc.createElement ('organisation')
        root.appendChild (org_ele)
        org_ele.setAttribute ('name', event.org.name)

        contacts = OrganisationContact.objects.filter (org = event.org)

        if contacts.count () > 0:
            contact = contacts[0]
            org_ele.setAttribute ('line_1', contact.line_1)
            org_ele.setAttribute ('line_2', contact.line_2)
            org_ele.setAttribute ('line_3', contact.line_3)
            org_ele.setAttribute ('town', contact.town)
            org_ele.setAttribute ('postcode', contact.postcode)
            org_ele.setAttribute ('website', contact.website)

    return HttpResponse (doc.toprettyxml ('  ', '\n', 'utf-8'),
                         mimetype = 'application/xml')

def get_list (request, param):
    if param in request.GET:
        return str2list (request.GET[param])
    else:
        return []

def get_pos_int (request, param):
    if param in request.GET:
        try:
            val = int (request.GET[param])
            if val < 0:
                val = -1
        except ValueError:
            val = -1
    else:
        val = -1

    return val

def search_obj (request, fair):
    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'events', None)
    root = doc.documentElement
    root.setAttribute ('year', str (fair.date.year))
    root.setAttribute ('month', str (fair.date.month))
    root.setAttribute ('day', str (fair.date.day))

    fe = FairEvent.objects.filter (fair = fair)

    for l in get_list (request, 'location'):
        fe = fe.filter (Q (event__location__icontains = l)
                | Q (event__org__organisationcontact__line_1__icontains = l)
                | Q (event__org__organisationcontact__line_2__icontains = l)
                | Q (event__org__organisationcontact__line_3__icontains = l)
                | Q (event__org__organisationcontact__postcode__icontains = l))

    hour = get_pos_int (request, 'hour')
    if (hour >= 0) and (hour < 24):
        time = datetime.time (hour)
        fe = fe.filter ((Q (event__time__isnull = True)
                         | Q (event__time__lte = time))
                        & (Q (event__end_time__isnull = True)
                           | Q (event__end_time__gte = time)))

    age = get_pos_int (request, 'age')
    if age > 0:
        fe = fe.filter ((Q (age_min__isnull = True)
                         | Q (age_min__lte = age))
                        & (Q (age_max__isnull = True)
                           | Q (age_max__gte = age)))

    for t in get_list (request, 'type'):
        fe = fe.filter (Q (etype__name__icontains = t))

    for w in get_list (request, 'desc'):
        fe = fe.filter (Q (event__name__icontains = w)
                        | Q (event__description__icontains = w)
                        | Q (event__org__name__icontains = w))

    fe = fe.order_by ('event__name')

    for it in fe:
        add_fevent_ele (doc, root, 'event', it)

    return HttpResponse (doc.toprettyxml ('  ', '\n', 'utf-8'),
                         mimetype = 'application/xml')

# -----------------------------------------------------------------------------

def all_fairs (request):
    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'fairs', None)
    root = doc.documentElement

    for fair in Fair.objects.all ():
        ele = doc.createElement ('fair')
        root.appendChild (ele)

        if fair.current:
            ele.setAttribute ('current', 'True')

        add_date_ele (doc, ele, 'date', fair.date)

    return HttpResponse (doc.toprettyxml ('  ', '\n', 'utf-8'),
                         mimetype = 'application/xml')

def fair (request, fair_year):
    return fair_obj (get_object_or_404 (Fair, date__year = fair_year))

def current (request):
    return fair_obj (get_object_or_404 (Fair, current = True))

def event (request, fair_year, event_id):
    fair = get_object_or_404 (Fair, date__year = fair_year)
    event = get_object_or_404 (FairEvent, pk = event_id)
    return event_obj (fair, event)

def current_event (request, event_id):
    fair = get_object_or_404 (Fair, current = True)
    event = get_object_or_404 (FairEvent, pk = event_id)
    return event_obj (fair, event)

def cats (request, fair_year):
    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'categories', None)
    root = doc.documentElement

    etypes_ele = doc.createElement ('event_types')
    root.appendChild (etypes_ele)
    etypes = FairEventType.objects.all ()

    for it in etypes:
        ele = doc.createElement ('type')
        etypes_ele.appendChild (ele)
        ele.setAttribute ('name', it.name)

    return HttpResponse (doc.toprettyxml ('  ', '\n', 'utf-8'),
                         mimetype = 'application/xml')

def current_cats (request):
    return cats (request, None) # placeholder until types are fair-related

def search (request, fair_year):
    fair = get_object_or_404 (Fair, date__year = fair_year)
    return search_obj (request, fair)

def current_search (request):
    fair = get_object_or_404 (Fair, current = True)
    return search_obj (request, fair)
