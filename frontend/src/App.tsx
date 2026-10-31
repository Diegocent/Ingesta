import { useCallback, useEffect, useState } from 'react'

import { LogOut, ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'

import { PantallaAcceso } from '@/components/PantallaAcceso'
import { Button } from '@/components/ui/button'
import { FormularioRegistro } from '@/features/ingesta/FormularioRegistro'
import { TablaRegistros } from '@/features/ingesta/TablaRegistros'
import { EVENTO_SESION_EXPIRADA } from '@/lib/api'
import { tokens } from '@/lib/tokens'

export default function App() {
  const [usuario, setUsuario] = useState<string | null>(null)
  const [recargas, setRecargas] = useState(0)

  const cerrarSesion = useCallback(() => {
    tokens.limpiar()
    setUsuario(null)
  }, [])

  // El cliente HTTP avisa cuando el refresco de token falla; en ese punto la
  // sesión ya no es recuperable y hay que volver a autenticarse.
  useEffect(() => {
    const alExpirar = () => {
      cerrarSesion()
      toast.warning('Su sesión expiró', {
        description: 'Vuelva a ingresar para continuar operando.',
      })
    }
    window.addEventListener(EVENTO_SESION_EXPIRADA, alExpirar)
    return () => window.removeEventListener(EVENTO_SESION_EXPIRADA, alExpirar)
  }, [cerrarSesion])

  if (!usuario) {
    return <PantallaAcceso onAcceso={setUsuario} />
  }

  return (
    <div className="min-h-svh">
      <header className="border-b border-border bg-background">
        <div className="flex h-14 items-center justify-between gap-4 px-4 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold">
                Ingesta de Asistencia Humanitaria
              </p>
              <p className="text-xs text-muted-foreground">
                Secretaría de Emergencia Nacional
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-muted-foreground sm:inline">
              {usuario}
            </span>
            <Button variant="outline" size="sm" onClick={cerrarSesion}>
              <LogOut className="h-4 w-4" />
              Salir
            </Button>
          </div>
        </div>
        {/* Franja institucional */}
        <div className="h-1 bg-primary" />
      </header>

      <main className="space-y-6 p-4 lg:p-8">
        <section className="space-y-1">
          <h1 className="text-xl font-semibold">Carga de registros</h1>
          <p className="text-sm text-muted-foreground">
            Cada registro corresponde a una entrega de asistencia humanitaria en
            territorio. Los datos alimentan directamente el tablero de gestión.
          </p>
        </section>

        <FormularioRegistro
          onRegistroCreado={() => setRecargas((previas) => previas + 1)}
        />

        <TablaRegistros recargar={recargas} />
      </main>
    </div>
  )
}
