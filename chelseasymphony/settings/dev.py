from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '73eo5$^ao97b0o86f&m$)e%q+1(^j*z4fkun&d*4ks=yy2d$ut'

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PAYPAL_ACCT_EMAIL = 'info-facilitator@example.org'
DONATION_EMAIL_ADDR = 'donations-test@example.org'

try:
    from .local import *
except ImportError:
    pass
