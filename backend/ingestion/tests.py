# -*- coding: utf-8 -*-
"""Pruebas de las reglas de negocio y de los controles de acceso de la API."""

import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Origen, RegistroAsistenciaHumanitaria

REGISTRO_VALIDO = {
    'fecha': '2026-03-10',
    'departamento': 'CENTRAL',
    'distrito': 'LUQUE',
    'localidad': 'BARRIO SAN MIGUEL',
    'es_poblacion_rural': False,
    'evento': 'INUNDACION',
    'sexo_titular': 'F',
    'cantidad_familias_asistidas': 12,
    'kit_a': 10,
    'kit_b': 2,
    'chapa_zinc': 20,
}


class BaseAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='operador.sen', password='Contrasena-Segura-2026',
        )

    def setUp(self):
        self.client.force_authenticate(self.usuario)


class AltaRegistroTests(BaseAPITest):
    url = reverse('registro-list')

    def test_calcula_los_campos_derivados(self):
        respuesta = self.client.post(self.url, REGISTRO_VALIDO, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['anio'], 2026)
        self.assertEqual(respuesta.data['mes'], 3)
        self.assertEqual(respuesta.data['nombre_mes'], 'Marzo')
        self.assertEqual(respuesta.data['orden_departamento'], 11)
        self.assertEqual(respuesta.data['total_insumos'], 32)
        self.assertEqual(respuesta.data['cargado_por'], 'operador.sen')

    def test_imputa_los_kits_segun_el_evento(self):
        respuesta = self.client.post(
            self.url, {**REGISTRO_VALIDO, 'evento': 'INUNDACION'}, format='json',
        )
        self.assertEqual(respuesta.data['kit_evento'], 12)
        self.assertEqual(respuesta.data['kit_sentencia'], 0)

        respuesta = self.client.post(
            self.url,
            {**REGISTRO_VALIDO, 'evento': 'C.I.D.H.'},
            format='json',
        )
        self.assertEqual(respuesta.data['kit_sentencia'], 12)
        self.assertEqual(respuesta.data['kit_evento'], 0)

    def test_normaliza_los_textos_geograficos(self):
        respuesta = self.client.post(
            self.url,
            {**REGISTRO_VALIDO, 'distrito': '  luque ', 'localidad': 'zona   norte'},
            format='json',
        )
        self.assertEqual(respuesta.data['distrito'], 'LUQUE')
        self.assertEqual(respuesta.data['localidad'], 'ZONA NORTE')

    def test_descarta_los_campos_derivados_enviados_por_el_cliente(self):
        """Los campos calculados son de solo lectura (asignación masiva)."""
        respuesta = self.client.post(
            self.url,
            {
                **REGISTRO_VALIDO,
                'total_insumos': 999_999,
                'kit_sentencia': 999_999,
                'orden_departamento': 1,
                'creado_por': 1,
            },
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['total_insumos'], 32)
        self.assertEqual(respuesta.data['kit_sentencia'], 0)
        self.assertEqual(respuesta.data['orden_departamento'], 11)


class ValidacionTests(BaseAPITest):
    url = reverse('registro-list')

    def test_rechaza_distrito_de_otro_departamento(self):
        respuesta = self.client.post(
            self.url,
            {**REGISTRO_VALIDO, 'departamento': 'CENTRAL', 'distrito': 'PILAR'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('distrito', respuesta.data)

    def test_rechaza_registro_sin_insumos(self):
        sin_insumos = {
            campo: valor for campo, valor in REGISTRO_VALIDO.items()
            if campo not in ('kit_a', 'kit_b', 'chapa_zinc')
        }
        respuesta = self.client.post(self.url, sin_insumos, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rechaza_cero_familias_asistidas(self):
        respuesta = self.client.post(
            self.url,
            {**REGISTRO_VALIDO, 'cantidad_familias_asistidas': 0},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cantidad_familias_asistidas', respuesta.data)

    def test_rechaza_cantidades_negativas(self):
        respuesta = self.client.post(
            self.url, {**REGISTRO_VALIDO, 'colchones': -5}, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rechaza_fecha_futura(self):
        manana = datetime.date.today() + datetime.timedelta(days=1)
        respuesta = self.client.post(
            self.url, {**REGISTRO_VALIDO, 'fecha': manana.isoformat()}, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha', respuesta.data)

    def test_rechaza_etiquetas_html_en_observaciones(self):
        respuesta = self.client.post(
            self.url,
            {**REGISTRO_VALIDO, 'observaciones': '<script>alert(1)</script>'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('observaciones', respuesta.data)

    def test_rechaza_evento_fuera_de_catalogo(self):
        respuesta = self.client.post(
            self.url, {**REGISTRO_VALIDO, 'evento': 'TERREMOTO'}, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)


class ListadoTests(BaseAPITest):
    url = reverse('registro-list')

    def setUp(self):
        super().setUp()
        self.client.post(self.url, REGISTRO_VALIDO, format='json')
        self.client.post(
            self.url,
            {
                **REGISTRO_VALIDO,
                'departamento': 'BOQUERON',
                'distrito': 'FILADELFIA',
                'es_poblacion_rural': True,
                'sexo_titular': 'M',
                'evento': 'SEQUIA',
            },
            format='json',
        )

    def test_pagina_del_lado_del_servidor(self):
        respuesta = self.client.get(self.url, {'page_size': 1})
        self.assertEqual(respuesta.data['count'], 2)
        self.assertEqual(len(respuesta.data['results']), 1)
        self.assertIsNotNone(respuesta.data['next'])

    def test_acota_el_tamano_de_pagina_solicitado(self):
        respuesta = self.client.get(self.url, {'page_size': 100_000})
        self.assertLessEqual(len(respuesta.data['results']), 200)

    def test_filtra_por_zona_rural(self):
        respuesta = self.client.get(self.url, {'es_poblacion_rural': 'true'})
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['zona'], 'Rural')

    def test_filtra_por_sexo_del_titular(self):
        respuesta = self.client.get(self.url, {'sexo_titular': 'M'})
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(
            respuesta.data['results'][0]['sexo_titular_etiqueta'], 'Masculino',
        )

    def test_rechaza_valores_de_filtro_fuera_de_catalogo(self):
        respuesta = self.client.get(self.url, {'departamento': 'NARNIA'})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ordena_por_columna_permitida(self):
        respuesta = self.client.get(self.url, {'ordering': 'departamento'})
        departamentos = [fila['departamento'] for fila in respuesta.data['results']]
        self.assertEqual(departamentos, ['BOQUERON', 'CENTRAL'])

    def test_ignora_ordenamiento_por_columna_no_permitida(self):
        respuesta = self.client.get(self.url, {'ordering': 'creado_por__password'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)


class ControlDeAccesoTests(APITestCase):
    def test_exige_autenticacion_en_el_listado(self):
        respuesta = self.client.get(reverse('registro-list'))
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_exige_autenticacion_en_el_alta(self):
        respuesta = self.client.post(
            reverse('registro-list'), REGISTRO_VALIDO, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(RegistroAsistenciaHumanitaria.objects.exists())

    def test_no_permite_eliminar_registros(self):
        usuario = get_user_model().objects.create_user(
            username='auditor', password='Contrasena-Segura-2026',
        )
        self.client.force_authenticate(usuario)
        self.client.post(reverse('registro-list'), REGISTRO_VALIDO, format='json')
        registro = RegistroAsistenciaHumanitaria.objects.get()

        respuesta = self.client.delete(
            reverse('registro-detail', args=[registro.pk])
        )
        self.assertEqual(
            respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_emite_token_con_credenciales_validas(self):
        get_user_model().objects.create_user(
            username='operador', password='Contrasena-Segura-2026',
        )
        respuesta = self.client.post(
            reverse('token-obtener'),
            {'username': 'operador', 'password': 'Contrasena-Segura-2026'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('access', respuesta.data)
        self.assertIn('refresh', respuesta.data)


class CatalogosTests(BaseAPITest):
    def test_expone_el_catalogo_oficial(self):
        respuesta = self.client.get(reverse('catalogos'))

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data['departamentos']), 18)
        self.assertEqual(respuesta.data['departamentos'][0]['valor'], 'CONCEPCIÓN')
        self.assertIn(
            'LUQUE', respuesta.data['distritos_por_departamento']['CENTRAL'],
        )
        self.assertEqual(len(respuesta.data['eventos']), 10)


class HistoricoTests(BaseAPITest):
    """Convivencia entre el histórico importado y las cargas por formulario.

    La planilla histórica no releva la caracterización de beneficiarios, así
    que esas columnas admiten NULL. Estas pruebas fijan el límite de esa
    concesión: vale solo para el origen `EXCEL_HISTORICO`.
    """

    url = reverse('registro-list')

    def crear_historico(self, **extras):
        datos = {
            'fecha': datetime.date(2017, 5, 20),
            'departamento': 'CENTRAL',
            'distrito': 'LUQUE',
            'localidad': 'SIN ESPECIFICAR',
            'evento': 'SIN EVENTO',
            'origen': Origen.EXCEL_HISTORICO,
            'kit_a': 5,
        }
        return RegistroAsistenciaHumanitaria.objects.create(**{**datos, **extras})

    def test_admite_historico_sin_caracterizacion_ni_fecha_de_la_serie(self):
        registro = self.crear_historico()

        self.assertIsNone(registro.sexo_titular)
        self.assertIsNone(registro.es_poblacion_rural)
        self.assertIsNone(registro.cantidad_familias_asistidas)
        self.assertIsNone(registro.creado_por)
        self.assertEqual(registro.total_insumos, 5)
        self.assertEqual(registro.kit_evento, 5)

    def test_informa_los_datos_ausentes_como_no_informado(self):
        self.crear_historico()

        respuesta = self.client.get(self.url)

        fila = respuesta.data['results'][0]
        self.assertEqual(fila['origen'], Origen.EXCEL_HISTORICO)
        self.assertEqual(fila['zona'], 'No informado')
        self.assertEqual(fila['sexo_titular_etiqueta'], 'No informado')

    def test_la_base_rechaza_una_carga_de_formulario_incompleta(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_historico(origen=Origen.FORMULARIO,
                                 fecha=datetime.date(2026, 5, 20),
                                 evento='INUNDACION')

    def test_la_api_exige_la_caracterizacion_completa(self):
        campos = ('sexo_titular', 'es_poblacion_rural',
                  'cantidad_familias_asistidas')

        for campo in campos:
            with self.subTest(campo=campo):
                datos = {k: v for k, v in REGISTRO_VALIDO.items() if k != campo}
                respuesta = self.client.post(self.url, datos, format='json')

                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(campo, respuesta.data)

            with self.subTest(campo=campo, valor='null'):
                respuesta = self.client.post(
                    self.url, {**REGISTRO_VALIDO, campo: None}, format='json',
                )

                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(campo, respuesta.data)

    def test_rechaza_el_evento_historico_en_una_carga_por_formulario(self):
        respuesta = self.client.post(
            self.url, {**REGISTRO_VALIDO, 'evento': 'SIN EVENTO'}, format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('evento', respuesta.data)

    def test_rechaza_una_carga_por_formulario_anterior_a_la_serie(self):
        respuesta = self.client.post(
            self.url, {**REGISTRO_VALIDO, 'fecha': '2017-05-20'}, format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha', respuesta.data)
