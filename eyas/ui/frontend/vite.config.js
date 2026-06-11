import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/ui/',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/gradio_api': 'http://localhost:7860',
      '/run': 'http://localhost:7860',
      '/upload': 'http://localhost:7860',
    },
  },
})
