import os
import settings

BASE_DIR = '/home/user/path/to/django/mrwf'

settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'mrwf.db'),
    }
}

settings.LOG_PATH = 'log'
settings.MEDIA_ROOT = os.path.join(BASE_DIR, 'upload')
settings.MEDIA_URL = '/static/mrwf/upload/'
settings.ADMIN_MEDIA_PREFIX = '/media/'
settings.TEMPLATE_DIRS += (os.path.join(BASE_DIR, 'templates'),)
settings.STATIC_ROOT = os.path.join(BASE_DIR, 'static')
settings.URL_PREFIX = '/'
settings.LOGIN_URL = settings.URL_PREFIX + 'accounts/login'
settings.LOGIN_REDIRECT_URL = settings.URL_PREFIX

#settings.SECRET_KEY = 
#settings.ADMINS += (('Name', 'name@email.com'), )

#settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#settings.EMAIL_FILE_PATH =
#settings.EMAIL_HOST = 'email.com'
#settings.EMAIL_HOST_PASSWORD =
#settings.EMAIL_HOST_USER =
#settings.EMAIL_PORT = 25
#settings.EMAIL_SUBJECT_PREFIX =
#settings.EMAIL_USE_TLS = True
