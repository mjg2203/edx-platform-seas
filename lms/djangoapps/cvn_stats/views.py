from django.http import HttpResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response

import proxy.views

@login_required
def dashboard(request):
    if request.user.username not in settings.CVN_ANALYTICS_USERS:
        raise Http404
    context = { }
    return render_to_response("cvn_stats_dash.html", context)

@login_required
def dashboard_inner(request):
    if request.user.username not in settings.CVN_ANALYTICS_USERS:
        raise Http404

    # the next three lines, I know, I know
    parts = request.path.split("/")
    shorter = "/".join(parts[3:])
    remoteurl = settings.CVN_ANALYTICS_URL + shorter

    return proxy.views.proxy_view(request, remoteurl)
