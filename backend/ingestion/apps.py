# -*- coding: utf-8 -*-
"""Configuración de la app de ingesta."""

from django.apps import AppConfig


class IngestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ingestion'
    verbose_name = 'Ingesta de asistencia humanitaria'
