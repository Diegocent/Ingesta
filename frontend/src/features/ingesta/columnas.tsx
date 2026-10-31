import type { ColumnDef } from '@tanstack/react-table'

import { Badge } from '@/components/ui/badge'
import { capitalizar, INSUMOS } from '@/features/ingesta/catalogos'
import type { RegistroAsistencia } from '@/features/ingesta/types'

const formatoNumero = new Intl.NumberFormat('es-PY')

/** Muestra la fecha ISO como dd/mm/aaaa sin reinterpretar la zona horaria. */
function formatearFecha(iso: string): string {
  const [anio, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${anio}`
}

function celdaNumerica(valor: number | null) {
  if (valor === null) {
    return <span className="text-muted-foreground">—</span>
  }
  return (
    <span className={valor === 0 ? 'text-muted-foreground' : 'tabular-nums'}>
      {formatoNumero.format(valor)}
    </span>
  )
}

function variantePorZona(esRural: boolean | null) {
  if (esRural === null) return 'outline' as const
  return esRural ? ('default' as const) : ('secondary' as const)
}

/**
 * Columnas de la vista "en duro": una columna por campo del registro, sin
 * agrupaciones ni agregaciones. Las banderas `enableSorting` habilitan solo las
 * columnas que el backend acepta en `ordering`; pedir orden por otra columna
 * sería una consulta sin índice.
 */
export const columnas: ColumnDef<RegistroAsistencia>[] = [
  {
    accessorKey: 'fecha',
    header: 'Fecha',
    cell: ({ row }) => (
      <span className="tabular-nums">{formatearFecha(row.original.fecha)}</span>
    ),
    enableSorting: true,
  },
  {
    accessorKey: 'departamento',
    header: 'Departamento',
    cell: ({ row }) => capitalizar(row.original.departamento),
    enableSorting: true,
  },
  {
    accessorKey: 'distrito',
    header: 'Distrito',
    cell: ({ row }) => capitalizar(row.original.distrito),
    enableSorting: true,
  },
  {
    accessorKey: 'localidad',
    header: 'Localidad',
    cell: ({ row }) => (
      <span className="text-muted-foreground">
        {capitalizar(row.original.localidad)}
      </span>
    ),
    enableSorting: false,
  },
  {
    accessorKey: 'es_poblacion_rural',
    header: 'Zona',
    // Los registros importados del histórico no tienen el dato. Se distinguen
    // con una variante neutra para no confundir «no informado» con «urbana».
    cell: ({ row }) => (
      <Badge variant={variantePorZona(row.original.es_poblacion_rural)}>
        {row.original.zona}
      </Badge>
    ),
    enableSorting: true,
  },
  {
    accessorKey: 'evento',
    header: 'Evento',
    cell: ({ row }) => (
      <span className="font-medium">{capitalizar(row.original.evento)}</span>
    ),
    enableSorting: true,
  },
  {
    accessorKey: 'sexo_titular',
    header: 'Sexo titular',
    cell: ({ row }) => row.original.sexo_titular_etiqueta,
    enableSorting: true,
  },
  {
    accessorKey: 'cantidad_familias_asistidas',
    header: 'Familias',
    cell: ({ row }) => celdaNumerica(row.original.cantidad_familias_asistidas),
    enableSorting: true,
  },
  ...INSUMOS.map<ColumnDef<RegistroAsistencia>>(({ campo, etiqueta }) => ({
    accessorKey: campo,
    header: etiqueta,
    cell: ({ row }) => celdaNumerica(row.original[campo]),
    enableSorting: false,
  })),
  {
    accessorKey: 'total_insumos',
    header: 'Total insumos',
    cell: ({ row }) => (
      <span className="font-semibold tabular-nums">
        {formatoNumero.format(row.original.total_insumos)}
      </span>
    ),
    enableSorting: true,
  },
  {
    accessorKey: 'cargado_por',
    header: 'Cargado por',
    cell: ({ row }) => (
      <span className="text-muted-foreground">
        {row.original.cargado_por ?? '—'}
      </span>
    ),
    enableSorting: false,
  },
]
