from .dev import *

import json
with open(ENV_ROOT / "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

INSTALLED_APPS += ('wind','cvn_cms')
LMS_URL = ENV_TOKENS.get("LMS_URL")
LTI_LAUNCH_URL = ENV_TOKENS.get("LTI_LAUNCH_URL")
LTI_CONSUMER_KEY = ENV_TOKENS.get("LTI_CONSUMER_KEY")
LTI_CONSUMER_SECRET = ENV_TOKENS.get("LTI_CONSUMER_SECRET")

MITX_FEATURES['ENABLE_CREATOR_GROUP'] = True

DEFAULT_FROM_EMAIL = 'lms@lms.cvn.columbia.edu'
DEFAULT_FEEDBACK_EMAIL = 'lms@lms.cvn.columbia.edu'
SERVER_EMAIL = 'lms@lms.cvn.columbia.edu'

DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': ENV_TOKENS.get('MYSQL_DBNAME'),
        'USER': ENV_TOKENS.get('MYSQL_USER'),
        'PASSWORD': ENV_TOKENS.get('MYSQL_PASSWORD'),
        'HOST': ENV_TOKENS.get('MYSQL_HOST', '127.0.0.1'),
        'PORT': '3306',
}
