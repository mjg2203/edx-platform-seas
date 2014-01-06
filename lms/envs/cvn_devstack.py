from .devstack import *

# THEME BROKEN!
# sass runs as:

### sass --style compressed --cache-location /tmp/sass-cache --load-path ./common/static/sass --update -E utf-8 */static

# When it should run as:

###  sass --style compressed --cache-location /tmp/sass-cache --load-path ./themes/stanford/static/sass/ --load-path ./common/static/sass --update -E utf-8 */static

with open(CONFIG_ROOT / "cvn_" + CONFIG_PREFIX + "env.json") as env_file:
    CVN_ENV_TOKENS = json.load(env_file)

## THEME_NAME=CVN_ENV_TOKENS.get('THEME_NAME')
## 
## enable_theme(THEME_NAME)
## FAVICON_PATH = 'themes/%s/images/favicon.ico' % THEME_NAME

LOGIN_URL = '/login'

INSTALLED_APPS += ('wind','cvn_lms', 'cvn_stats', 'cvn_student')

WIND_LOGIN_URL = CVN_ENV_TOKENS.get("WIND_LOGIN_URL")
WIND_DESTINATION = CVN_ENV_TOKENS.get("WIND_DESTINATION")
WIND_VALIDATION = CVN_ENV_TOKENS.get("WIND_VALIDATION")
LMS_URL = CVN_ENV_TOKENS.get("LMS_URL")
CMS_URL = CVN_ENV_TOKENS.get("CMS_URL")
CVN_SC_URL = CVN_ENV_TOKENS.get("CVN_SC_URL")
LTI_LAUNCH_URL = CVN_ENV_TOKENS.get("LTI_LAUNCH_URL")
LTI_CONSUMER_KEY = CVN_ENV_TOKENS.get("LTI_CONSUMER_KEY")
LTI_CONSUMER_SECRET = CVN_ENV_TOKENS.get("LTI_CONSUMER_SECRET")

ENABLE_DJANGO_ADMIN_SITE = True
FEATURES['USE_CUSTOM_THEME'] = True
FEATURES['ENABLE_DISCUSSION_SERVICE'] = CVN_ENV_TOKENS.get("ENABLE_DISCUSSION_SERVICE", True)
SITE_NAME = "lms.cvn.columbia.edu"

## DATABASES['cvn_php'] = {
##         'ENGINE': 'django.db.backends.sqlite3',
##         'NAME': ENV_ROOT / "db" / "cvn_php_dev.db",
## }
## 
## DATABASES['default'] = {
##         'ENGINE': 'django.db.backends.mysql',
##         'NAME': CVN_ENV_TOKENS.get('MYSQL_DBNAME'),
##         'USER': CVN_ENV_TOKENS.get('MYSQL_USER'),
##         'PASSWORD': CVN_ENV_TOKENS.get('MYSQL_PASSWORD'),
##         'HOST': CVN_ENV_TOKENS.get('MYSQL_HOST', '127.0.0.1'),
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
