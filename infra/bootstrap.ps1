# Arranca el Postgres local y deja el esquema listo.
# No toca el Data Warehouse de producción.

$ErrorActionPreference = 'Stop'
$infra = $PSScriptRoot
$backend = Join-Path $infra '..\backend' | Resolve-Path
$venvPython = Join-Path $infra '..\.venv\Scripts\python.exe' | Resolve-Path -ErrorAction SilentlyContinue

Write-Host '1/4  Levantando PostgreSQL local (puerto 5434)...'
docker compose -f (Join-Path $infra 'docker-compose.yml') up -d

Write-Host '    Esperando a que acepte conexiones...'
$ok = $false
foreach ($i in 1..30) {
    docker exec sen_dw_dev pg_isready -U sen -d sen_dw_dev 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $ok) {
    throw 'PostgreSQL no respondió a tiempo. Revise: docker compose logs postgres'
}

$envDestino = Join-Path $backend '.env'
$envPlantilla = Join-Path $backend '.env.docker.example'
if (-not (Test-Path $envDestino)) {
    Copy-Item $envPlantilla $envDestino
    Write-Host '2/4  Se copió backend/.env.docker.example -> backend/.env'
} else {
    Write-Host '2/4  backend/.env ya existe; no se sobrescribe.'
}

if (-not $venvPython) {
    throw 'No se encontró ingesta_sen/.venv. Cree el entorno virtual antes de continuar.'
}

Write-Host '3/4  Aplicando migraciones de Django (tabla de ingesta y auth)...'
Set-Location $backend
& $venvPython manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'migrate falló' }

Write-Host '4/4  Creando el esquema estrella (dimensiones y hechos)...'
& $venvPython manage.py inicializar_dw
if ($LASTEXITCODE -ne 0) { throw 'inicializar_dw falló' }

Write-Host ''
Write-Host 'Listo. Base nueva: sen_dw_dev en localhost:5434'
Write-Host '  Ingesta:  python manage.py runserver'
Write-Host '  Usuario:  python manage.py createsuperuser'
Write-Host '  Histórico + ETL (desde BI-SEN-Back, con su .env apuntando acá):'
Write-Host '            python etl/cargar_historico_a_ingesta.py'
Write-Host '            python etl/etl_script.py'
