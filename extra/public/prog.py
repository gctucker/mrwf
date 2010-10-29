import datetime
from xml.dom.minidom import getDOMImplementation
from django.http import HttpResponse, Http404
from django.db.models.query import Q
from django.shortcuts import render_to_response, get_object_or_404
from cams.models import Record, Person, Organisation, Contact, Event, Fair
from cams.libcams import str2list
from mrwf.extra.models import FairEvent, FairEventCategory

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

def add_event_id_ele (doc, root, tag, event):
    ele = doc.createElement (tag)
    root.appendChild (ele)
    ele.setAttribute ('id', str (event.pk))
    ele.setAttribute ('name', event.name)

def populate_event_ele (doc, ele, event):
    ele.setAttribute ('id', str (event.pk))
    ele.setAttribute ('name', event.name)

    # listing attribute ...
#    if event.etype:
#        root.setAttribute ('type', event.etype.name)

    if event.location:
        ele.setAttribute ('venue', event.location)
    elif event.org:
        ele.setAttribute ('venue', event.org.name)

    if event.description:
        desc_ele = doc.createElement ('description')
        ele.appendChild (desc_ele)
        desc_txt = doc.createTextNode (event.description)
        desc_ele.appendChild (desc_txt)

    if event.image:
        img = doc.createElement ('image')
        ele.appendChild (img)
        img.setAttribute ('url', event.image.url)
        img.setAttribute ('width', str (event.image.width))
        img.setAttribute ('height', str (event.image.height))

    if event.date != event.fair.date:
        add_date_ele (doc, ele, 'date', event.date)

    if event.end_date:
        add_date_ele (doc, ele, 'end_date', event.end_date)

    if event.time:
        add_time_ele (doc, ele, 'time', event.time)

    if event.end_time:
        add_time_ele (doc, ele, 'end_time', event.end_time)

    if event.age_min or event.age_max:
        age = doc.createElement ('age')
        ele.appendChild (age)
        if event.age_min:
            age.setAttribute ('min', str (event.age_min))

        if event.age_max:
            age.setAttribute ('max', str (event.age_max))

    for cat in event.categories.all ():
        cat_ele = doc.createElement ('category')
        ele.appendChild (cat_ele)
        cat_ele.setAttribute ('id', str (cat.pk))
        cat_ele.setAttribute ('name', cat.word)

    # WORKAROUND
    c = event.get_composite_contact ()
    addr_ele = doc.createElement ('address')

    for it in ['line_1', 'line_2', 'line_3', 'town', 'postcode', 'website',
               'email', 'telephone', 'mobile', 'addr_order', 'addr_suborder']:
        addr_ele.setAttribute (it, str (getattr (c, it, '')))

    ele.appendChild (addr_ele)

def fair_obj (fair, dump):
    events = FairEvent.objects.filter (fair = fair)
    events = events.filter (status = Record.ACTIVE)
    events = events.order_by ('organisationcontact__line1')
    events = events.order_by ('time')

    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'events', None)
    root = doc.documentElement
    root.setAttribute ('year', str (fair.date.year))
    root.setAttribute ('month', str (fair.date.month))
    root.setAttribute ('day', str (fair.date.day))

    if dump:
        for it in events:
            ele = doc.createElement ('event')
            root.appendChild (ele)
            populate_event_ele (doc, ele, it)
    else:
        for it in events:
            add_event_id_ele (doc, root, 'event', it)

    return HttpResponse (doc.toprettyxml ('  ', '\n', 'utf-8'),
                         mimetype = 'application/xml')

def event_obj (event):
    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'event', None)
    ele = doc.documentElement
    populate_event_ele (doc, ele, event)
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

    for l in get_list (request, 'venue'):
        fe = fe.filter (Q (event__location__icontains = l)
                        | Q (event__org__name__icontains = l))

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

    if 'cat' in request.GET:
        category = request.GET['cat']
        fe = fe.filter (categories__word__icontains = category)

    for w in get_list (request, 'desc'):
        fe = fe.filter (Q (event__name__icontains = w)
                        | Q (event__description__icontains = w)
                        | Q (event__org__name__icontains = w))

    fe = fe.order_by ('event__name')

    for it in fe:
        add_event_id_ele (doc, root, 'event', it)

    return HttpResponse (doc.toprettyxml ('  ', '\n', 'utf-8'),
                         mimetype = 'application/xml')

# -----------------------------------------------------------------------------

def all_fairs (request):
    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'fairs', None)
    root = doc.documentElement
    root.setAttribute ("api_version", "1.2")

    for fair in Fair.objects.all ():
        ele = doc.createElement ('fair')
        root.appendChild (ele)

        if fair.current:
            ele.setAttribute ('current', 'True')

        add_date_ele (doc, ele, 'date', fair.date)

    return HttpResponse (doc.toprettyxml ('  ', '\n', 'utf-8'),
                         mimetype = 'application/xml')

def fair (request, fair_year):
    return fair_obj (get_object_or_404 (Fair, date__year = int (fair_year)),
                     False)

def current (request):
    return fair_obj (get_object_or_404 (Fair, current = True), False)

def event (request, fair_year, event_id):
    fair = get_object_or_404 (Fair, date__year = fair_year)
    event = get_object_or_404 (FairEvent, pk = event_id)
    if (not event.fair) or (event.fair != fair):
        raise Http404
    return event_obj (event)

def current_event (request, event_id):
    fair = get_object_or_404 (Fair, current = True)
    event = get_object_or_404 (FairEvent, pk = event_id)
    if (not event.fair) or (event.fair != fair):
        raise Http404
    return event_obj (event)

def dump (request, fair_year):
    return fair_obj (get_object_or_404 (Fair, date__year = int (fair_year)),
                     True)

def current_dump (request):
    return fair_obj (get_object_or_404 (Fair, current = True), True)

def cats (request, fair_year):
    # ToDo: review names of categories, types etc.
    impl = getDOMImplementation ()
    doc = impl.createDocument (None, 'categories', None)
    root = doc.documentElement

    for it in FairEventCategory.objects.all ():
        ele = doc.createElement ('category')
        root.appendChild (ele)
        ele.setAttribute ('id', str (it.pk))
        ele.setAttribute ('name', it.word)

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
