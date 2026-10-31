import { useEffect, useMemo, useState } from 'react'

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table'
import {
  ArrowDown,
  ArrowUp,
  ChevronLeft,
  ChevronRight,
  ChevronsUpDown,
  Loader2,
  RotateCcw,
  Search,
} from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { listarRegistros } from '@/features/ingesta/api'
import { capitalizar, DEPARTAMENTOS, EVENTOS, SEXOS } from '@/features/ingesta/catalogos'
import { columnas } from '@/features/ingesta/columnas'
import type { ConsultaRegistros, RegistroAsistencia } from '@/features/ingesta/types'
import { mensajeDeError } from '@/lib/api'

const TAMANOS_DE_PAGINA = [25, 50, 100] as const
const TODOS = '__todos__'

interface Props {
  /** Cambia cuando se crea un registro; obliga a recargar la primera página. */
  recargar?: number
}

interface Filtros {
  search: string
  departamento: string
  evento: string
  sexo_titular: string
  es_poblacion_rural: string
  fecha_desde: string
  fecha_hasta: string
}

const FILTROS_INICIALES: Filtros = {
  search: '',
  departamento: TODOS,
  evento: TODOS,
  sexo_titular: TODOS,
  es_poblacion_rural: TODOS,
  fecha_desde: '',
  fecha_hasta: '',
}

/** Traduce el estado de orden de la tabla al parámetro `ordering` de DRF. */
function aOrdenDeApi(sorting: SortingState): string | undefined {
  const [orden] = sorting
  if (!orden) return undefined
  return orden.desc ? `-${orden.id}` : orden.id
}

export function TablaRegistros({ recargar = 0 }: Props) {
  const [datos, setDatos] = useState<RegistroAsistencia[]>([])
  const [total, setTotal] = useState(0)
  const [cargando, setCargando] = useState(true)
  const [pagina, setPagina] = useState(0)
  const [tamanoPagina, setTamanoPagina] = useState<number>(25)
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'fecha', desc: true },
  ])
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_INICIALES)
  const [busquedaEscrita, setBusquedaEscrita] = useState('')

  // La búsqueda libre se aplica con retardo para no emitir una petición por
  // cada tecla y consumir la cuota de tasa del usuario.
  useEffect(() => {
    const temporizador = setTimeout(
      () => setFiltros((previos) => ({ ...previos, search: busquedaEscrita })),
      400,
    )
    return () => clearTimeout(temporizador)
  }, [busquedaEscrita])

  // Cualquier cambio de filtro u orden invalida la página actual.
  useEffect(() => {
    setPagina(0)
  }, [filtros, sorting, tamanoPagina])

  const consulta = useMemo<ConsultaRegistros>(() => {
    const parametros: ConsultaRegistros = {
      page: pagina + 1,
      page_size: tamanoPagina,
      ordering: aOrdenDeApi(sorting),
    }

    if (filtros.search) parametros.search = filtros.search
    if (filtros.departamento !== TODOS) parametros.departamento = filtros.departamento
    if (filtros.evento !== TODOS) parametros.evento = filtros.evento
    if (filtros.sexo_titular !== TODOS) parametros.sexo_titular = filtros.sexo_titular
    if (filtros.es_poblacion_rural !== TODOS) {
      parametros.es_poblacion_rural = filtros.es_poblacion_rural === 'rural'
    }
    if (filtros.fecha_desde) parametros.fecha_desde = filtros.fecha_desde
    if (filtros.fecha_hasta) parametros.fecha_hasta = filtros.fecha_hasta

    return parametros
  }, [pagina, tamanoPagina, sorting, filtros])

  useEffect(() => {
    let activo = true
    setCargando(true)

    listarRegistros(consulta)
      .then((respuesta) => {
        if (!activo) return
        setDatos(respuesta.results)
        setTotal(respuesta.count)
      })
      .catch((error) => {
        if (!activo) return
        setDatos([])
        setTotal(0)
        toast.error('No se pudieron cargar los registros', {
          description: mensajeDeError(error),
        })
      })
      .finally(() => activo && setCargando(false))

    return () => {
      activo = false
    }
  }, [consulta, recargar])

  const cantidadPaginas = Math.max(1, Math.ceil(total / tamanoPagina))

  const tabla = useReactTable({
    data: datos,
    columns: columnas,
    getCoreRowModel: getCoreRowModel(),
    // El servidor pagina y ordena; la tabla solo refleja ese estado.
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
    pageCount: cantidadPaginas,
    state: {
      sorting,
      pagination: { pageIndex: pagina, pageSize: tamanoPagina },
    },
    onSortingChange: setSorting,
  })

  const hayFiltrosActivos =
    JSON.stringify(filtros) !== JSON.stringify(FILTROS_INICIALES)

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <CardTitle>
          Registros cargados
          <span className="ml-2 font-normal text-muted-foreground">
            ({total.toLocaleString('es-PY')})
          </span>
        </CardTitle>
        {hayFiltrosActivos && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setFiltros(FILTROS_INICIALES)
              setBusquedaEscrita('')
            }}
          >
            <RotateCcw className="h-4 w-4" />
            Limpiar filtros
          </Button>
        )}
      </CardHeader>

      {/* --- Filtros ------------------------------------------------- */}
      <div className="grid gap-3 border-b border-border bg-surface p-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
        <div className="space-y-1.5 xl:col-span-2">
          <Label htmlFor="busqueda">Búsqueda</Label>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              id="busqueda"
              className="pl-8"
              placeholder="Distrito, localidad u observaciones"
              value={busquedaEscrita}
              onChange={(evento) => setBusquedaEscrita(evento.target.value)}
              maxLength={120}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label>Zona</Label>
          <Select
            value={filtros.es_poblacion_rural}
            onValueChange={(valor) =>
              setFiltros((previos) => ({ ...previos, es_poblacion_rural: valor }))
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todas</SelectItem>
              <SelectItem value="rural">Rural</SelectItem>
              <SelectItem value="urbana">Urbana</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Sexo del titular</Label>
          <Select
            value={filtros.sexo_titular}
            onValueChange={(valor) =>
              setFiltros((previos) => ({ ...previos, sexo_titular: valor }))
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos</SelectItem>
              {SEXOS.map(({ valor, etiqueta }) => (
                <SelectItem key={valor} value={valor}>
                  {etiqueta}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Departamento</Label>
          <Select
            value={filtros.departamento}
            onValueChange={(valor) =>
              setFiltros((previos) => ({ ...previos, departamento: valor }))
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos</SelectItem>
              {DEPARTAMENTOS.map((departamento) => (
                <SelectItem key={departamento} value={departamento}>
                  {capitalizar(departamento)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Evento</Label>
          <Select
            value={filtros.evento}
            onValueChange={(valor) =>
              setFiltros((previos) => ({ ...previos, evento: valor }))
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos</SelectItem>
              {EVENTOS.map((evento) => (
                <SelectItem key={evento} value={evento}>
                  {evento === 'C.I.D.H.' ? evento : capitalizar(evento)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1.5">
            <Label htmlFor="desde">Desde</Label>
            <Input
              id="desde"
              type="date"
              value={filtros.fecha_desde}
              onChange={(evento) =>
                setFiltros((previos) => ({
                  ...previos,
                  fecha_desde: evento.target.value,
                }))
              }
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="hasta">Hasta</Label>
            <Input
              id="hasta"
              type="date"
              value={filtros.fecha_hasta}
              onChange={(evento) =>
                setFiltros((previos) => ({
                  ...previos,
                  fecha_hasta: evento.target.value,
                }))
              }
            />
          </div>
        </div>
      </div>

      {/* --- Tabla --------------------------------------------------- */}
      <CardContent className="p-0">
        <div className="relative max-h-[60vh] overflow-auto">
          {cargando && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/60">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
          )}

          <Table>
            <TableHeader className="sticky top-0 z-[1]">
              {tabla.getHeaderGroups().map((grupo) => (
                <TableRow key={grupo.id}>
                  {grupo.headers.map((encabezado) => {
                    const ordenable = encabezado.column.getCanSort()
                    const orden = encabezado.column.getIsSorted()
                    return (
                      <TableHead key={encabezado.id}>
                        {ordenable ? (
                          <button
                            type="button"
                            className="flex items-center gap-1 uppercase tracking-wide hover:text-foreground"
                            onClick={encabezado.column.getToggleSortingHandler()}
                            aria-label={`Ordenar por ${String(
                              encabezado.column.columnDef.header,
                            )}`}
                          >
                            {flexRender(
                              encabezado.column.columnDef.header,
                              encabezado.getContext(),
                            )}
                            {orden === 'asc' ? (
                              <ArrowUp className="h-3 w-3 text-primary" />
                            ) : orden === 'desc' ? (
                              <ArrowDown className="h-3 w-3 text-primary" />
                            ) : (
                              <ChevronsUpDown className="h-3 w-3 opacity-40" />
                            )}
                          </button>
                        ) : (
                          flexRender(
                            encabezado.column.columnDef.header,
                            encabezado.getContext(),
                          )
                        )}
                      </TableHead>
                    )
                  })}
                </TableRow>
              ))}
            </TableHeader>

            <TableBody>
              {tabla.getRowModel().rows.length === 0 && !cargando ? (
                <TableRow>
                  <TableCell
                    colSpan={columnas.length}
                    className="h-28 text-center text-muted-foreground"
                  >
                    No hay registros que coincidan con los filtros aplicados.
                  </TableCell>
                </TableRow>
              ) : (
                tabla.getRowModel().rows.map((fila) => (
                  <TableRow key={fila.id}>
                    {fila.getVisibleCells().map((celda) => (
                      <TableCell key={celda.id}>
                        {flexRender(celda.column.columnDef.cell, celda.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>

      {/* --- Paginación ---------------------------------------------- */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border p-3">
        <div className="flex items-center gap-2">
          <Label htmlFor="tamano" className="text-xs">
            Filas por página
          </Label>
          <Select
            value={String(tamanoPagina)}
            onValueChange={(valor) => setTamanoPagina(Number(valor))}
          >
            <SelectTrigger id="tamano" className="h-8 w-20">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TAMANOS_DE_PAGINA.map((tamano) => (
                <SelectItem key={tamano} value={String(tamano)}>
                  {tamano}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <p className="text-sm text-muted-foreground">
          Página {pagina + 1} de {cantidadPaginas}
        </p>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={pagina === 0 || cargando}
            onClick={() => setPagina((previa) => Math.max(0, previa - 1))}
          >
            <ChevronLeft className="h-4 w-4" />
            Anterior
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={pagina + 1 >= cantidadPaginas || cargando}
            onClick={() => setPagina((previa) => previa + 1)}
          >
            Siguiente
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  )
}
