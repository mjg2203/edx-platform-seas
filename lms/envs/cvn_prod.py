from .aws import *

# Used for dealing with sites that don't live at the "/" url path
# disabled since it breaks some JS parts of the system
# FORCE_SCRIPT_NAME = ENV_TOKENS.get("FORCE_SCRIPT_NAME")

# Add our cvn- and columbia-specific apps:
INSTALLED_APPS += ('wind','cvn_lms')

# Configure columbia authentication. These vars say WIND, but could be used for
# CAS as well
WIND_LOGIN_URL = ENV_TOKENS.get("WIND_LOGIN_URL")
WIND_DESTINATION = ENV_TOKENS.get("WIND_DESTINATION")
WIND_VALIDATION = ENV_TOKENS.get("WIND_VALIDATION")

# Need these urls for redirects
LMS_URL = ENV_TOKENS.get("LMS_URL")
CMS_URL = ENV_TOKENS.get("CMS_URL")
CVN_SC_URL = ENV_TOKENS.get("CVN_SC_URL")

# for piazza, we use the LTI standard
LTI_LAUNCH_URL = ENV_TOKENS.get("LTI_LAUNCH_URL")
LTI_CONSUMER_KEY = ENV_TOKENS.get("LTI_CONSUMER_KEY")
LTI_CONSUMER_SECRET = ENV_TOKENS.get("LTI_CONSUMER_SECRET")

# Edx uses AWS's filing and email service, we use regular old email, as well as
# regular file storage:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

ENABLE_DJANGO_ADMIN_SITE = True
MITX_FEATURES['USE_CUSTOM_THEME'] = True

SITE_NAME = "lms.cvn.columbia.edu"

DEFAULT_FROM_EMAIL = 'lms@lms.cvn.columbia.edu'
DEFAULT_FEEDBACK_EMAIL = 'lms@lms.cvn.columbia.edu'
SERVER_EMAIL = 'lms@lms.cvn.columbia.edu'
TECH_SUPPORT_EMAIL = 'lms@lms.cvn.columbia.edu'
CONTACT_EMAIL = 'lms@lms.cvn.columbia.edu'
BUGS_EMAIL = 'lms@lms.cvn.columbia.edu'
ADMINS = (("Matt", "mjg2203@columbia.edu"),)

OPEN_ENDED_GRADING_INTERFACE['url'] = 'http://example.com/peer_grading'

MIDDLEWARE_CLASSES += ('wind.middleware.DisableCSRF',)
MKTG_URL_LINK_MAP['FAQ'] = None

AUTHENTICATION_BACKENDS = ('wind.backends.OldCVNBackend', 'wind.backends.WindBackend', ) + AUTHENTICATION_BACKENDS

XQUEUE_INTERFACE['url']= "https://example.com"

MITX_FEATURES['AUTH_USE_OPENID'] = False
MITX_FEATURES['AUTH_USE_OPENID_PROVIDER'] = False
MITX_FEATURES['ENABLE_SQL_TRACKING_LOGS'] = True

LOGIN_URL = '/login'

# must have trailing slash:    !!!                     v
CVN_ANALYTICS_URL = "http://snipe.cvn.columbia.edu:9999/"

# don't change this
CVN_ANALYTICS_PATH = "view/video_list"

CVN_ANALYTICS_USERS = (
    'mjg2203',
    'ljc2147',
)
