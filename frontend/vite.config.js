// Vite config — sets up the React plugin and proxies /query calls to the FastAPI backend on port 8000.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
