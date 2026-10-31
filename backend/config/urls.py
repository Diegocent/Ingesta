# -*- coding: utf-8 -*-
"""Ruteo raíz del sistema de ingesta."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/v1/', include('ingestion.urls')),
]

# El panel de administración solo se publica si se habilita explícitamente:
# en producción conviene servirlo por una red restringida o no exponerlo.
if settings.DEBUG or getattr(settings, 'HABILITAR_ADMIN', False):
    urlpatterns.append(path('admin/', admin.site.urls))
