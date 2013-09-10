# Create your views here.
from django.conf import settings
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from markupsafe import escape

from courseware import grades
from courseware.access import has_access
from courseware.courses import (get_courses, get_course_with_access,
                                get_courses_by_university, sort_by_announcement)
import courseware.tabs as tabs
from courseware.masquerade import setup_masquerade
# from courseware.model_data import ModelDataCache
#from .module_render import toc_for_course, get_module_for_descriptor, get_module
from courseware.models import StudentModule, StudentModuleHistory

from django_comment_client.utils import get_discussion_title

from student.models import UserTestGroup, CourseEnrollment
from util.cache import cache, cache_if_anonymous
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError, ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location
from xmodule.course_module import CourseDescriptor

import comment_client


@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def proctor(request, course_id, student_id=None):
    """ User progress. We show the grade bar and every problem score.

    Course staff are allowed to see the progress of students in their class.
    """
    course = get_course_with_access(request.user, course_id, 'load', depth=None)
    staff_access = has_access(request.user, course, 'staff')

    if student_id is None or student_id == request.user.id:
        # always allowed to see your own profile
        student = request.user
    else:
        # Requesting access to a different student's profile
        if not staff_access:
            raise Http404
        student = User.objects.get(id=int(student_id))

    # NOTE: To make sure impersonation by instructor works, use
    # student instead of request.user in the rest of the function.

    # The pre-fetching of groups is done to make auth checks not require an
    # additional DB lookup (this kills the Progress page in particular).
    student = User.objects.prefetch_related("groups").get(id=student.id)

    context = {'course': course,
               'staff_access': staff_access,
               'student': student,
               }
    context.update()

    return render_to_response('courseware/proctor.html', context)
