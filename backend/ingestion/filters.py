# -*- coding: utf-8 -*-
"""Filtros del endpoint de listado.

Los filtros de nomenclatura se declaran como `ChoiceFilter` contra el catálogo
oficial: un valor fuera del catálogo devuelve 400 y nunca llega al ORM. Esto
cierra la puerta a que el cliente controle el contenido de una cláusula WHERE,
además de dar mensajes de error útiles al operador.
"""

import django_filters as filters

from .models import (
    Departamento,
    Evento,
    Origen,
    RegistroAsistenciaHumanitaria,
    SexoTitular,
)


class RegistroAsistenciaFilter(filters.FilterSet):
    """Filtros disponibles para `GET /api/v1/registros/`."""

    fecha_desde = filters.DateFilter(field_name='fecha', lookup_expr='gte')
    fecha_hasta = filters.DateFilter(field_name='fecha', lookup_expr='lte')

    departamento = filters.ChoiceFilter(choices=Departamento.choices)
    evento = filters.ChoiceFilter(choices=Evento.choices)
    sexo_titular = filters.ChoiceFilter(choices=SexoTitular.choices)
    es_poblacion_rural = filters.BooleanFilter()
    es_poblacion_indigena = filters.BooleanFilter()

    # El distrito es texto libre validado; se compara sin distinguir
    # mayúsculas para no obligar al operador a replicar el formato del DW.
    distrito = filters.CharFilter(lookup_expr='iexact')
    localidad = filters.CharFilter(lookup_expr='icontains')

    familias_min = filters.NumberFilter(
        field_name='cantidad_familias_asistidas', lookup_expr='gte',
    )
    familias_max = filters.NumberFilter(
        field_name='cantidad_familias_asistidas', lookup_expr='lte',
    )

    # Separa las cargas del formulario de los registros importados de la
    # planilla histórica, que no tienen caracterización de beneficiarios.
    origen = filters.ChoiceFilter(choices=Origen.choices)

    class Meta:
        model = RegistroAsistenciaHumanitaria
        fields = (
            'fecha', 'fecha_desde', 'fecha_hasta', 'anio', 'mes',
            'departamento', 'distrito', 'localidad', 'evento',
            'es_poblacion_rural', 'es_poblacion_indigena', 'sexo_titular',
            'familias_min', 'familias_max', 'origen',
        )
