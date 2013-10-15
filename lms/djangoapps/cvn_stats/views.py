from django.http import HttpResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response


@login_required
def dashboard(request):
    if request.user.username not in settings.CVN_ANALYTICS_USERS:
        raise Http404
    context = { }
    return render_to_response("cvn_stats_dash.html", context)
