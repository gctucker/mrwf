from cams.models import Fair
from django.shortcuts import render_to_response

def index (request):
    try:
        fair = Fair.objects.get (current = True)
    except Fair.DoesNotExist:
        fair = None
    return render_to_response ('cams/public.html',
                               {'page_title': 'Public Information',
                                'fair': fair})
