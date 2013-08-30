from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.models import User, check_password
from student.views import _do_create_account
from django.conf import settings
from student.views import activate_account
import requests

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
                if isinstance(ret, HttpResponse):  # if there was an error then return that
                    return ret
                (user, profile, registration) = ret
                user.is_active = True;
                user.save()
            return user
        return None

    def get_user(self, user_email):
        try:
            return User.objects.get(email=user_email)
        except User.DoesNotExist:
            return None