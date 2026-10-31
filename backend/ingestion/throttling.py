# -*- coding: utf-8 -*-
"""Límites de tasa de la API.

Se separan tres cuotas porque el perfil de riesgo de cada una es distinto:

* `lectura`: consultas del dashboard y de la tabla de datos.
* `escritura`: alta de registros; más restrictiva porque cada petición implica
  una transacción en el Data Warehouse.
* `autenticacion`: obtención de tokens; es la cuota más baja porque protege
  contra fuerza bruta y relleno de credenciales.

Las cuotas se identifican por usuario cuando hay sesión válida y por dirección
IP cuando no la hay. DRF devuelve 429 con la cabecera `Retry-After` calculada a
partir de la ventana configurada.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LecturaThrottle(UserRateThrottle):
    scope = 'lectura'


class EscrituraThrottle(UserRateThrottle):
    scope = 'escritura'


class AutenticacionThrottle(AnonRateThrottle):
    """Cuota por IP para los endpoints de emisión y refresco de tokens."""

    scope = 'autenticacion'
