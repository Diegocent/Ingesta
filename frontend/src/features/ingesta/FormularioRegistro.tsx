import { useMemo, useState } from 'react'

import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, MapPin, PackageCheck, Save, Users } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { crearRegistro } from '@/features/ingesta/api'
import {
  capitalizar,
  DEPARTAMENTOS,
  EVENTOS,
  INSUMOS,
  SEXOS,
} from '@/features/ingesta/catalogos'
import {
  aPayloadDeApi,
  esquemaRegistro,
  VALORES_INICIALES,
  type DatosRegistro,
} from '@/features/ingesta/schema'
import { useCatalogos } from '@/features/ingesta/useCatalogos'
import { erroresDeCampo, mensajeDeError } from '@/lib/api'
import type { RegistroAsistencia } from '@/features/ingesta/types'

interface Props {
  /** Se dispara tras un alta exitosa para que la tabla se refresque. */
  onRegistroCreado?: (registro: RegistroAsistencia) => void
}

/** Encabezado de sección con icono, para orientar la lectura del formulario. */
function TituloSeccion({
  icono: Icono,
  titulo,
  descripcion,
}: {
  icono: typeof MapPin
  titulo: string
  descripcion: string
}) {
  return (
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <Icono className="h-4 w-4 text-primary" />
        {titulo}
      </CardTitle>
      <CardDescription>{descripcion}</CardDescription>
    </CardHeader>
  )
}

export function FormularioRegistro({ onRegistroCreado }: Props) {
  const { catalogos } = useCatalogos()
  const [enviando, setEnviando] = useState(false)

  const formulario = useForm<DatosRegistro>({
    resolver: zodResolver(esquemaRegistro),
    defaultValues: VALORES_INICIALES,
    mode: 'onBlur',
  })

  const departamentoElegido = formulario.watch('departamento')
  const insumos = formulario.watch(INSUMOS.map(({ campo }) => campo))

  const distritosDisponibles = useMemo(
    () =>
      departamentoElegido
        ? (catalogos?.distritos_por_departamento[departamentoElegido] ?? [])
        : [],
    [catalogos, departamentoElegido],
  )

  const totalInsumos = insumos.reduce(
    (suma, valor) => suma + (Number.isFinite(valor) ? valor : 0),
    0,
  )

  async function enviar(datos: DatosRegistro) {
    setEnviando(true)
    try {
      const registro = await crearRegistro(aPayloadDeApi(datos))

      toast.success('Registro guardado', {
        description: `${capitalizar(registro.departamento)} · ${capitalizar(
          registro.distrito,
        )} · ${registro.total_insumos.toLocaleString('es-PY')} unidades.`,
      })

      // Se conservan fecha, ubicación y evento: lo habitual es cargar varias
      // asistencias del mismo operativo de forma consecutiva.
      formulario.reset({
        ...VALORES_INICIALES,
        fecha: datos.fecha,
        departamento: datos.departamento,
        distrito: datos.distrito,
        evento: datos.evento,
      })
      formulario.setFocus('localidad')
      onRegistroCreado?.(registro)
    } catch (error) {
      // Los errores por campo que devuelve el backend se muestran junto al
      // control correspondiente, no solo en la notificación.
      for (const [campo, mensaje] of Object.entries(erroresDeCampo(error))) {
        if (campo in VALORES_INICIALES || campo === 'departamento') {
          formulario.setError(campo as keyof DatosRegistro, {
            type: 'server',
            message: mensaje,
          })
        }
      }
      toast.error('No se pudo guardar el registro', {
        description: mensajeDeError(error),
      })
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Form {...formulario}>
      <form onSubmit={formulario.handleSubmit(enviar)} className="space-y-4">
        {/* --- Ubicación y evento ------------------------------------- */}
        <Card>
          <TituloSeccion
            icono={MapPin}
            titulo="Ubicación y evento"
            descripcion="Dónde y por qué motivo se entregó la asistencia."
          />
          <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <FormField
              control={formulario.control}
              name="fecha"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Fecha de la asistencia</FormLabel>
                  <FormControl>
                    <Input
                      type="date"
                      max={new Date().toLocaleDateString('en-CA')}
                      min="2018-01-01"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={formulario.control}
              name="departamento"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Departamento</FormLabel>
                  <Select
                    value={field.value ?? ''}
                    onValueChange={(valor) => {
                      field.onChange(valor)
                      // El distrito depende del departamento: al cambiarlo, el
                      // valor anterior deja de ser válido.
                      formulario.resetField('distrito', { defaultValue: '' })
                    }}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccione…" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {DEPARTAMENTOS.map((departamento) => (
                        <SelectItem key={departamento} value={departamento}>
                          {capitalizar(departamento)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={formulario.control}
              name="distrito"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Distrito</FormLabel>
                  <Select
                    value={field.value ?? ''}
                    onValueChange={field.onChange}
                    disabled={!departamentoElegido || distritosDisponibles.length === 0}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue
                          placeholder={
                            departamentoElegido
                              ? 'Seleccione…'
                              : 'Elija primero el departamento'
                          }
                        />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {distritosDisponibles.map((distrito) => (
                        <SelectItem key={distrito} value={distrito}>
                          {capitalizar(distrito)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={formulario.control}
              name="evento"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tipo de evento</FormLabel>
                  <Select value={field.value ?? ''} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccione…" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {EVENTOS.map((evento) => (
                        <SelectItem key={evento} value={evento}>
                          {evento === 'C.I.D.H.' ? evento : capitalizar(evento)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={formulario.control}
              name="localidad"
              render={({ field }) => (
                <FormItem className="sm:col-span-2">
                  <FormLabel>Localidad o barrio</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Opcional"
                      autoComplete="off"
                      maxLength={120}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Si se omite, se registra como «Sin especificar».
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={formulario.control}
              name="es_poblacion_rural"
              render={({ field }) => (
                <FormItem className="sm:col-span-2">
                  <FormLabel>Tipo de población</FormLabel>
                  <div className="flex h-9 items-center gap-3 rounded-md border border-input bg-background px-3 shadow-sm">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={(marcado) => field.onChange(marcado === true)}
                      />
                    </FormControl>
                    <span className="text-sm">
                      {field.value ? 'Población rural' : 'Población urbana'}
                    </span>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* --- Población asistida ------------------------------------- */}
        <Card>
          <TituloSeccion
            icono={Users}
            titulo="Población asistida"
            descripcion="Caracterización de los hogares que recibieron la asistencia."
          />
          <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <FormField
              control={formulario.control}
              name="sexo_titular"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Sexo del titular</FormLabel>
                  <Select value={field.value ?? ''} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccione…" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {SEXOS.map(({ valor, etiqueta }) => (
                        <SelectItem key={valor} value={valor}>
                          {etiqueta}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={formulario.control}
              name="cantidad_familias_asistidas"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Familias asistidas</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      inputMode="numeric"
                      min={1}
                      step={1}
                      placeholder="0"
                      {...field}
                      value={Number.isFinite(field.value) ? field.value : ''}
                      onChange={(evento) =>
                        field.onChange(evento.target.valueAsNumber)
                      }
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* --- Insumos ------------------------------------------------- */}
        <Card>
          <TituloSeccion
            icono={PackageCheck}
            titulo="Insumos entregados"
            descripcion="Debe registrarse al menos una unidad de algún insumo."
          />
          <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {INSUMOS.map(({ campo, etiqueta }) => (
              <FormField
                key={campo}
                control={formulario.control}
                name={campo}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{etiqueta}</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        inputMode="numeric"
                        min={0}
                        step={1}
                        {...field}
                        value={Number.isFinite(field.value) ? field.value : ''}
                        onChange={(evento) =>
                          field.onChange(evento.target.valueAsNumber)
                        }
                        onFocus={(evento) => evento.target.select()}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            ))}
          </CardContent>
        </Card>

        {/* --- Observaciones y envío ----------------------------------- */}
        <Card>
          <CardContent className="grid gap-4 lg:grid-cols-3">
            <FormField
              control={formulario.control}
              name="observaciones"
              render={({ field }) => (
                <FormItem className="lg:col-span-2">
                  <FormLabel>Observaciones</FormLabel>
                  <FormControl>
                    <Textarea
                      rows={3}
                      maxLength={500}
                      placeholder="Detalles relevantes del operativo (opcional)."
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {(field.value?.length ?? 0)}/500 caracteres.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex flex-col justify-end gap-3">
              <div className="rounded-md border border-border bg-surface p-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Total de insumos
                </p>
                <p className="text-2xl font-semibold tabular-nums text-primary">
                  {totalInsumos.toLocaleString('es-PY')}
                </p>
              </div>

              <div className="flex gap-2">
                <Button type="submit" disabled={enviando} className="flex-1">
                  {enviando ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  {enviando ? 'Guardando…' : 'Guardar registro'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={enviando}
                  onClick={() => formulario.reset(VALORES_INICIALES)}
                >
                  Limpiar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </form>
    </Form>
  )
}
