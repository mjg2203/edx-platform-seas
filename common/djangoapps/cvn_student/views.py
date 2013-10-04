# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
import urllib
import urllib2
import requests
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from student.views import login_user
from student.views import _do_create_account
from student.views import activate_account
from mitxmako.shortcuts import render_to_response

from student.models import UserProfile
from student.models import CourseEnrollment

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
        '''
        post_data = [('ticketid',request.GET.get('ticketid', '')),]     # a sequence of two element tuples
        result = urllib2.urlopen('http://400pixels.net/fakewind/fake_wind_validation.php?'+urllib.urlencode(post_data))
        content = result.read()
        return HttpResponse('Validation Successful!<br />Contents of ticket validation response:<br />'+content if 'yes' in content else 'Validation Failed!<br />Contents of ticket validation response:<br />'+content);
        #return HttpResponse("There's a GET message! ticketid is " +request.GET.get('ticketid', ""))
        '''
        user = authenticate(request=request, token=request.GET.get('ticketid', ''))

        # FIXME: 
        # if isinstance(user, HttpResponse):
            # Raise some kind of exception

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
        '''template = loader.get_template('wind/index.html')
        context = RequestContext(request, {})
        return HttpResponse(template.render(context))'''


    
def fakewind(request):
    return HttpResponse("Hello, world. You're at fake WIND.")

def register(request):
    return redirect("http://cvn.columbia.edu/");

LTI_LAUNCH_URL = settings.LTI_LAUNCH_URL
LTI_CONSUMER_KEY = settings.LTI_CONSUMER_KEY
LTI_CONSUMER_SECRET = settings.LTI_CONSUMER_SECRET



def course_dashboard(request, org, course, name):
    #TODO: display course roster for a class
    #CourseEnrollment.get(user=request.user.id)
    #user = User.objects.get(id=request.user.id)
    #userProfile = UserProfile.objects.get(user_id=user.id)
    courseEnrollments = CourseEnrollment.objects.filter(course_id=org+'/'+course+'/'+name)
    returnable = ''
    for courseEnrollment in courseEnrollments:
        #user = User.objects.get(...
        returnable += str(courseEnrollment.user.username)+'<br />'
    return HttpResponse(returnable)
    return HttpResponse("Welcome to the professor dashboard!")

@login_required
@ensure_csrf_cookie
def course_dashboard(request, org, course, name):
    """
    Display an editable asset library

    org, course, name: Attributes of the Location for the item to edit
    """
    courseEnrollments = CourseEnrollment.objects.filter(course_id=org+'/'+course+'/'+name)
    '''
    returnable = ''
    for courseEnrollment in courseEnrollments:
        #user = User.objects.get(...
        returnable += str(courseEnrollment.user.username)+'<br />'
    return HttpResponse(returnable)
    return HttpResponse("Welcome to the professor dashboard!")
    '''

    return render_to_response('dashboard_index.html', {'courseEnrollments':courseEnrollments})


import json

@ensure_csrf_cookie
def change_proctorinfo_request(request):
    ''' AJAX call from the profile page. User wants a new e-mail.
    '''
    ## Make sure it checks for existing e-mail conflicts
    if not request.user.is_authenticated:
        raise Http404

    user = request.user

    '''
    if not user.check_password(request.POST['password']):
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('Invalid password')}))

    new_email = request.POST['new_email']
    try:
        validate_email(new_email)
    except ValidationError:
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('Valid e-mail address required.')}))

    if User.objects.filter(email=new_email).count() != 0:
        ## CRITICAL TODO: Handle case sensitivity for e-mails
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('An account with this e-mail already exists.')}))

    pec_list = PendingEmailChange.objects.filter(user=request.user)
    if len(pec_list) == 0:
        pec = PendingEmailChange()
        pec.user = user
    else:
        pec = pec_list[0]

    pec.new_email = request.POST['new_email']
    pec.activation_key = uuid.uuid4().hex
    pec.save()

    if pec.new_email == user.email:
        pec.delete()
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('Old email is the same as the new email.')}))

    d = {'key': pec.activation_key,
         'old_email': user.email,
         'new_email': pec.new_email}

    subject = render_to_string('emails/email_change_subject.txt', d)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/email_change.txt', d)

    _res = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [pec.new_email])
    '''
    return HttpResponse(json.dumps({'success': True}))
