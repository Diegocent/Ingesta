# -*- coding: utf-8 -*-
"""Vistas de la API de ingesta."""

import logging

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .filters import RegistroAsistenciaFilter
from .models import RegistroAsistenciaHumanitaria
from .serializers import (
    CatalogosSerializer,
    RegistroAsistenciaEscrituraSerializer,
    RegistroAsistenciaLecturaSerializer,
)
from .throttling import AutenticacionThrottle, EscrituraThrottle, LecturaThrottle

logger = logging.getLogger('ingestion')


class RegistroAsistenciaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Alta, consulta y corrección de registros de asistencia humanitaria.

    No se expone `destroy`: los registros de un organismo público no se
    eliminan, se corrigen dejando rastro en `actualizado_en`. La baja lógica
    queda para la Fase 2, junto con el circuito de aprobación.
    """

    queryset = RegistroAsistenciaHumanitaria.objects.select_related('creado_por')
    permission_classes = (IsAuthenticated,)
    filterset_class = RegistroAsistenciaFilter

    # Búsqueda libre acotada a los campos geográficos y de observaciones.
    search_fields = ('distrito', 'localidad', 'observaciones')

    # Lista blanca de ordenamiento: evita que el cliente ordene por columnas
    # sin índice y degrade la base con consultas costosas.
    ordering_fields = (
        'fecha', 'departamento', 'distrito', 'evento', 'sexo_titular',
        'es_poblacion_rural', 'cantidad_familias_asistidas', 'total_insumos',
        'creado_en',
    )
    ordering = ('-fecha', '-id')

    http_method_names = ('get', 'post', 'patch', 'head', 'options')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RegistroAsistenciaEscrituraSerializer
        return RegistroAsistenciaLecturaSerializer

    def get_throttles(self):
        clase = (
            EscrituraThrottle
            if self.request.method in ('POST', 'PATCH')
            else LecturaThrottle
        )
        return [clase()]

    def perform_create(self, serializer):
        registro = serializer.save(creado_por=self.request.user)
        logger.info(
            'Registro %s creado por %s (%s, %s, %s)',
            registro.pk,
            self.request.user.get_username(),
            registro.fecha,
            registro.departamento,
            registro.evento,
        )

    def perform_update(self, serializer):
        registro = serializer.save()
        logger.info(
            'Registro %s corregido por %s',
            registro.pk,
            self.request.user.get_username(),
        )

    def create(self, request, *args, **kwargs):
        """Devuelve el registro creado con los campos derivados ya calculados."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        salida = RegistroAsistenciaLecturaSerializer(serializer.instance)
        return Response(salida.data, status=status.HTTP_201_CREATED)


class CatalogosView(APIView):
    """Catálogo oficial de departamentos, distritos, eventos y sexos.

    El frontend lo consume para poblar sus selectores, de modo que exista una
    sola fuente de verdad de la nomenclatura.
    """

    permission_classes = (IsAuthenticated,)
    throttle_classes = (LecturaThrottle,)

    def get(self, request):
        return Response(CatalogosSerializer.datos())


class TokenView(TokenObtainPairView):
    """Emisión de tokens con cuota estricta por IP."""

    throttle_classes = (AutenticacionThrottle,)


class TokenRefrescoView(TokenRefreshView):
    """Refresco de tokens con cuota estricta por IP."""

    throttle_classes = (AutenticacionThrottle,)
