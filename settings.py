# Django settings for mrwf project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG
STATIC_ROOT = ''
ADMINS = () # local_settings
MANAGERS = ADMINS
DATABASES = {} # local_settings

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
#MEDIA_ROOT = (loaded from local_settings)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = (loaded from local_settings)

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = (loaded from local_settings)

# Make this unique, and don't share it with anybody.
#SECRET_KEY = (loaded from local_settings)

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

TEMPLATE_DIRS = () # (loaded from local_settings)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'cams',
    'mrwf.extra'
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': [],
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

SESSION_COOKIE_AGE = 7 * 24 * 60 * 60 # a week
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

IMG_MAX_D = 800
IMG_MAX_d = 600

# site-dependent settings
import local_settings
import os
import cams

HISTORY_PATH = os.path.join(LOG_PATH, 'history.log')

LOGGING['formatters'].update({ \
        'short': {
            'format': '%(asctime)s %(levelname)s %(message)s',
            'datefmt': '%Y.%m.%d %H.%M.%S',
            },
        'history': {
            'format': cams.history_format,
            'datefmt': cams.history_datefmt,
            },
        })

LOGGING['handlers'].update({ \
        'cams': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_PATH, 'cams.log'),
            'formatter': 'short',
            },
        'history': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': HISTORY_PATH,
            'formatter': 'history',
            },
        })

LOGGING['loggers'].update({ \
        'cams': {
            'handlers': ['cams'],
            'level': 'INFO',
            'propagate': True,
            },
        'cams.history': {
            'handlers': ['history'],
            'level': 'INFO',
            'propagate': False,
            },
        })
