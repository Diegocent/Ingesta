# Grano de la tabla de hechos

Documento de diseño del Data Warehouse que usa el sistema de ingesta.
Equivalente al canvas *Grano tabla de hechos*. Ya está aplicado en
`sen_dw_dev` (Postgres local, puerto 5434). La base de producción no se toca.

| Ingesta | Hecho | Medidas |
|---|---|---|
| Una fila = una familia | Una fila = fecha + lugar + evento | Hombres, mujeres, otro, rural, urbana, insumos |

El formulario guarda un registro por familia. El tablero no consulta
familias: consulta totales. El ETL compacta esas filas en una sola fila de
hechos por día, ubicación y tipo de evento, con las cantidades ya sumadas.

## Dos capas, dos granos

| Capa | Tabla | Una fila representa | Para qué sirve |
|---|---|---|---|
| Transaccional | `ingesta_asistencia_humanitaria` | Una familia asistida | Carga, auditoría, corrección |
| Analítica | `hechos_asistencia_humanitaria` | El total de ese día en ese lugar por ese evento | Tablero, cortes, series |

Fuente: modelo dimensional Kimball. El hecho nunca copia 1 a 1 el formulario
si el consumo es OLAP.

## Clave de agrupación

No basta fecha y ubicación. El mismo día, en el mismo barrio, puede haber
inundación y un incendio. Si se mezclan, los kits y las familias de dos
operativos distintos aparecen como uno solo.

| Campo | ¿Va en la clave? | Motivo |
|---|---|---|
| fecha | Sí | Corte temporal del tablero |
| departamento + distrito + localidad | Sí | Jerarquía geográfica ya usada por el BI |
| evento | Sí | Evita mezclar tipologías distintas |
| sexo del titular | No | Pasa a ser medida: cantidad de hombres / mujeres / otro |
| población rural | No | Pasa a ser medida: cantidad rural / urbana |

## Cómo queda una fila del hecho

**Clave (dimensiones)**

- fecha → `dim_fecha`
- ubicación → `dim_ubicacion`
- evento → `dim_evento`

**Medidas (todas aditivas)**

- `cantidad_registros`
- `cantidad_familias_asistidas`
- `cantidad_mujeres` / `cantidad_hombres` / `cantidad_otro`
- `cantidad_rural` / `cantidad_urbana`
- kits, chapas, colchones, frazadas, terciadas, puntales, carpas

### Ejemplo

Tres familias cargadas el 14/08/2026 en Luque, Central, por inundación.

| En la ingesta | Sexo | Zona | Kit A |
|---|---|---|---|
| Familia 1 | F | Urbana | 2 |
| Familia 2 | F | Rural | 1 |
| Familia 3 | M | Rural | 3 |

El ETL produce **una sola fila** en el hecho:

| Fecha | Lugar | Evento | Familias | Mujeres | Hombres | Rural | Urbana | Kit A |
|---|---|---|---|---|---|---|---|---|
| 2026-08-14 | Central / Luque | INUNDACION | 3 | 2 | 1 | 2 | 1 | 6 |

Una carga posterior de otra familia con la misma clave **actualiza esa fila**;
no inserta otra.

## Por qué es óptimo

**Conviene el hecho agregado.** El tablero ya agrupa por año, mes,
departamento y evento. Llegar con los totales precalculados evita sumar miles
de filas familiares en cada gráfico. Sexo y zona quedan como medidas
aditivas: se pueden sumar por departamento o por año sin doble conteo. La
familia no se pierde: sigue en la tabla de ingesta.

**No conviene el hecho 1 a 1 con el formulario.** Replicaría el sistema
transaccional dentro del warehouse. El BI volvería a agregar en cada consulta
lo que el ETL ya puede resolver una vez. Sexo y rural como columnas de fila
no sirven para un KPI de «cantidad de mujeres»: habría que contar filas, no
sumar una medida.

## Histórico de Excel

La planilla 2018–2023 registra operativos, no hogares. No hay sexo ni zona.
Al compactarlas, familias / mujeres / hombres / rural quedan en cero. Los
insumos sí se suman. El tablero debe mostrar «No informado» en la
caracterización de esa serie, nunca inventar un 50/50.

## Qué no entra en el hecho

Observaciones, usuario que cargó, marcas de auditoría. Eso es transaccional.
Si el tablero pidiera el detalle de un día, se abre la ingesta filtrada por
fecha y ubicación; no se desagrega el hecho.

## Dónde está implementado

- Esquema: `BI-SEN-Back/etl/sql/000_esquema_estrella.sql`
- Refresco al guardar: `BI-SEN-Back/etl/sql/003_dw_refresco_automatico.sql`
- ETL (compactación completa / cargas masivas): `BI-SEN-Back/etl/etl_script.py`
- Arranque local: `ingesta_sen/infra/README.md`
