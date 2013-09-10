from .dev import *

import json
with open(ENV_ROOT / "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

INSTALLED_APPS += ('wind','cvncms')
LMS_URL = ENV_TOKENS.get("LMS_URL")
LTI_LAUNCH_URL = ENV_TOKENS.get("LTI_LAUNCH_URL")
LTI_CONSUMER_KEY = ENV_TOKENS.get("LTI_CONSUMER_KEY")
LTI_CONSUMER_SECRET = ENV_TOKENS.get("LTI_CONSUMER_SECRET")
