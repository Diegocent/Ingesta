import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { Toaster } from 'sonner'

import App from '@/App'
import '@/index.css'

const contenedor = document.getElementById('root')
if (!contenedor) throw new Error('No se encontró el nodo raíz de la aplicación.')

createRoot(contenedor).render(
  <StrictMode>
    <App />
    <Toaster
      position="top-right"
      richColors
      closeButton
      toastOptions={{ duration: 5000 }}
    />
  </StrictMode>,
)
