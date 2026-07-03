"""WSGI config for pawnshop_management project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pawnshop_management.settings')
application = get_wsgi_application()
