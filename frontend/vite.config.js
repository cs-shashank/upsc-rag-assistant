import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ask':    'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
      '/documents': 'http://127.0.0.1:8000',
    }
  }
})
