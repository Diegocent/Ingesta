# -*- coding: utf-8 -*-
"""Rutas de la API de ingesta (versión 1)."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CatalogosView,
    RegistroAsistenciaViewSet,
    TokenRefrescoView,
    TokenView,
)

router = DefaultRouter()
router.register('registros', RegistroAsistenciaViewSet, basename='registro')

urlpatterns = [
    path('auth/token/', TokenView.as_view(), name='token-obtener'),
    path('auth/token/refresh/', TokenRefrescoView.as_view(), name='token-refrescar'),
    path('catalogos/', CatalogosView.as_view(), name='catalogos'),
    *router.urls,
]
