import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'

import { tokens } from '@/lib/tokens'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 20_000,
  headers: { 'Content-Type': 'application/json' },
  // La API se autentica con el encabezado Authorization, no con cookies. Sin
  // credenciales de origen cruzado no hay superficie para CSRF.
  withCredentials: false,
})

/** Evento que emite el cliente cuando la sesión deja de ser válida. */
export const EVENTO_SESION_EXPIRADA = 'ingesta:sesion-expirada'

type ConfigConReintento = InternalAxiosRequestConfig & { _reintentado?: boolean }

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const acceso = tokens.obtenerAcceso()
  if (acceso) {
    config.headers = AxiosHeaders.from(config.headers)
    config.headers.set('Authorization', `Bearer ${acceso}`)
  }
  return config
})

// Un único refresco en vuelo: sin esta cola, N peticiones simultáneas que
// reciben 401 dispararían N refrescos y, con rotación de tokens activada,
// todos menos uno quedarían invalidados.
let refrescoEnCurso: Promise<string> | null = null

async function refrescarToken(): Promise<string> {
  const refresh = tokens.obtenerRefresco()
  if (!refresh) throw new Error('No hay token de refresco disponible.')

  const { data } = await axios.post<{ access: string; refresh?: string }>(
    `${BASE_URL}/auth/token/refresh/`,
    { refresh },
    { headers: { 'Content-Type': 'application/json' } },
  )

  tokens.guardar({ access: data.access, refresh: data.refresh })
  return data.access
}

api.interceptors.response.use(
  (respuesta) => respuesta,
  async (error: AxiosError) => {
    const config = error.config as ConfigConReintento | undefined
    const esReintentable =
      error.response?.status === 401 &&
      config &&
      !config._reintentado &&
      !config.url?.includes('/auth/token')

    if (esReintentable) {
      config._reintentado = true
      try {
        refrescoEnCurso ??= refrescarToken().finally(() => {
          refrescoEnCurso = null
        })
        await refrescoEnCurso
        return api(config)
      } catch {
        tokens.limpiar()
        window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA))
      }
    }

    return Promise.reject(error)
  },
)

/** Traduce un error de Axios al mensaje que se le muestra al operador. */
export function mensajeDeError(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return 'Ocurrió un error inesperado.'
  }

  if (!error.response) {
    return 'No se pudo contactar al servidor. Verifique su conexión.'
  }

  const { status, data, headers } = error.response

  if (status === 429) {
    const esperar = Number(headers['retry-after'])
    return Number.isFinite(esperar)
      ? `Demasiadas peticiones. Reintente en ${esperar} segundos.`
      : 'Demasiadas peticiones. Aguarde unos instantes antes de reintentar.'
  }

  if (status === 401) return 'Su sesión expiró. Vuelva a autenticarse.'
  if (status === 403) return 'No cuenta con permisos para esta operación.'
  if (status >= 500) return 'El servidor no pudo procesar la solicitud.'

  if (status === 400 && data && typeof data === 'object') {
    const detalle = Object.values(data as Record<string, unknown>)
      .flat()
      .filter((valor): valor is string => typeof valor === 'string')
    if (detalle.length > 0) return detalle.join(' ')
  }

  return 'La solicitud no pudo completarse.'
}

/** Errores de validación del backend, mapeados por campo. */
export function erroresDeCampo(error: unknown): Record<string, string> {
  if (!axios.isAxiosError(error) || error.response?.status !== 400) return {}

  const data = error.response.data
  if (!data || typeof data !== 'object') return {}

  return Object.fromEntries(
    Object.entries(data as Record<string, unknown>).map(([campo, mensajes]) => [
      campo,
      Array.isArray(mensajes) ? String(mensajes[0]) : String(mensajes),
    ]),
  )
}

export async function autenticar(usuario: string, contrasena: string) {
  const { data } = await axios.post<{ access: string; refresh: string }>(
    `${BASE_URL}/auth/token/`,
    { username: usuario, password: contrasena },
    { headers: { 'Content-Type': 'application/json' } },
  )
  tokens.guardar(data)
  return data
}

export type { AxiosRequestConfig }
