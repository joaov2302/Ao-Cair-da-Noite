"""Configuração obrigatória para as rodadas PostgreSQL isoladas."""
import os
import re
from .settings import *  # noqa: F403

database_name = os.environ.get('POSTGRES_DB', '')
if not re.fullmatch(r'acdn_(api|e2e)_[0-9a-f]{12}', database_name):
    raise RuntimeError('Use scripts/test_env.py: banco sintético exclusivo obrigatório.')
if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise RuntimeError('Os testes isolados exigem PostgreSQL.')
DATABASES['default']['TEST'] = {'NAME': 'test_' + database_name}
DATABASES['default']['OPTIONS'] = {'options': '-c lock_timeout=10000 -c statement_timeout=30000'}
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:5175']
SESSION_COOKIE_NAME = 'acdn_e2e_session'
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
