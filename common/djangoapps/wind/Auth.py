from django.conf import settings
from django.contrib.auth.models import User, check_password

class SettingsBackend(object):
    """
    Authenticate against the settings ADMIN_LOGIN and ADMIN_PASSWORD.

    Use the login name, and a hash of the password. For example:

    ADMIN_LOGIN = 'admin'
    ADMIN_PASSWORD = 'sha1$4e987$afbcf42e21bd417fb71db8c66b321e9fc33051de'
    """

    def authenticate(self, windticket=None):
        post_data = {'ticketid':request.GET.get('ticketid', '')}
		result = requests.get(settings.WIND_VALIDATION, params=post_data)
		content_array = result.text.split()
		if content_array[0] == 'yes'
			username = content_array[1]
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. Note that we can set password
                # to anything, because it won't be checked; the user
                # will be authenticated via WIND.
                user = User(username=username, password='randompassword')
                
                #what settings do we use?!!?!?!?!?!?
                user.is_staff = True
                user.is_superuser = True
                
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None