import settings

settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db',
        'USER': 'dbuser',
        'PASSWORD': 'pwd',
        'HOST': 'localhost',
        'PORT': ''
    }
}

#settings.MEDIA_ROOT = 
#settings.MEDIA_URL = 
#settings.ADMIN_MEDIA_PREFIX = 
#settings.TEMPLATE_DIRS += ('/path/',)
#settings.STATIC_ROOT = 
#settings.SECRET_KEY = 
#settings.ADMINS += (('Name', 'name@email.com'), )

#settings.URL_PREFIX = '/'
#settings.LOGIN_URL = settings.URL_PREFIX + 'accounts/login'
#settings.LOGIN_REDIRECT_URL = settings.URL_PREFIX

#settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#settings.EMAIL_FILE_PATH =
#settings.EMAIL_HOST = 'email.com'
#settings.EMAIL_HOST_PASSWORD =
#settings.EMAIL_HOST_USER =
#settings.EMAIL_PORT = 25
#settings.EMAIL_SUBJECT_PREFIX =
#settings.EMAIL_USE_TLS = True
