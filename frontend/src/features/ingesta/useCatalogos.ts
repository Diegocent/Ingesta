import { useEffect, useState } from 'react'

import { obtenerCatalogos } from '@/features/ingesta/api'
import type { Catalogos } from '@/features/ingesta/types'

/**
 * Carga el catálogo oficial una sola vez por sesión.
 *
 * Es información estable (división político-administrativa y tipologías de
 * evento), así que se guarda en un módulo compartido en lugar de volver a
 * pedirla cada vez que se monta un componente.
 */
let cache: Catalogos | null = null
let peticionEnCurso: Promise<Catalogos> | null = null

function cargar() {
  if (cache) return Promise.resolve(cache)
  peticionEnCurso ??= obtenerCatalogos()
    .then((datos) => {
      cache = datos
      return datos
    })
    .finally(() => {
      peticionEnCurso = null
    })
  return peticionEnCurso
}

export function useCatalogos() {
  const [catalogos, setCatalogos] = useState<Catalogos | null>(cache)
  const [error, setError] = useState<unknown>(null)

  useEffect(() => {
    if (cache) return
    let activo = true
    cargar()
      .then((datos) => activo && setCatalogos(datos))
      .catch((fallo) => activo && setError(fallo))
    return () => {
      activo = false
    }
  }, [])

  return { catalogos, cargando: !catalogos && !error, error }
}
