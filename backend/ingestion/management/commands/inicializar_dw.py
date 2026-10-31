# -*- coding: utf-8 -*-
"""Crea el esquema estrella en una base de datos vacía.

Aplica `etl/sql/000_esquema_estrella.sql` sobre la misma base a la que apunta
esta aplicación. No toca el Data Warehouse de producción: solo corre contra
la DATABASE_URL configurada.

Prerrequisito: `python manage.py migrate` ya creó `ingesta_asistencia_humanitaria`.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


def _localizar_sql() -> Path:
    # Este archivo vive en ingestion/management/commands/.
    # parents[5] = carpeta bi_sen (hermana de BI-SEN-Back).
    # parents[4] = carpeta ingesta_sen.
    bi_sen = Path(__file__).resolve().parents[5]
    ingesta_sen = Path(__file__).resolve().parents[4]
    candidatos = [
        bi_sen / 'BI-SEN-Back' / 'etl' / 'sql' / '000_esquema_estrella.sql',
        ingesta_sen / 'infra' / 'sql' / '000_esquema_estrella.sql',
    ]
    for camino in candidatos:
        if camino.exists():
            return camino
    raise CommandError(
        'No se encontró 000_esquema_estrella.sql. Se buscó en:\n'
        + '\n'.join(f'  - {c}' for c in candidatos)
    )


def _enunciados(script: str):
    """Parte el script en sentencias sueltas.

    psycopg3 (el conector de Django 5) no ejecuta varios enunciados de una
    vez. El archivo no usa bloques $$ así que cortar por ';' es seguro.
    """
    lineas = [
        linea for linea in script.splitlines()
        if not linea.lstrip().startswith('--')
    ]
    for parte in '\n'.join(lineas).split(';'):
        sentencia = parte.strip()
        if sentencia and sentencia.upper() not in ('BEGIN', 'COMMIT'):
            yield sentencia


class Command(BaseCommand):
    help = 'Crea dim_fecha, dim_evento, dim_ubicacion y hechos_asistencia_humanitaria.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sql',
            type=Path,
            default=None,
            help='Ruta al archivo SQL. Por defecto se usa el del repositorio.',
        )

    def handle(self, *args, **opciones):
        engine = connection.settings_dict.get('ENGINE', '')
        if 'postgresql' not in engine:
            raise CommandError(
                'El esquema estrella requiere PostgreSQL. '
                f'Motor actual: {engine}'
            )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                 WHERE table_name = 'ingesta_asistencia_humanitaria';
                """
            )
            if cursor.fetchone() is None:
                raise CommandError(
                    'No existe ingesta_asistencia_humanitaria. '
                    'Ejecute primero: python manage.py migrate'
                )

            cursor.execute(
                """
                SELECT table_name FROM information_schema.tables
                 WHERE table_schema = 'public'
                   AND table_name IN (
                       'dim_fecha', 'dim_evento', 'dim_ubicacion',
                       'hechos_asistencia_humanitaria'
                   )
                 ORDER BY table_name;
                """
            )
            ya_existen = [fila[0] for fila in cursor.fetchall()]

        if len(ya_existen) == 4:
            self.stdout.write(self.style.SUCCESS(
                'El esquema estrella ya está creado. No se hizo ningún cambio.'
            ))
            return

        sql = opciones['sql'] or _localizar_sql()
        if not sql.exists():
            raise CommandError(f'No existe el archivo SQL: {sql}')

        script = sql.read_text(encoding='utf-8')
        self.stdout.write(f'Aplicando {sql}...')

        with transaction.atomic():
            with connection.cursor() as cursor:
                for sentencia in _enunciados(script):
                    cursor.execute(sentencia)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name FROM information_schema.tables
                 WHERE table_schema = 'public'
                   AND table_name IN (
                       'dim_fecha', 'dim_evento', 'dim_ubicacion',
                       'hechos_asistencia_humanitaria',
                       'ingesta_asistencia_humanitaria'
                   )
                 ORDER BY table_name;
                """
            )
            tablas = [fila[0] for fila in cursor.fetchall()]

        self.stdout.write(self.style.SUCCESS(
            'Esquema estrella listo: ' + ', '.join(tablas)
        ))
        self.stdout.write(
            'Siguiente paso: migrar el histórico con '
            'cargar_historico_a_ingesta.py y correr etl_script.py.'
        )
