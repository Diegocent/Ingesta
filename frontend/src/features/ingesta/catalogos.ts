/**
 * Catálogos del frontend.
 *
 * Solo se declaran aquí los conjuntos cerrados y cortos que Zod necesita en
 * tiempo de compilación (departamentos, eventos y sexo). Los distritos se
 * piden a `GET /api/v1/catalogos/`: son más de 250 y replicarlos garantizaría
 * que en algún momento queden desincronizados del backend.
 *
 * Los valores están en mayúsculas porque es el formato que almacena el Data
 * Warehouse; la etiqueta visible se escribe en capitalización normal.
 */

export const DEPARTAMENTOS = [
  'CONCEPCIÓN',
  'SAN PEDRO',
  'CORDILLERA',
  'GUAIRÁ',
  'CAAGUAZÚ',
  'CAAZAPÁ',
  'ITAPÚA',
  'MISIONES',
  'PARAGUARÍ',
  'ALTO PARANÁ',
  'CENTRAL',
  'ÑEEMBUCÚ',
  'AMAMBAY',
  'CANINDEYÚ',
  'PDTE. HAYES',
  'ALTO PARAGUAY',
  'BOQUERON',
  'CAPITAL',
] as const

export const EVENTOS = [
  'C.I.D.H.',
  'COVID',
  'EXTREMA VULNERABILIDAD',
  'INCENDIO',
  'INUNDACION',
  'OLLA POPULAR',
  "OPERATIVO JAHO'I",
  'OTROS',
  'SEQUIA',
  'TORMENTA SEVERA',
] as const

export const SEXOS = [
  { valor: 'M', etiqueta: 'Masculino' },
  { valor: 'F', etiqueta: 'Femenino' },
  { valor: 'O', etiqueta: 'Otro / No especificado' },
] as const

export const SEXOS_VALORES = ['M', 'F', 'O'] as const

/** Etiquetas legibles de los campos de insumos, en el orden del formulario. */
export const INSUMOS = [
  { campo: 'kit_a', etiqueta: 'Kit A' },
  { campo: 'kit_b', etiqueta: 'Kit B' },
  { campo: 'chapa_fibrocemento', etiqueta: 'Chapas de fibrocemento' },
  { campo: 'chapa_zinc', etiqueta: 'Chapas de zinc' },
  { campo: 'colchones', etiqueta: 'Colchones' },
  { campo: 'frazadas', etiqueta: 'Frazadas' },
  { campo: 'terciadas', etiqueta: 'Terciadas' },
  { campo: 'puntales', etiqueta: 'Puntales' },
  { campo: 'carpas_plasticas', etiqueta: 'Carpas plásticas' },
] as const

export type CampoInsumo = (typeof INSUMOS)[number]['campo']

/** Pasa 'SAN PEDRO' a 'San Pedro' para mostrarlo sin gritar al operador. */
export function capitalizar(texto: string): string {
  return texto
    .toLocaleLowerCase('es-PY')
    .replace(/(^|[\s./'-])([\p{L}])/gu, (_, separador: string, letra: string) =>
      separador + letra.toLocaleUpperCase('es-PY'),
    )
}
