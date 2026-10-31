# Warehouse nuevo de asistencia humanitaria
#
# Este directorio levanta un PostgreSQL local (puerto 5434) que NO es el Neon
# de producción. El 5433 ya está ocupado en esta máquina por otro contenedor.
# Ingesta y BI apuntan a la misma base: `sen_dw_dev`.
#
# Arranque rápido (Docker)
# ------------------------
#   cd ingesta_sen/infra
#   docker compose up -d
#   copy ..\backend\.env.docker.example ..\backend\.env
#   cd ..\backend
#   ..\.venv\Scripts\python.exe manage.py migrate
#   ..\.venv\Scripts\python.exe manage.py inicializar_dw
#   ..\.venv\Scripts\python.exe manage.py createsuperuser
#
# O ejecutar el script:
#   powershell -File bootstrap.ps1
#
# Neon nuevo (en lugar de Docker)
# -------------------------------
# 1. Crear un proyecto/base vacía, por ejemplo `sen_dw_dev`.
# 2. Pegar la URL en backend/.env (DATABASE_URL) y en BI-SEN-Back/.env (DB_DW_*).
# 3. Correr migrate + inicializar_dw igual que arriba.
#
# Carga de datos
# --------------
# El hecho compacta la ingesta por fecha + ubicación + evento.
# Fuente preferida: consolidados anuales 2018-2024 (una fila = un titular).
#   python etl/cargar_consolidados_a_ingesta.py --simular
#   python etl/cargar_consolidados_a_ingesta.py
#   python etl/etl_script.py
#
# No mezclar con cargar_historico_a_ingesta.py (registros_historicos.xlsx):
# duplicaría 2018-2023.
#
# Una carga tardía de la misma fecha no duplica el hecho: el ETL actualiza
# los totales de esa clave.
#
# Automatización
# --------------
# Tras `inicializar_dw`, instalar el trigger (una sola vez):
#   python etl/etl_script.py --instalar-refresco
# A partir de ahí, cada familia guardada en el formulario actualiza el BI.
# Las cargas masivas de Excel pausan el trigger solas y hay que correr
# etl_script.py al terminar.
#
# Diseño del grano (canvas / decisión):
#   ../docs/grano-tabla-hechos.md
