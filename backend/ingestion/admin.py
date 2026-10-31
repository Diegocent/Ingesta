# -*- coding: utf-8 -*-
"""Panel de administración de la ingesta."""

from django.contrib import admin

from .models import RegistroAsistenciaHumanitaria
from .serializers import CAMPOS_DERIVADOS


@admin.register(RegistroAsistenciaHumanitaria)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = (
        'fecha', 'departamento', 'distrito', 'evento', 'zona',
        'sexo_titular', 'cantidad_familias_asistidas', 'total_insumos',
    )
    list_filter = (
        'departamento', 'evento', 'es_poblacion_rural',
        'es_poblacion_indigena', 'sexo_titular', 'anio',
    )
    search_fields = ('distrito', 'localidad')
    date_hierarchy = 'fecha'
    readonly_fields = (*CAMPOS_DERIVADOS, 'creado_por', 'creado_en', 'actualizado_en')

    @admin.display(description='zona', boolean=False)
    def zona(self, obj):
        return 'Rural' if obj.es_poblacion_rural else 'Urbana'

    def has_delete_permission(self, request, obj=None):
        """Los registros no se eliminan: se corrigen."""
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
