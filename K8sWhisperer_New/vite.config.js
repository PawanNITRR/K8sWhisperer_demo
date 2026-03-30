import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: browser calls /state → proxied to FastAPI (avoids CORS during npm run dev)
const API = process.env.VITE_DEV_API_PROXY || 'http://127.0.0.1:8081'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/health': { target: API, changeOrigin: true },
      '/state': { target: API, changeOrigin: true },
      '/slack': { target: API, changeOrigin: true },
    },
  },
})
