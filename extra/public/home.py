from django.shortcuts import render_to_response
from cams.models import Fair

def index (request):
    try:
        fair = Fair.objects.get (current = True)
    except Fair.DoesNotExist:
        fair = None
    return render_to_response ('public/home.html',
                               {'page_title': 'Public Information',
                                'fair': fair})
