# Django settings for mrwf project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG
STATIC_ROOT = ''
ADMINS = () # (loaded from site.conf)
MANAGERS = ADMINS
DATABASES = {} # (loaded from site.conf)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
#MEDIA_ROOT = (loaded from site.conf)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = (loaded from site.conf)

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = (loaded from site.conf)

# Make this unique, and don't share it with anybody.
#SECRET_KEY = (loaded from site.conf)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'mrwf.urls'

TEMPLATE_DIRS = () # (loaded from site.conf)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'cams.abook',
    'cams.mgmt',
)

# -----------------------------------------------------------------------------
# site-dependent configuration (site.conf)

from ConfigParser import SafeConfigParser

conf = SafeConfigParser ()
conf.read ('site.conf')

if conf.has_section ('database'):
    default = {}
    db_conf = conf.items ('database')
    for (k, v) in db_conf:
        default[k.upper ()] = v
    DATABASES = {'default': default}

if conf.has_section ('paths'):
    paths = conf.items ('paths')
    for (k, v) in paths:
        if k == 'python':
            import sys
            sys.path.append (v)
        elif k == 'url_prefix':
            URL_PREFIX = v
        elif k == 'path_prefix':
            PATH_PREFIX = v
        elif k == 'media_root':
            MEDIA_ROOT = v
        elif k == 'media_url':
            MEDIA_URL = v
        elif k == 'admin_media_prefix':
            ADMIN_MEDIA_PREFIX = v
        elif k == 'templates':
            TEMPLATE_DIRS += (v, )
        elif k == 'static_root':
            STATIC_ROOT = v

if conf.has_section ('extra'):
    extras = conf.items ('extra')
    admin_name = ''
    for (k, v) in extras:
        if k == 'secret_key':
            SECRET_KEY = v
        elif k == 'debug':
            DEBUG = (v == 'true')
        elif k == 'admin_name':
            admin_name = v
        elif k == 'admin_email' and admin_name:
            ADMINS += ((admin_name, v), )
