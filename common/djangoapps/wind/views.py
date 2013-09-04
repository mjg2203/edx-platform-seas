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
        user = authenticate(email=reqData['email'], first=reqData['first'],
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

@login_required
@ensure_csrf_cookie
def piazza_test(request, course_id):
    '''
    This view outputs a self-sending html form that sends a POST message to Piazza.
      From the user's perspective, this view redirects them and signs them into Piazza
    '''
    # Create a new tool configuration
    config = ToolConfig(title = 'Piazza',
            launch_url = LTI_LAUNCH_URL)

    # Create tool consumer using LTI!
    consumer = ToolConsumer(LTI_CONSUMER_KEY,
            LTI_CONSUMER_SECRET)
    consumer.set_config(config)

    
    #retrieve user and course models
    user = User.objects.prefetch_related("groups").get(id=request.user.id)
    userProfile = UserProfile.objects.get(user_id=user.id)
    course = course_from_id(course_id)

    #check for permissions to determine what role to pass to Piazza.com through 
    piazza_role = ''
    if user.groups.filter(name=('instructor_'+course_id)).count() != 0 or request.user.is_staff:
        piazza_role = 'Instructor'
    elif user.groups.filter(name=('staff_'+course_id)).count() != 0:
        piazza_role = 'Staff'
    else:
        piazza_role = 'Learner'

    # Set some launch data from: http://www.imsglobal.org/LTI/v1p1pd/ltiIMGv1p1pd.html#_Toc309649684
    consumer.resource_link_id = course_id
    consumer.lis_person_contact_email_primary = user.email
    consumer.lis_person_name_full = str(userProfile.name)
    hash = hashlib.md5()
    hash.update(str(userProfile.user_id))
    consumer.user_id = hash.hexdigest()
    #TODO: check if user is is_staff, student, professor, or staff and set the role appropriately
    #consumer.roles = 'Learner'
    consumer.roles = piazza_role
    consumer.context_id = course_id
    consumer.context_title = course.display_name_with_default
    consumer.context_label = course.number.replace('_', ' ')
    consumer.tool_consumer_instance_guid = 'lms.cvn.columbia.edu'
    consumer.tool_consumer_instance_description = 'Columbia University'
 

    launch_data = consumer.generate_launch_data()
    launch_url = consumer.launch_url
    

    #render a self-submitting form that sends all data to Piazza.com via the LTI standard
    returnable = '<form id="ltiLaunchFormSubmitArea" action="' + launch_url + '" name="ltiLaunchForm" id="ltiLaunchForm" method="post" encType="application/x-www-form-urlencoded">'
    for key in launch_data:
        returnable += '<input type="hidden" name="'+ key +'" value="'+ str(launch_data[key]) + '"/>'
    returnable += '<input type="submit" value="Go to Piazza"></input>'
    returnable += '</form>'
    returnable += '<script language="javascript">document.getElementById("ltiLaunchFormSubmitArea").style.display = "none";document.ltiLaunchForm.submit();</script>'
    return HttpResponse(returnable)
    result = requests.post(launch_url, params=launch_data)
    return HttpResponse(result.text)

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
