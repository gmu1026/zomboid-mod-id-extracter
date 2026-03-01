import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// For production (nginx), proxy /jobs and /workshop to the API server.
// For dev, vite proxy handles it automatically.
export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    proxy: {
      '/jobs': 'http://localhost:8000',
      '/workshop': 'http://localhost:8000',
    },
  },
})
