# -*- coding: utf-8 -*-
"""Modelo transaccional de ingesta de asistencia humanitaria.

Esta tabla reemplaza la planilla `registros_historicos.xlsx` como fuente de
datos del proyecto BI. Se ubica en el mismo motor PostgreSQL que el Data
Warehouse para que el proceso de carga a `hechos_asistencia_humanitaria` sea una
consulta SQL directa, sin exportaciones intermedias.

Decisiones de diseño relevantes:

* Los 14 campos heredados de la planilla se conservan con la misma semántica
  (fecha, ubicación, evento y las nueve cantidades de insumos).
* Los campos derivados que el ETL calculaba en memoria (`anio`, `mes`,
  `nombre_mes`, `orden_departamento`, `kit_sentencia`, `kit_evento`,
  `total_insumos`) se persisten como columnas no editables. Se calculan en
  `save()` a partir de los campos de captura, de modo que el dashboard pueda
  consumirlos sin replicar reglas de negocio.
* La validación de nomenclatura se hace contra el catálogo oficial
  (`catalogos.py`), lo que elimina la necesidad de estandarización difusa
  (Levenshtein) que hoy aplica el ETL sobre datos de Excel.
"""

import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models

from .catalogos import (
    DEPARTAMENTO_ORDEN,
    EVENTO_SENTENCIA,
    EVENTOS,
    EVENTOS_ADMITIDOS,
    MESES_ES,
    SIN_ESPECIFICAR,
    distritos_de,
    normalizar_texto,
    orden_de_departamento,
)

# Techo defensivo para las cantidades de insumos. El análisis exploratorio del
# ETL detectó registros históricos con valores atípicos muy altos; este límite
# frena errores de tipeo sin bloquear operativos de gran escala.
MAX_UNIDADES_POR_INSUMO = 100_000

# Un operativo puede asistir a muchas familias, pero un valor de seis cifras
# indica error de carga.
MAX_FAMILIAS_ASISTIDAS = 50_000

# La serie histórica del BI arranca en 2018; no se aceptan cargas anteriores
# por formulario.
FECHA_MINIMA_ADMITIDA = datetime.date(2018, 1, 1)

# Piso absoluto para los registros importados de la planilla histórica, que
# contiene fechas mal tipeadas fuera del rango de la serie. Sirve para descartar
# fechas imposibles sin perder filas legítimas.
FECHA_MINIMA_HISTORICA = datetime.date(1990, 1, 1)

# Restringe los nombres geográficos al juego de caracteres del catálogo oficial.
# Además de validar formato, impide que llegue a la base cualquier carga útil de
# scripting o de metacaracteres SQL.
validador_nombre_geografico = RegexValidator(
    regex=r"^[A-ZÁÉÍÓÚÜÑ0-9 .,'\-/]+$",
    message=(
        'Solo se admiten letras mayúsculas, números, espacios y los signos '
        ". , ' - /"
    ),
)

# El texto libre se acota a caracteres imprimibles y se rechazan los signos de
# apertura/cierre de etiquetas para evitar almacenar HTML o scripts.
validador_texto_libre = RegexValidator(
    regex=r'[<>\x00-\x1f\x7f]',
    inverse_match=True,
    message='El texto contiene caracteres no permitidos (< > o de control).',
)


class Departamento(models.TextChoices):
    """Departamentos del Paraguay, en el orden oficial usado por el BI."""

    CONCEPCION = 'CONCEPCIÓN', 'Concepción'
    SAN_PEDRO = 'SAN PEDRO', 'San Pedro'
    CORDILLERA = 'CORDILLERA', 'Cordillera'
    GUAIRA = 'GUAIRÁ', 'Guairá'
    CAAGUAZU = 'CAAGUAZÚ', 'Caaguazú'
    CAAZAPA = 'CAAZAPÁ', 'Caazapá'
    ITAPUA = 'ITAPÚA', 'Itapúa'
    MISIONES = 'MISIONES', 'Misiones'
    PARAGUARI = 'PARAGUARÍ', 'Paraguarí'
    ALTO_PARANA = 'ALTO PARANÁ', 'Alto Paraná'
    CENTRAL = 'CENTRAL', 'Central'
    NEEMBUCU = 'ÑEEMBUCÚ', 'Ñeembucú'
    AMAMBAY = 'AMAMBAY', 'Amambay'
    CANINDEYU = 'CANINDEYÚ', 'Canindeyú'
    PDTE_HAYES = 'PDTE. HAYES', 'Pdte. Hayes'
    ALTO_PARAGUAY = 'ALTO PARAGUAY', 'Alto Paraguay'
    BOQUERON = 'BOQUERON', 'Boquerón'
    CAPITAL = 'CAPITAL', 'Capital'


class Evento(models.TextChoices):
    """Tipologías de evento ya normalizadas en `dim_evento`."""

    CIDH = 'C.I.D.H.', 'C.I.D.H. (sentencia de la Corte)'
    COVID = 'COVID', 'COVID'
    EXTREMA_VULNERABILIDAD = 'EXTREMA VULNERABILIDAD', 'Extrema vulnerabilidad'
    INCENDIO = 'INCENDIO', 'Incendio'
    INUNDACION = 'INUNDACION', 'Inundación'
    OLLA_POPULAR = 'OLLA POPULAR', 'Olla popular'
    OPERATIVO_JAHOI = "OPERATIVO JAHO'I", "Operativo Jaho'i"
    SEQUIA = 'SEQUIA', 'Sequía'
    TORMENTA_SEVERA = 'TORMENTA SEVERA', 'Tormenta severa'
    OTROS = 'OTROS', 'Otros'
    # Solo admisible en registros importados del histórico.
    NO_INFORMADO = 'SIN EVENTO', 'Sin evento (histórico)'


class SexoTitular(models.TextChoices):
    """Sexo del titular del hogar asistido."""

    MASCULINO = 'M', 'Masculino'
    FEMENINO = 'F', 'Femenino'
    OTRO = 'O', 'Otro / No especificado'


class Origen(models.TextChoices):
    """Procedencia del registro.

    Discrimina las dos poblaciones que conviven en la tabla y que tienen
    exigencias de completitud distintas: lo capturado por el formulario debe
    estar completo, mientras que lo importado de la planilla histórica carece
    de la caracterización de beneficiarios porque nunca se relevó.
    """

    FORMULARIO = 'FORMULARIO', 'Carga por formulario'
    EXCEL_HISTORICO = 'EXCEL_HISTORICO', 'Importación histórica (Excel)'


class RegistroAsistenciaHumanitaria(models.Model):
    """Registro único de una asistencia humanitaria entregada en territorio."""

    # --- Dimensión temporal -------------------------------------------------
    fecha = models.DateField(
        'fecha de la asistencia',
        help_text='Fecha en que se entregó la asistencia. No puede ser futura.',
    )

    # --- Dimensión geográfica ----------------------------------------------
    departamento = models.CharField(
        'departamento',
        max_length=20,
        choices=Departamento.choices,
    )
    distrito = models.CharField(
        'distrito',
        max_length=60,
        validators=[validador_nombre_geografico],
        help_text='Debe pertenecer al departamento seleccionado.',
    )
    localidad = models.CharField(
        'localidad / barrio',
        max_length=120,
        blank=True,
        default=SIN_ESPECIFICAR,
        validators=[validador_nombre_geografico],
    )
    # Las tres columnas de caracterización admiten NULL únicamente para alojar
    # los registros históricos de Excel, donde el dato no existe. Para las
    # cargas por formulario son obligatorias, y así lo impone la restricción
    # `ing_asis_caracterizacion_completa`.
    es_poblacion_rural = models.BooleanField(
        'población rural',
        null=True,
        blank=True,
        help_text='Verdadero si la asistencia se entregó en zona rural.',
    )
    es_poblacion_indigena = models.BooleanField(
        'población indígena',
        null=True,
        blank=True,
        help_text=(
            'Verdadero si el titular pertenece a un pueblo indígena. '
            'Lo aportan los consolidados anuales; el formulario no lo captura.'
        ),
    )

    # --- Dimensión evento ---------------------------------------------------
    evento = models.CharField(
        'tipo de evento',
        max_length=30,
        choices=Evento.choices,
    )

    # --- Caracterización de los beneficiarios -------------------------------
    sexo_titular = models.CharField(
        'sexo del titular',
        max_length=1,
        choices=SexoTitular.choices,
        null=True,
        blank=True,
    )
    cantidad_familias_asistidas = models.PositiveIntegerField(
        'cantidad de familias asistidas',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(MAX_FAMILIAS_ASISTIDAS),
        ],
    )

    # --- Insumos entregados -------------------------------------------------
    # Se mantienen los nombres de la planilla original (KIT_A / KIT_B) porque
    # son los que registra el operador; la imputación contable a
    # kit_sentencia / kit_evento es derivada.
    kit_a = models.PositiveIntegerField(
        'kit A',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )
    kit_b = models.PositiveIntegerField(
        'kit B',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )
    chapa_fibrocemento = models.PositiveIntegerField(
        'chapas de fibrocemento',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )
    chapa_zinc = models.PositiveIntegerField(
        'chapas de zinc',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )
    colchones = models.PositiveIntegerField(
        'colchones',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )
    frazadas = models.PositiveIntegerField(
        'frazadas',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )
    terciadas = models.PositiveIntegerField(
        'terciadas',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )
    puntales = models.PositiveIntegerField(
        'puntales',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )
    carpas_plasticas = models.PositiveIntegerField(
        'carpas plásticas',
        default=0,
        validators=[MaxValueValidator(MAX_UNIDADES_POR_INSUMO)],
    )

    observaciones = models.TextField(
        'observaciones',
        max_length=500,
        blank=True,
        default='',
        validators=[validador_texto_libre],
    )

    # --- Campos derivados (no editables, calculados en save) ----------------
    anio = models.PositiveSmallIntegerField('año', editable=False)
    mes = models.PositiveSmallIntegerField('mes', editable=False)
    nombre_mes = models.CharField(
        'nombre del mes', max_length=12, editable=False,
    )
    orden_departamento = models.PositiveSmallIntegerField(
        'orden del departamento', editable=False,
    )
    kit_sentencia = models.PositiveIntegerField(
        'kits por sentencia', default=0, editable=False,
    )
    kit_evento = models.PositiveIntegerField(
        'kits por evento', default=0, editable=False,
    )
    total_insumos = models.PositiveIntegerField(
        'total de insumos', default=0, editable=False,
    )

    # --- Auditoría ----------------------------------------------------------
    origen = models.CharField(
        'origen del registro',
        max_length=15,
        choices=Origen.choices,
        default=Origen.FORMULARIO,
        editable=False,
        db_index=True,
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='registros_cargados',
        editable=False,
        null=True,
        verbose_name='cargado por',
    )
    creado_en = models.DateTimeField('creado en', auto_now_add=True)
    actualizado_en = models.DateTimeField('actualizado en', auto_now=True)

    class Meta:
        db_table = 'ingesta_asistencia_humanitaria'
        verbose_name = 'registro de asistencia humanitaria'
        verbose_name_plural = 'registros de asistencia humanitaria'
        ordering = ('-fecha', '-id')
        indexes = (
            models.Index(fields=('fecha',), name='ing_asis_fecha_idx'),
            models.Index(
                fields=('departamento', 'distrito'), name='ing_asis_geo_idx',
            ),
            models.Index(fields=('evento',), name='ing_asis_evento_idx'),
            models.Index(
                fields=('es_poblacion_rural',), name='ing_asis_rural_idx',
            ),
            models.Index(
                fields=('es_poblacion_indigena',), name='ing_asis_indigena_idx',
            ),
            models.Index(fields=('sexo_titular',), name='ing_asis_sexo_idx'),
            models.Index(fields=('anio', 'mes'), name='ing_asis_periodo_idx'),
        )
        constraints = (
            models.CheckConstraint(
                check=(
                    models.Q(cantidad_familias_asistidas__isnull=True)
                    | models.Q(cantidad_familias_asistidas__gte=1)
                ),
                name='ing_asis_familias_min_1',
            ),
            models.CheckConstraint(
                check=models.Q(total_insumos__gt=0),
                name='ing_asis_total_insumos_positivo',
            ),
            # La fecha mínima depende del origen: las cargas por formulario
            # pertenecen a la serie vigente, mientras que la importación
            # histórica solo se protege de fechas imposibles.
            models.CheckConstraint(
                check=(
                    models.Q(
                        origen=Origen.FORMULARIO,
                        fecha__gte=FECHA_MINIMA_ADMITIDA,
                    )
                    | models.Q(
                        origen=Origen.EXCEL_HISTORICO,
                        fecha__gte=FECHA_MINIMA_HISTORICA,
                    )
                ),
                name='ing_asis_fecha_minima',
            ),
            # Garantía de completitud: ningún registro capturado por el
            # formulario puede quedar sin caracterización de beneficiarios,
            # aunque las columnas admitan NULL para el histórico.
            models.CheckConstraint(
                check=(
                    models.Q(origen=Origen.EXCEL_HISTORICO)
                    | models.Q(
                        cantidad_familias_asistidas__isnull=False,
                        sexo_titular__isnull=False,
                        es_poblacion_rural__isnull=False,
                    )
                ),
                name='ing_asis_caracterizacion_completa',
            ),
        )

    def __str__(self):
        return f'{self.fecha} · {self.departamento} · {self.evento}'

    # -- Reglas de negocio ---------------------------------------------------
    @property
    def campos_de_insumos(self):
        """Nombres de los campos que componen el total de insumos."""
        return (
            'kit_a', 'kit_b', 'chapa_fibrocemento', 'chapa_zinc', 'colchones',
            'frazadas', 'terciadas', 'puntales', 'carpas_plasticas',
        )

    @property
    def es_historico(self):
        return self.origen == Origen.EXCEL_HISTORICO

    def calcular_total_insumos(self):
        return sum(getattr(self, campo) or 0 for campo in self.campos_de_insumos)

    def clean(self):
        """Valida coherencia geográfica, temporal y de negocio."""
        errores = {}

        # Normalización previa: el DW almacena todo en mayúsculas.
        self.distrito = normalizar_texto(self.distrito)
        self.localidad = normalizar_texto(self.localidad) or SIN_ESPECIFICAR
        self.departamento = normalizar_texto(self.departamento)
        self.evento = normalizar_texto(self.evento)

        if self.departamento and self.departamento not in DEPARTAMENTO_ORDEN:
            errores['departamento'] = 'El departamento no figura en el catálogo oficial.'
        elif self.distrito and self.distrito not in distritos_de(self.departamento):
            errores['distrito'] = (
                f'El distrito «{self.distrito}» no pertenece a '
                f'{self.departamento}.'
            )

        if self.evento:
            admitidos = EVENTOS_ADMITIDOS if self.es_historico else EVENTOS
            if self.evento not in admitidos:
                errores['evento'] = (
                    'El tipo de evento no figura en el catálogo oficial.'
                )

        if self.fecha:
            piso = (
                FECHA_MINIMA_HISTORICA if self.es_historico
                else FECHA_MINIMA_ADMITIDA
            )
            if self.fecha > datetime.date.today():
                errores['fecha'] = 'La fecha de la asistencia no puede ser futura.'
            elif self.fecha < piso:
                errores['fecha'] = (
                    f'La fecha no puede ser anterior a {piso.isoformat()}.'
                )

        # La caracterización de beneficiarios solo puede faltar en el histórico
        # importado; el formulario debe informarla siempre.
        if not self.es_historico:
            faltantes = {
                campo: 'Este dato es obligatorio.'
                for campo in (
                    'cantidad_familias_asistidas',
                    'sexo_titular',
                    'es_poblacion_rural',
                )
                if getattr(self, campo) is None
            }
            errores.update(faltantes)

        if self.calcular_total_insumos() <= 0:
            errores['total_insumos'] = (
                'Debe registrarse al menos una unidad de algún insumo.'
            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        """Recalcula los campos derivados antes de persistir."""
        self.anio = self.fecha.year
        self.mes = self.fecha.month
        self.nombre_mes = MESES_ES[self.fecha.month]
        self.orden_departamento = orden_de_departamento(self.departamento)
        self.total_insumos = self.calcular_total_insumos()

        # Regla heredada del ETL: los kits de asistencias C.I.D.H. se imputan a
        # kit_sentencia; los del resto de los eventos, a kit_evento.
        total_kits = (self.kit_a or 0) + (self.kit_b or 0)
        if self.evento == EVENTO_SENTENCIA:
            self.kit_sentencia, self.kit_evento = total_kits, 0
        else:
            self.kit_sentencia, self.kit_evento = 0, total_kits

        super().save(*args, **kwargs)
