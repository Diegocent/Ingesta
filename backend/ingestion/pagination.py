# -*- coding: utf-8 -*-
"""Paginación del lado del servidor para la tabla de datos."""

from rest_framework.pagination import PageNumberPagination


class PaginacionEstandar(PageNumberPagination):
    """Paginación por número de página, controlable desde el cliente.

    `max_page_size` acota cuántos registros puede pedir un cliente en una sola
    petición: sin ese techo, `?page_size=100000` sería un vector trivial de
    agotamiento de recursos.
    """

    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200
