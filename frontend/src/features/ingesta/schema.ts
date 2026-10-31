import type { DefaultValues } from 'react-hook-form'
import { z } from 'zod'

import {
  DEPARTAMENTOS,
  EVENTOS,
  INSUMOS,
  SEXOS_VALORES,
} from '@/features/ingesta/catalogos'

/**
 * Esquema de validación del formulario de carga.
 *
 * Replica las reglas que el backend aplica en `Model.clean()` y en las
 * restricciones de la base de datos. La validación del cliente existe para dar
 * retroalimentación inmediata al operador, nunca como control de seguridad: el
 * servidor vuelve a validar todo, porque cualquier verificación que corra en el
 * navegador es modificable por quien la ejecuta.
 *
 * Las fechas se manejan como cadenas `YYYY-MM-DD` (el formato nativo de
 * `<input type="date">` y el que espera Django). Convertirlas a `Date` en el
 * medio introduce desfasajes de zona horaria que cambian el día del registro.
 */

const FECHA_MINIMA = '2018-01-01'
const MAX_UNIDADES_POR_INSUMO = 100_000
const MAX_FAMILIAS_ASISTIDAS = 50_000

/** Juego de caracteres admitido en los nombres geográficos. */
const PATRON_NOMBRE_GEOGRAFICO = /^[\p{L}\p{M}0-9 .,'\-/]+$/u

const fechaDeHoy = () => new Date().toLocaleDateString('en-CA')

/** Cantidad de insumos: entera, no negativa y acotada. */
const cantidadInsumo = z
  .number({ error: 'Ingrese un número válido.' })
  .int('Debe ser un número entero.')
  .min(0, 'No puede ser negativo.')
  .max(
    MAX_UNIDADES_POR_INSUMO,
    `No puede superar ${MAX_UNIDADES_POR_INSUMO.toLocaleString('es-PY')} unidades.`,
  )

const textoGeografico = (maximo: number) =>
  z
    .string()
    .trim()
    .max(maximo, `No puede superar los ${maximo} caracteres.`)
    .regex(
      PATRON_NOMBRE_GEOGRAFICO,
      "Solo se admiten letras, números, espacios y los signos . , ' - /",
    )

const camposDeInsumos = Object.fromEntries(
  INSUMOS.map(({ campo }) => [campo, cantidadInsumo]),
) as Record<(typeof INSUMOS)[number]['campo'], typeof cantidadInsumo>

export const esquemaRegistro = z
  .object({
    // --- Fecha ---------------------------------------------------------
    fecha: z
      .string()
      .min(1, 'Seleccione la fecha de la asistencia.')
      .regex(/^\d{4}-\d{2}-\d{2}$/, 'Fecha inválida.')
      .refine((valor) => valor >= FECHA_MINIMA, {
        error: 'La serie histórica comienza en enero de 2018.',
      })
      .refine((valor) => valor <= fechaDeHoy(), {
        error: 'La fecha no puede ser futura.',
      }),

    // --- Ubicación -----------------------------------------------------
    departamento: z.enum(DEPARTAMENTOS, {
      error: 'Seleccione un departamento.',
    }),
    distrito: textoGeografico(60).min(1, 'Seleccione un distrito.'),
    localidad: textoGeografico(120).or(z.literal('')),
    es_poblacion_rural: z.boolean(),

    // --- Evento --------------------------------------------------------
    evento: z.enum(EVENTOS, { error: 'Seleccione el tipo de evento.' }),

    // --- Población asistida --------------------------------------------
    sexo_titular: z.enum(SEXOS_VALORES, {
      error: 'Indique el sexo del titular.',
    }),
    cantidad_familias_asistidas: z
      .number({ error: 'Ingrese la cantidad de familias asistidas.' })
      .int('Debe ser un número entero.')
      .min(1, 'Debe asistirse al menos una familia.')
      .max(
        MAX_FAMILIAS_ASISTIDAS,
        `Verifique el dato: supera las ${MAX_FAMILIAS_ASISTIDAS.toLocaleString('es-PY')} familias.`,
      ),

    // --- Insumos entregados --------------------------------------------
    ...camposDeInsumos,

    observaciones: z
      .string()
      .trim()
      .max(500, 'Las observaciones no pueden superar los 500 caracteres.')
      .refine((valor) => !/[<>]/.test(valor), {
        error: 'No se admiten los caracteres < ni >.',
      })
      .or(z.literal('')),
  })
  // Regla de negocio heredada del BI: un registro sin insumos no representa
  // una asistencia, y el ETL histórico descartaba esas filas.
  .refine((datos) => INSUMOS.some(({ campo }) => datos[campo] > 0), {
    error: 'Registre al menos una unidad de algún insumo entregado.',
    path: ['kit_a'],
  })

export type DatosRegistro = z.infer<typeof esquemaRegistro>

/**
 * Valores iniciales. Los selectores quedan sin valor (`undefined`) para que el
 * operador deba elegir de forma consciente en lugar de aceptar un default.
 */
export const VALORES_INICIALES: DefaultValues<DatosRegistro> = {
  fecha: '',
  distrito: '',
  localidad: '',
  es_poblacion_rural: false,
  kit_a: 0,
  kit_b: 0,
  chapa_fibrocemento: 0,
  chapa_zinc: 0,
  colchones: 0,
  frazadas: 0,
  terciadas: 0,
  puntales: 0,
  carpas_plasticas: 0,
  observaciones: '',
}

/** Arma el cuerpo de la petición a partir de los datos ya validados. */
export function aPayloadDeApi(datos: DatosRegistro) {
  return {
    ...datos,
    localidad: datos.localidad.trim() || 'SIN ESPECIFICAR',
    observaciones: datos.observaciones.trim(),
  }
}
