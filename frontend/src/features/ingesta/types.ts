/** Contratos de la API de ingesta. */

export interface RegistroAsistencia {
  id: number
  fecha: string
  anio: number
  mes: number
  nombre_mes: string
  departamento: string
  orden_departamento: number
  distrito: string
  localidad: string
  /**
   * Los tres campos de caracterización llegan nulos en los registros
   * importados de la planilla histórica, donde el dato nunca se relevó. El
   * formulario, en cambio, los exige siempre.
   */
  es_poblacion_rural: boolean | null
  zona: 'Rural' | 'Urbana' | 'No informado'
  es_poblacion_indigena: boolean | null
  tipo_poblacion: 'Indígena' | 'No indígena' | 'No informado'
  evento: string
  sexo_titular: 'M' | 'F' | 'O' | null
  sexo_titular_etiqueta: string
  cantidad_familias_asistidas: number | null
  kit_a: number
  kit_b: number
  chapa_fibrocemento: number
  chapa_zinc: number
  colchones: number
  frazadas: number
  terciadas: number
  puntales: number
  carpas_plasticas: number
  kit_sentencia: number
  kit_evento: number
  total_insumos: number
  observaciones: string
  origen: 'FORMULARIO' | 'EXCEL_HISTORICO'
  cargado_por: string | null
  creado_en: string
}

export interface RespuestaPaginada<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface Catalogos {
  departamentos: { valor: string; orden: number }[]
  distritos_por_departamento: Record<string, string[]>
  eventos: string[]
  sexos: { valor: string; etiqueta: string }[]
}

/** Parámetros de consulta del listado, tal como los espera el backend. */
export interface ConsultaRegistros {
  page: number
  page_size: number
  ordering?: string
  search?: string
  departamento?: string
  distrito?: string
  evento?: string
  sexo_titular?: string
  es_poblacion_rural?: boolean
  fecha_desde?: string
  fecha_hasta?: string
}
