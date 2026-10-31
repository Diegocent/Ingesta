# -*- coding: utf-8 -*-
"""Serializers de la ingesta de asistencia humanitaria.

Ambos serializers declaran `fields` como lista blanca explícita. No se usa
`fields = '__all__'`: eso ataría el contrato de la API a la forma del modelo y
abriría la puerta a asignación masiva cada vez que se agregue una columna
interna (por ejemplo, un campo de estado de aprobación en la Fase 2).
"""

import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .catalogos import (
    DEPARTAMENTO_ORDEN,
    EVENTOS,
    SIN_ESPECIFICAR,
    distritos_de,
    normalizar_texto,
)
from .models import RegistroAsistenciaHumanitaria, SexoTitular

# Campos de nomenclatura que se llevan al formato del Data Warehouse
# (mayúsculas, sin espacios redundantes) antes de validarlos.
CAMPOS_NORMALIZABLES = ('departamento', 'distrito', 'localidad', 'evento')

# Columnas que el modelo calcula en `save()`. El cliente no puede escribirlas.
CAMPOS_DERIVADOS = (
    'anio', 'mes', 'nombre_mes', 'orden_departamento',
    'kit_sentencia', 'kit_evento', 'total_insumos',
)

CAMPOS_AUDITORIA = ('id', 'creado_por', 'creado_en', 'actualizado_en')

CAMPOS_INSUMOS = (
    'kit_a', 'kit_b', 'chapa_fibrocemento', 'chapa_zinc', 'colchones',
    'frazadas', 'terciadas', 'puntales', 'carpas_plasticas',
)

# Etiqueta única para los datos ausentes del histórico de Excel.
SIN_INFORMAR = 'No informado'


class RegistroAsistenciaEscrituraSerializer(serializers.ModelSerializer):
    """Serializer de alta y corrección de registros.

    Los tres campos de caracterización admiten NULL en la base para alojar la
    importación histórica de Excel, pero por la API son obligatorios: quien
    carga desde el formulario tiene el dato a la vista y debe informarlo.
    """

    es_poblacion_rural = serializers.BooleanField(required=True)
    sexo_titular = serializers.ChoiceField(
        choices=SexoTitular.choices, required=True, allow_null=False,
    )
    cantidad_familias_asistidas = serializers.IntegerField(
        required=True, allow_null=False, min_value=1,
    )

    class Meta:
        model = RegistroAsistenciaHumanitaria
        fields = (
            'id',
            'fecha',
            'departamento',
            'distrito',
            'localidad',
            'es_poblacion_rural',
            'evento',
            'sexo_titular',
            'cantidad_familias_asistidas',
            *CAMPOS_INSUMOS,
            'observaciones',
            *CAMPOS_DERIVADOS,
            'creado_en',
        )
        read_only_fields = ('id', *CAMPOS_DERIVADOS, 'creado_en')

    # -- Saneamiento de entrada ---------------------------------------------
    def to_internal_value(self, data):
        """Normaliza los textos antes de que corran los validadores de campo.

        El saneamiento tiene que ocurrir en este punto y no en `validate_*`:
        los validadores declarados en el modelo (que exigen mayúsculas) se
        ejecutan primero y rechazarían una entrada correcta escrita en
        minúsculas, que es lo natural al tipear en un formulario.
        """
        if isinstance(data, dict):
            data = {
                clave: (
                    normalizar_texto(valor)
                    if clave in CAMPOS_NORMALIZABLES and isinstance(valor, str)
                    else valor
                )
                for clave, valor in data.items()
            }
            if not data.get('localidad'):
                data['localidad'] = SIN_ESPECIFICAR
        return super().to_internal_value(data)

    def validate_observaciones(self, valor):
        return (valor or '').strip()

    def validate(self, attrs):
        """Delega la validación de negocio en `Model.clean()`.

        Mantener una sola implementación de las reglas evita que la API y el
        panel de administración divergan. Las restricciones de base de datos
        se excluyen porque dependen de campos derivados que aún no se
        calcularon; `clean()` ya valida sus equivalentes.
        """
        instancia = self._instancia_candidata(attrs)
        try:
            instancia.full_clean(
                exclude=(*CAMPOS_DERIVADOS, 'creado_por'),
                validate_constraints=False,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                serializers.as_serializer_error(exc)
            )
        return attrs

    def _instancia_candidata(self, attrs):
        """Construye la instancia resultante sin persistirla."""
        if self.instance is None:
            return RegistroAsistenciaHumanitaria(**attrs)

        instancia = copy.copy(self.instance)
        for campo, valor in attrs.items():
            setattr(instancia, campo, valor)
        return instancia


class RegistroAsistenciaLecturaSerializer(serializers.ModelSerializer):
    """Serializer de la tabla de datos: incluye etiquetas legibles."""

    sexo_titular_etiqueta = serializers.SerializerMethodField()
    zona = serializers.SerializerMethodField()
    tipo_poblacion = serializers.SerializerMethodField()
    cargado_por = serializers.SerializerMethodField()

    class Meta:
        model = RegistroAsistenciaHumanitaria
        fields = (
            'id',
            'fecha',
            'anio',
            'mes',
            'nombre_mes',
            'departamento',
            'orden_departamento',
            'distrito',
            'localidad',
            'es_poblacion_rural',
            'zona',
            'es_poblacion_indigena',
            'tipo_poblacion',
            'evento',
            'sexo_titular',
            'sexo_titular_etiqueta',
            'cantidad_familias_asistidas',
            *CAMPOS_INSUMOS,
            'kit_sentencia',
            'kit_evento',
            'total_insumos',
            'observaciones',
            'origen',
            'cargado_por',
            'creado_en',
        )
        read_only_fields = fields

    def get_sexo_titular_etiqueta(self, obj) -> str:
        return obj.get_sexo_titular_display() or SIN_INFORMAR

    def get_zona(self, obj) -> str:
        """Distingue los tres estados posibles, incluido el «no informado».

        Los registros históricos no tienen el dato, y presentarlos como
        «Urbana» sería afirmar algo que nunca se relevó.
        """
        if obj.es_poblacion_rural is None:
            return SIN_INFORMAR
        return 'Rural' if obj.es_poblacion_rural else 'Urbana'

    def get_tipo_poblacion(self, obj) -> str:
        if obj.es_poblacion_indigena is None:
            return SIN_INFORMAR
        return 'Indígena' if obj.es_poblacion_indigena else 'No indígena'

    def get_cargado_por(self, obj):
        return obj.creado_por.get_username() if obj.creado_por_id else None


class CatalogosSerializer(serializers.Serializer):
    """Contrato del endpoint de catálogos que alimenta los selectores."""

    departamentos = serializers.ListField(child=serializers.DictField())
    distritos_por_departamento = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
    )
    eventos = serializers.ListField(child=serializers.CharField())
    sexos = serializers.ListField(child=serializers.DictField())

    @staticmethod
    def datos():
        """Arma el catálogo oficial en el orden en que debe mostrarse."""
        return {
            'departamentos': [
                {'valor': nombre, 'orden': orden}
                for nombre, orden in sorted(
                    DEPARTAMENTO_ORDEN.items(), key=lambda par: par[1]
                )
            ],
            'distritos_por_departamento': {
                departamento: sorted(distritos_de(departamento))
                for departamento in DEPARTAMENTO_ORDEN
            },
            'eventos': list(EVENTOS),
            'sexos': [
                {'valor': valor, 'etiqueta': etiqueta}
                for valor, etiqueta in
                RegistroAsistenciaHumanitaria._meta.get_field(
                    'sexo_titular'
                ).choices
            ],
        }
