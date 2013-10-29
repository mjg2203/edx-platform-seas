from bulk_email.models import Optout
from courseware.access import has_access
from courseware.masquerade import setup_masquerade
from cvn_student.forms import ProctorForm
from cvn_student.models import Proctor
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django_future.csrf import ensure_csrf_cookie
from external_auth.models import ExternalAuthMap
from ims_lti_py import ToolConsumer, ToolConfig
from mitxmako.shortcuts import render_to_response
from student.models import CourseEnrollment
from student.models import UserProfile
from student.views import cert_info
from student.views import course_from_id
from student.views import exam_registration_info
import django.contrib.auth
import hashlib
import json
import re

# TODO: check on this import
from courseware.courses import (get_courses, get_course_with_access,
                                get_courses_by_university, sort_by_announcement)


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



@login_required
@ensure_csrf_cookie
def cvn_lms_dashboard(request):
    user = request.user

    # Build our courses list for the user, but ignore any courses that no longer
    # exist (because the course IDs have changed). Still, we don't delete those
    # enrollments, because it could have been a data push snafu.
    courses = []
    for enrollment in CourseEnrollment.enrollments_for_user(user):
        try:
            courses.append((course_from_id(enrollment.course_id), enrollment))
        except ItemNotFoundError:
            log.error("User {0} enrolled in non-existent course {1}"
                      .format(user.username, enrollment.course_id))

    course_optouts = Optout.objects.filter(user=user).values_list('course_id', flat=True)

    message = ""
    if not user.is_active:
        message = render_to_string('registration/activate_account_notice.html', {'email': user.email})

    # Global staff can see what courses errored on their dashboard
    staff_access = False
    errored_courses = {}

    # FIXME: in the copy-paste where this page of code came from, the following
    # lines were not taken into consideration, so they cause this page to break
    # for admin users:
    ## if has_access(user, 'global', 'staff'):
    ##     # Show any courses that errored on load
    ##     staff_access = True
    ##     errored_courses = modulestore().get_errored_courses()

    show_courseware_links_for = frozenset(course.id for course, _enrollment in courses
                                          if has_access(request.user, course, 'load'))

    cert_statuses = {course.id: cert_info(request.user, course) for course, _enrollment in courses}

    exam_registrations = {course.id: exam_registration_info(request.user, course) for course, _enrollment in courses}

    # get info w.r.t ExternalAuthMap
    external_auth_map = None
    try:
        external_auth_map = ExternalAuthMap.objects.get(user=user)
    except ExternalAuthMap.DoesNotExist:
        pass

    try:
        theProctor = Proctor.objects.get(user=user)
    except:
        theProctor = Proctor(user=user)
        theProctor.save()
    proct_form = ProctorForm(instance=theProctor)

    context = {'courses': courses,
               'course_optouts': course_optouts,
               'message': message,
               'external_auth_map': external_auth_map,
               'staff_access': staff_access,
               'errored_courses': errored_courses,
               'show_courseware_links_for': show_courseware_links_for,
               'cert_statuses': cert_statuses,
               'exam_registrations': exam_registrations,
               'form':proct_form,
               }

    return render_to_response('dashboard.html', context)




def change_proctorinfo_request(request):
    ''' AJAX call from the profile page. User wants to update his proctor's info.
    '''
    ## Make sure it checks for existing e-mail conflicts
    if not request.user.is_authenticated:
        return HttpResponse(json.dumps({'success': False,
                                        'error': _("You must be signed in to edit your proctor's information.")}))
    elif request.method != 'GET':
        return HttpResponse(json.dumps({'success': False,
                                        'error': _("There's been an error updating your proctor's information!")}))

    user = request.user

    # At this point we know that the user is signed in and has submitted the form
    form = ProctorForm(request.GET) # A form bound to the POST data
    if form.is_valid(): # All validation rules pass
        try:
            thisProctor = user.proctor;
        except DoesNotExist:
            thisProctor = Proctor(user=user)
            thisProctor.save();
        thisProctor.__dict__.update(**form.cleaned_data);
        thisProctor.save();
        return HttpResponse(json.dumps({'success': True}))
    else:
        return HttpResponse(json.dumps({'success': False,
                                    'errors': form.errors}))

    return HttpResponse(json.dumps({'success': True}))

LTI_LAUNCH_URL = settings.LTI_LAUNCH_URL
LTI_CONSUMER_KEY = settings.LTI_CONSUMER_KEY
LTI_CONSUMER_SECRET = settings.LTI_CONSUMER_SECRET

@login_required
@ensure_csrf_cookie
def piazza_discussion(request, course_id):
    '''
    Shows the page under the Discussion tab with an iframe containing Piazza
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
    consumer.roles = piazza_role
    consumer.context_id = course_id
    consumer.context_title = course.display_name_with_default
    consumer.context_label = course.number.replace('_', ' ')
    consumer.tool_consumer_instance_guid = 'lms.cvn.columbia.edu'
    consumer.tool_consumer_instance_description = 'Columbia University'
 

    launch_data = consumer.generate_launch_data()
    launch_url = consumer.launch_url


    course = get_course_with_access(request.user, course_id, 'load')
    staff_access = has_access(request.user, course, 'staff')
    masq = setup_masquerade(request, staff_access)    # allow staff to toggle masquerade on info page

    return render_to_response('courseware/piazza_discussion.html', {'request': request, 'course_id': course_id, 'cache': None,
            'course': course, 'staff_access': staff_access, 'masquerade': masq, 'launch_url':launch_url, 'launch_data':launch_data})

@login_required
@ensure_csrf_cookie
def piazza_redirect(request):
    '''
    This view outputs a self-sending html form that sends a POST message to Piazza.
      From the user's perspective, this view redirects signs them into Piazza
    '''
    return render_to_response('courseware/piazza_redirect.html', {'launch_data':request.GET, 'launch_url':LTI_LAUNCH_URL})


def course_dashboard(request, org, course, name):
    #TODO: display course roster for a class
    courseEnrollments = CourseEnrollment.objects.filter(course_id=org+'/'+course+'/'+name)
    returnable = ''
    for courseEnrollment in courseEnrollments:
        returnable += str(courseEnrollment.user.username)+'<br />'
    return HttpResponse(returnable)
    return HttpResponse("Welcome to the professor dashboard!")