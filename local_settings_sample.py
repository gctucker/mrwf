# MRWF - local_settings_sample.py
#
# Copyright (C) 2009, 2010, 2011. 2012, 2013
# Guillaume Tucker <guillaume@mangoz.org>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

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
