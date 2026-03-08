import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    host: true,   // expose to LAN (binds to 0.0.0.0)
    port: 5173,
    strictPort: true, // fail clearly instead of silently shifting to 5174
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
      '/bot': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/discoveries': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  }
})

