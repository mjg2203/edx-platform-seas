# Create your views here.
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
import requests
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from student.views import login_user
from student.views import _do_create_account
from student.views import activate_account
from mitxmako.shortcuts import render_to_response



from django.contrib.auth.models import User

from django.conf import settings

import re

from ims_lti_py import ToolConsumer, ToolConfig,\
        OutcomeRequest, OutcomeResponse
import hashlib
from student.views import course_from_id

from django.db import connection, connections, transaction

import time

from django.contrib.auth import authenticate
import django.contrib.auth

def login(request):
    '''
    If user is already logged in, redirects him to the dashboard
    If user isn't logged in, redirects them to WIND login
    If user is coming back from WIND, authenticates with ticket id
    If user is coming from the old CVN, authenticates with CVN-generated ticket
    '''
    reqData = request.POST
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))
    if 'ticketid' in request.GET:
        user = authenticate(request=request, token=request.GET.get('ticketid', ''))

        if user is not None:
            if user.is_active:
                print "You provided a correct username and password!"
                django.contrib.auth.login(request, user)
            else:
                return HttpResponse('Your account has been disabled!')
        else:
            return HttpResponse('Your username and password were incorrect.')
        #if user is a professor, redirect them to cms
        user_groups = [g.name for g in user.groups.all()]
        pattern = re.compile("instructor|staff")
        returnable = ''
        for user_group in user_groups:
            if pattern.match(user_group):
                return redirect(settings.CMS_URL)
        return redirect(reverse('dashboard'))

    elif 'email' in reqData and 'first' in reqData and 'last' in reqData and 'token' in reqData:
        '''
        User is logging in via the old PHP CVN web app
        available GET variables: email, first, last, token
        '''
        user = authenticate(user_email=reqData['email'], first=reqData['first'],
                             last=reqData['last'], token=reqData['token'], username=None)
        if user is not None:
            if user.is_active:
                print "You provided a correct username and password!"
                django.contrib.auth.login(request, user)
            else:
                return HttpResponse('Your account has been disabled!')
        else:
            return HttpResponse('CVN authentication failed.')
        #if user is a professor, redirect them to cms
        user_groups = [g.name for g in user.groups.all()]
        pattern = re.compile("instructor|staff")
        returnable = ''
        for user_group in user_groups:
            if pattern.match(user_group):
                return redirect(settings.CMS_URL)
        return redirect(reverse('dashboard'))
    else:
        '''
        No post or get requests, so redirect user to Columbia WIND login
        '''
        return redirect(settings.WIND_LOGIN_URL + "?destination=" + settings.WIND_DESTINATION)


    
def fakewind(request):
    return HttpResponse("Hello, world. You're at fake WIND.")

def register(request):
    return redirect("http://cvn.columbia.edu/");
