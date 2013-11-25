from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.models import User, check_password
from student.views import _do_create_account
from django.conf import settings
from student.views import activate_account
import requests
import random
import string
from django.db import connection, connections, transaction
import time
import logging

class WindBackend(object):
    """
    Authenticate token against WIND server.
    
    """

    supports_inactive_user = False

    def authenticate(self, request=None, token=None):
        post_data = {'ticketid':token}
        result = requests.get(settings.WIND_VALIDATION, params=post_data)
        content_array = result.text.split()
        if (content_array[0] == 'yes'):
            try:
                user = User.objects.prefetch_related("groups").get(email=content_array[1]+'@columbia.edu')
            except User.DoesNotExist:
                post_override = dict()
                post_override['email'] = content_array[1]+'@columbia.edu'
                post_override['name'] = content_array[1]
                post_override['username'] = content_array[1]
                post_override['password'] = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(20))
                post_override['terms_of_service'] = 'true'
                post_override['honor_code'] = 'true'
                #create_account(request, post_override)
                ret = _do_create_account(post_override)
                if isinstance(ret, HttpResponse):
                    raise Exception("Account creation failed")
                (user, profile, registration) = ret
                user.is_active = True;
                user.save()
            return user
        else:
            logging.error("Bad WIND ticket! Ticket value was: %s" % token)
            return None

class OldCVNBackend(object):
    """
    Authenticate token against WIND server.
    
    """

    supports_inactive_user = False

    def authenticate(self, user_email=None, first=None, last=None, token=None, username=None):
        if user_email is None or first is None or last is None or token is None:
            return None
        cursor = connections['cvn_php'].cursor()
        # Data retrieval operation - no commit required
        cursor.execute("SELECT unix_timestamp(created), email, token FROM django_auth_hack WHERE email=%s AND token=%s", [user_email, token])
        row = cursor.fetchone()
        if row is not None and row[0] > int(time.time())-86400:
            #if token has been found in database and was created less than 1 day ago
            try:
                user = User.objects.prefetch_related("groups").get(email=user_email)
            except User.DoesNotExist:
                post_override = dict()
                post_override['email'] = user_email
                post_override['name'] = first + ' ' + last
                post_override['username'] = user_email
                post_override['password'] = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(20))
                post_override['terms_of_service'] = 'true'
                post_override['honor_code'] = 'true'
                #create_account(request, post_override)
                ret = _do_create_account(post_override)
                if isinstance(ret, HttpResponse):  # if there was an error then return that
                    return ret
                (user, profile, registration) = ret
                user.is_active = True;
                user.save()
            return user
        return None
