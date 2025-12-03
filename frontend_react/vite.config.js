import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  // Add this block below ⬇️
  preview: {
    allowedHosts: ["sunny-flow-production-b6eb.up.railway.app", "tagsafe.us"],
  },
})