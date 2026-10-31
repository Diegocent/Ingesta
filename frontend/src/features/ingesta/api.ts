import { api } from '@/lib/api'

import type {
  Catalogos,
  ConsultaRegistros,
  RegistroAsistencia,
  RespuestaPaginada,
} from '@/features/ingesta/types'

/** Descarta claves vacías para no enviar filtros sin valor. */
function limpiarParametros(consulta: ConsultaRegistros) {
  return Object.fromEntries(
    Object.entries(consulta).filter(
      ([, valor]) => valor !== undefined && valor !== '' && valor !== null,
    ),
  )
}

export async function listarRegistros(consulta: ConsultaRegistros) {
  const { data } = await api.get<RespuestaPaginada<RegistroAsistencia>>(
    '/registros/',
    { params: limpiarParametros(consulta) },
  )
  return data
}

export async function crearRegistro(payload: Record<string, unknown>) {
  const { data } = await api.post<RegistroAsistencia>('/registros/', payload)
  return data
}

export async function obtenerCatalogos() {
  const { data } = await api.get<Catalogos>('/catalogos/')
  return data
}
