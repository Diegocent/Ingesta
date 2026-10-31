/**
 * Almacenamiento de tokens de sesión.
 *
 * El token de acceso vive solo en memoria: si se guardara en `localStorage`,
 * cualquier XSS podría leerlo y reutilizarlo desde otra máquina. Al estar en el
 * cierre de este módulo, desaparece al recargar la página.
 *
 * El token de refresco se guarda en `sessionStorage` para sobrevivir a una
 * recarga sin obligar al operador a autenticarse de nuevo. Es una concesión
 * consciente: `sessionStorage` sigue siendo accesible por JavaScript, pero se
 * limita a la pestaña y se borra al cerrarla. La alternativa robusta —cookie
 * `HttpOnly` + `SameSite=Strict` emitida por el backend— queda para la Fase 2,
 * porque exige un endpoint de sesión propio en lugar del de SimpleJWT.
 */

const CLAVE_REFRESCO = 'ingesta_sen.refresh'

let tokenDeAcceso: string | null = null

export const tokens = {
  obtenerAcceso: () => tokenDeAcceso,

  obtenerRefresco: () => {
    try {
      return sessionStorage.getItem(CLAVE_REFRESCO)
    } catch {
      return null
    }
  },

  guardar: ({ access, refresh }: { access: string; refresh?: string }) => {
    tokenDeAcceso = access
    if (refresh) {
      try {
        sessionStorage.setItem(CLAVE_REFRESCO, refresh)
      } catch {
        // Navegador con almacenamiento bloqueado: la sesión durará lo que
        // dure el token de acceso en memoria.
      }
    }
  },

  limpiar: () => {
    tokenDeAcceso = null
    try {
      sessionStorage.removeItem(CLAVE_REFRESCO)
    } catch {
      // Sin almacenamiento disponible no hay nada que limpiar.
    }
  },
}
