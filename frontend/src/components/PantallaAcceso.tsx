import { useState } from 'react'

import { Loader2, LogIn, ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { autenticar, mensajeDeError } from '@/lib/api'

interface Props {
  onAcceso: (usuario: string) => void
}

export function PantallaAcceso({ onAcceso }: Props) {
  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault()
    setEnviando(true)
    try {
      await autenticar(usuario.trim(), contrasena)
      onAcceso(usuario.trim())
    } catch (error) {
      // No se distingue entre usuario inexistente y contraseña incorrecta:
      // hacerlo permitiría enumerar cuentas válidas.
      toast.error('No se pudo iniciar sesión', {
        description: mensajeDeError(error),
      })
      setContrasena('')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <div className="mx-auto mb-1 flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <CardTitle>Ingesta de Asistencia Humanitaria</CardTitle>
          <CardDescription>
            Acceso restringido a personal autorizado.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={enviar} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="usuario">Usuario</Label>
              <Input
                id="usuario"
                autoComplete="username"
                required
                maxLength={150}
                value={usuario}
                onChange={(evento) => setUsuario(evento.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="contrasena">Contraseña</Label>
              <Input
                id="contrasena"
                type="password"
                autoComplete="current-password"
                required
                value={contrasena}
                onChange={(evento) => setContrasena(evento.target.value)}
              />
            </div>
            <Button type="submit" className="w-full" disabled={enviando}>
              {enviando ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <LogIn className="h-4 w-4" />
              )}
              Ingresar
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
