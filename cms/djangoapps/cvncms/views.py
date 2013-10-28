from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from django.core.urlresolvers import reverse
from mitxmako.shortcuts import render_to_response
from student.models import UserProfile
from student.models import CourseEnrollment
from django.contrib.auth.models import User
from ims_lti_py import ToolConsumer, ToolConfig
import hashlib
from student.views import course_from_id
from xmodule.modulestore.django import modulestore
from contentstore.views.access import get_location_and_verify_access
from xmodule.contentstore.content import StaticContent


LTI_LAUNCH_URL = 'https://piazza.com/connect'
LTI_CONSUMER_KEY = 'piazza.sandbox'
LTI_CONSUMER_SECRET = 'test_only_secret'

@login_required
@ensure_csrf_cookie
def piazza_test(request, course_id):
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


@login_required
@ensure_csrf_cookie
def course_dashboard(request, org, course, name):
    """
    Display an editable asset library

    org, course, name: Attributes of the Location for the item to edit
    """
    courseEnrollments = CourseEnrollment.objects.order_by('user').filter(course_id=org+'/'+course+'/'+name)
    
    location = get_location_and_verify_access(request, org, course, name)

    upload_asset_callback_url = reverse('upload_asset', kwargs={
        'org': org,
        'course': course,
        'coursename': name
    })

    course_module = modulestore().get_item(location)

    course_reference = StaticContent.compute_location(org, course, name)

    return render_to_response('dashboard_index.html', {
        'context_course': course_module,
        'course_reference':course_reference,
        'courseEnrollments':courseEnrollments
    })
