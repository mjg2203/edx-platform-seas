from .devstack import *

LOGIN_URL = '/login'

INSTALLED_APPS += ('wind','cvn_lms', 'cvn_stats', 'cvn_student')

WIND_LOGIN_URL = ENV_TOKENS.get("WIND_LOGIN_URL")
WIND_DESTINATION = ENV_TOKENS.get("WIND_DESTINATION")
WIND_VALIDATION = ENV_TOKENS.get("WIND_VALIDATION")
LMS_URL = ENV_TOKENS.get("LMS_URL")
CMS_URL = ENV_TOKENS.get("CMS_URL")
CVN_SC_URL = ENV_TOKENS.get("CVN_SC_URL")
LTI_LAUNCH_URL = ENV_TOKENS.get("LTI_LAUNCH_URL")
LTI_CONSUMER_KEY = ENV_TOKENS.get("LTI_CONSUMER_KEY")
LTI_CONSUMER_SECRET = ENV_TOKENS.get("LTI_CONSUMER_SECRET")

ENABLE_DJANGO_ADMIN_SITE = True
FEATURES['USE_CUSTOM_THEME'] = True
FEATURES['ENABLE_DISCUSSION_SERVICE'] = ENV_TOKENS.get("ENABLE_DISCUSSION_SERVICE", True)
SITE_NAME = "lms.cvn.columbia.edu"

## DATABASES['cvn_php'] = {
##         'ENGINE': 'django.db.backends.sqlite3',
##         'NAME': ENV_ROOT / "db" / "cvn_php_dev.db",
## }
## 
## DATABASES['default'] = {
##         'ENGINE': 'django.db.backends.mysql',
##         'NAME': ENV_TOKENS.get('MYSQL_DBNAME'),
##         'USER': ENV_TOKENS.get('MYSQL_USER'),
##         'PASSWORD': ENV_TOKENS.get('MYSQL_PASSWORD'),
##         'HOST': ENV_TOKENS.get('MYSQL_HOST', '127.0.0.1'),
##         'PORT': '3306',
## }

MIDDLEWARE_CLASSES += ('wind.middleware.DisableCSRF',)

MKTG_URL_LINK_MAP['FAQ'] = None

AUTHENTICATION_BACKENDS = ('wind.backends.OldCVNBackend', 'wind.backends.WindBackend', ) + AUTHENTICATION_BACKENDS

XQUEUE_INTERFACE['url']= "https://example.com"

FEATURES['AUTH_USE_OPENID'] = False
FEATURES['AUTH_USE_OPENID_PROVIDER'] = False

# must have trailing slash:    !!!                     v
CVN_ANALYTICS_URL = "http://snipe.cvn.columbia.edu:9999/"

# don't change this
CVN_ANALYTICS_PATH = "view/video_list"

CVN_ANALYTICS_USERS = (
    'mjg2203',
    'ljc2147',
)

CVN_ENABLE_PROCTOR=True
