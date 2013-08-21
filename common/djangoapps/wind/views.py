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

from student.models import UserProfile

from django.contrib.auth.models import User

from django.conf import settings

from ims_lti_py import ToolConsumer, ToolConfig,\
        OutcomeRequest, OutcomeResponse
import hashlib
from student.views import course_from_id

def login(request):
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))
    if 'ticketid' not in request.GET:
        return redirect(settings.WIND_LOGIN_URL + "?destination=" + settings.WIND_DESTINATION)
        '''template = loader.get_template('wind/index.html')
        context = RequestContext(request, {})
        return HttpResponse(template.render(context))'''
    else:
        '''
        post_data = [('ticketid',request.GET.get('ticketid', '')),]     # a sequence of two element tuples
        result = urllib2.urlopen('http://400pixels.net/fakewind/fake_wind_validation.php?'+urllib.urlencode(post_data))
        content = result.read()
        return HttpResponse('Validation Successful!<br />Contents of ticket validation response:<br />'+content if 'yes' in content else 'Validation Failed!<br />Contents of ticket validation response:<br />'+content);
        #return HttpResponse("There's a GET message! ticketid is " +request.GET.get('ticketid', ""))
        '''
        post_data = {'ticketid':request.GET.get('ticketid', '')}
        result = requests.get(settings.WIND_VALIDATION, params=post_data)
        content_array = result.text.split()
        #return HttpResponse(content_array[0]=='yes')
        
        #return redirect(reverse('dashboard'))
        if (content_array[0] == 'yes'):
            try:
                user = User.objects.get(email=content_array[1]+'@columbia.edu')
            except User.DoesNotExist:
                post_override = dict()
                post_override['email'] = content_array[1]+'@columbia.edu'
                post_override['name'] = content_array[1]
                post_override['username'] = content_array[1]
                post_override['password'] = 'secret'
                post_override['terms_of_service'] = 'true'
                post_override['honor_code'] = 'true'
                #create_account(request, post_override)
                ret = _do_create_account(post_override)
                if isinstance(ret, HttpResponse):  # if there was an error then return that
                    return ret
                (user, profile, registration) = ret
                activate_account(request, registration.activation_key)
            
            request.POST = request.POST.copy()
            
            #newrequest = request.copy()
            #request.POST = dict()
            
            request.POST['email'] = content_array[1]+'@columbia.edu'
            
            request.POST['password'] = 'secret'

            #return HttpResponse(content_array[1]+'@columbia.edu')
            login_user(request)
            return redirect(reverse('dashboard'))
            #return HttpResponse("User does not exist!"); 

            

            #return HttpResponse('Validation Successful!<br />Contents of ticket validation response:<br />'+' '.join(content_array))
        else:
            return HttpResponse('Validation Failed!<br />Contents of ticket validation response:<br />'+content_array[0])
            #return HttpResponse("There's a GET message! ticketid is " +request.GET.get('ticketid', ""))
        
    
def fakewind(request):
    return HttpResponse("Hello, world. You're at fake WIND.")

def register(request):
    return redirect("http://cvn.columbia.edu/");

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
    result = requests.post(launch_url, params=launch_data)
    return HttpResponse(result.text)
