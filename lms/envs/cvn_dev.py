from .dev import *
from .cms.dev import *
import json

with open(ENV_ROOT / "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

THEME_NAME=ENV_TOKENS.get('THEME_NAME')

enable_theme(THEME_NAME)
FAVICON_PATH = 'themes/%s/images/favicon.ico' % THEME_NAME


INSTALLED_APPS += ('wind','cvn')
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
MITX_FEATURES['USE_CUSTOM_THEME'] = True

SITE_NAME = "lms.cvn.columbia.edu"

DATABASES['cvn_php'] = {
    "HOST": 'example.com',
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'joaquin',
    'USER': 'joaquin',
    'PASSWORD': 'PASSWORD_REDACTED'
}

MIDDLEWARE_CLASSES += ('wind.middleware.DisableCSRF',)

MKTG_URL_LINK_MAP['FAQ'] = None

AUTHENTICATION_BACKENDS = ('wind.backends.OldCVNBackend', 'wind.backends.WindBackend', ) + AUTHENTICATION_BACKENDS

XQUEUE_INTERFACE['url']= "https://example.com"

MITX_FEATURES['AUTH_USE_OPENID'] = False
MITX_FEATURES['AUTH_USE_OPENID_PROVIDER'] = False
