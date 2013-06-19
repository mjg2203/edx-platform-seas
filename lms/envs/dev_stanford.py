import json

from .dev import *

with open(ENV_ROOT / "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

PLATFORM_NAME = ENV_TOKENS['PLATFORM_NAME']
SITE_NAME = ENV_TOKENS['SITE_NAME']

#Theme overrides
THEME_NAME = ENV_TOKENS.get('THEME_NAME', None)
if not THEME_NAME is None:
    enable_theme(THEME_NAME)
    FAVICON_PATH = 'themes/%s/images/favicon.ico' % THEME_NAME

TECH_SUPPORT_EMAIL = ENV_TOKENS.get('TECH_SUPPORT_EMAIL', TECH_SUPPORT_EMAIL)
CONTACT_EMAIL = ENV_TOKENS.get('CONTACT_EMAIL', CONTACT_EMAIL)
BUGS_EMAIL = ENV_TOKENS.get('BUGS_EMAIL', BUGS_EMAIL)

# Marketing link overrides
for key, value in ENV_TOKENS.get('MKTG_URL_LINK_MAP', {}).items():
    MKTG_URL_LINK_MAP[key] = value
