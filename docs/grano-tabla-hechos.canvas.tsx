import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

/**
 * Copia de trabajo del canvas de diseño. El original visual se abre en Cursor;
 * esta copia vive en el repositorio de ingesta para versionarlo junto al código.
 *
 * Documentación en Markdown: ../docs/grano-tabla-hechos.md
 */
export default function GranoTablaHechos() {
  return (
    <Stack gap={24}>
      <Stack gap={8}>
        <H1>Grano del Data Warehouse</H1>
        <Text tone="secondary">
          Diseño aplicado en sen_dw_dev (Postgres local, puerto 5434). La base
          de producción no se toca.
        </Text>
      </Stack>

      <Grid columns={3} gap={16}>
        <Stat value="Familia" label="Grano de la ingesta" tone="info" />
        <Stat
          value="Fecha + lugar + evento"
          label="Grano del hecho"
          tone="success"
        />
        <Stat
          value="Medidas"
          label="Hombres, mujeres, rural, urbana, insumos"
        />
      </Grid>

      <Callout tone="success" title="Diseño aplicado">
        El formulario guarda un registro por familia. El tablero consulta
        totales. El ETL compacta esas filas en una sola fila de hechos por
        día, ubicación y tipo de evento, con cantidades ya sumadas. Una carga
        tardía de la misma clave actualiza esa fila; no inserta otra.
      </Callout>

      <H2>Dos capas, dos granos</H2>
      <Table
        headers={["Capa", "Tabla", "Una fila representa", "Para qué sirve"]}
        rows={[
          [
            "Transaccional",
            "ingesta_asistencia_humanitaria",
            "Una familia asistida",
            "Carga, auditoría, corrección",
          ],
          [
            "Analítica",
            "hechos_asistencia_humanitaria",
            "El total de ese día en ese lugar por ese evento",
            "Tablero, cortes, series",
          ],
        ]}
        rowTone={["info", "success"]}
        striped
      />
      <Text size="small" tone="secondary">
        Fuente: modelo dimensional Kimball. El hecho nunca copia 1 a 1 el
        formulario si el consumo es OLAP.
      </Text>

      <H2>Clave de agrupación</H2>
      <Text>
        No basta fecha y ubicación. El mismo día, en el mismo barrio, puede
        haber inundación y un incendio. Si se mezclan, los kits y las familias
        de dos operativos distintos aparecen como uno solo.
      </Text>
      <Table
        headers={["Campo", "¿Va en la clave?", "Motivo"]}
        rows={[
          ["fecha", "Sí", "Corte temporal del tablero"],
          [
            "departamento + distrito + localidad",
            "Sí",
            "Jerarquía geográfica ya usada por el BI",
          ],
          ["evento", "Sí", "Evita mezclar tipologías distintas"],
          [
            "sexo del titular",
            "No",
            "Pasa a ser medida: cantidad de hombres / mujeres / otro",
          ],
          [
            "población rural",
            "No",
            "Pasa a ser medida: cantidad rural / urbana",
          ],
        ]}
        striped
      />

      <H2>Cómo queda una fila del hecho</H2>
      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Clave (dimensiones)</CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text size="small">fecha → dim_fecha</Text>
              <Text size="small">ubicación → dim_ubicacion</Text>
              <Text size="small">evento → dim_evento</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Medidas (todo aditivo)</CardHeader>
          <CardBody>
            <Stack gap={6}>
              <Text size="small">cantidad_familias_asistidas</Text>
              <Text size="small">cantidad_mujeres / hombres / otro</Text>
              <Text size="small">cantidad_rural / urbana</Text>
              <Text size="small">kits, chapas, colchones, frazadas…</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <H3>Ejemplo</H3>
      <Text tone="secondary" size="small">
        Tres familias cargadas el 14/08/2026 en Luque, Central, por inundación.
      </Text>
      <Table
        headers={["En la ingesta", "Sexo", "Zona", "Kit A"]}
        rows={[
          ["Familia 1", "F", "Urbana", "2"],
          ["Familia 2", "F", "Rural", "1"],
          ["Familia 3", "M", "Rural", "3"],
        ]}
        striped
      />
      <Text size="small" weight="semibold">
        El ETL produce una sola fila en el hecho
      </Text>
      <Table
        headers={[
          "Fecha",
          "Lugar",
          "Evento",
          "Familias",
          "Mujeres",
          "Hombres",
          "Rural",
          "Urbana",
          "Kit A",
        ]}
        rows={[
          [
            "2026-08-14",
            "Central / Luque",
            "INUNDACION",
            "3",
            "2",
            "1",
            "2",
            "1",
            "6",
          ],
        ]}
      />

      <H2>Por qué es óptimo</H2>
      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <Row gap={8} align="center">
            <Pill tone="success" size="sm" active>
              Conviene
            </Pill>
            <Text weight="semibold">Hecho agregado</Text>
          </Row>
          <Text size="small">
            El tablero ya agrupa por año, mes, departamento y evento. Llegar
            con los totales precalculados evita sumar miles de filas familiares
            en cada gráfico.
          </Text>
          <Text size="small">
            Sexo y zona quedan como medidas aditivas: se pueden sumar por
            departamento o por año sin doble conteo.
          </Text>
          <Text size="small">
            La familia no se pierde: sigue en la tabla de ingesta, que es la
            fuente de verdad operativa.
          </Text>
        </Stack>
        <Stack gap={8}>
          <Row gap={8} align="center">
            <Pill tone="warning" size="sm" active>
              No conviene
            </Pill>
            <Text weight="semibold">Hecho 1 a 1 con el formulario</Text>
          </Row>
          <Text size="small">
            Replica el sistema transaccional dentro del warehouse. El BI
            volvería a agregar en cada consulta lo que el ETL ya puede
            resolver una vez.
          </Text>
          <Text size="small">
            Sexo y rural como columnas de fila no sirven para un KPI de
            «cantidad de mujeres»: habría que contar filas, no sumar una
            medida.
          </Text>
        </Stack>
      </Grid>

      <Divider />

      <H2>Histórico de Excel</H2>
      <Callout tone="warning" title="Esas filas no son familias">
        La planilla 2018–2023 registra operativos, no hogares. No hay sexo ni
        zona. Al compactarlas, familias / mujeres / hombres / rural quedan en
        cero. Los insumos sí se suman. El tablero debe mostrar «No informado»
        en la caracterización de esa serie, nunca inventar un 50/50.
      </Callout>

      <H2>Qué no entra en el hecho</H2>
      <Text>
        Observaciones y usuario que cargó. Eso es transaccional. Si el tablero
        pidiera el detalle de un día, se abre la ingesta filtrada por fecha y
        ubicación, no se desagrega el hecho.
      </Text>

      <Card>
        <CardHeader
          trailing={
            <Pill tone="success" active size="sm">
              Aplicado
            </Pill>
          }
        >
          Estado
        </CardHeader>
        <CardBody>
          <Text>
            Esquema en etl/sql/000_esquema_estrella.sql. ETL en etl_script.py.
            UPSERT sobre (id_fecha, id_ubicacion, id_evento).
          </Text>
        </CardBody>
      </Card>
    </Stack>
  );
}
