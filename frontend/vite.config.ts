import path from 'path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@src': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        assetFileNames: 'assets/[hash].[ext]',
        chunkFileNames: 'assets/[hash].js',
        entryFileNames: 'assets/[hash].js',
        manualChunks(id: string): string | undefined {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('leaflet')) return 'vendor-leaflet'
          if (id.includes('@tanstack')) return 'vendor-query'
          if (id.includes('react') || id.includes('react-dom')) return 'vendor-react'
          return undefined
        },
      },
    },
  },
})
