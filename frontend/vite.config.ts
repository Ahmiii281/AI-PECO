import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import compression from 'vite-plugin-compression';

export default defineConfig(() => {
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      plugins: [
        tailwindcss(),
        react(),
        compression({
          algorithm: 'brotliCompress',
          ext: '.br',
        }),
        compression({
          algorithm: 'gzip',
          ext: '.gz',
        }),
      ],
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      build: {
        reportCompressedSize: true,
        chunkSizeWarningLimit: 500,
        rollupOptions: {
          output: {
            manualChunks(id) {
              if (id.includes('node_modules')) {
                if (id.includes('react') || id.includes('react-dom') || id.includes('react-router-dom')) {
                  return 'vendor-react';
                }
                if (id.includes('recharts')) {
                  return 'vendor-charts';
                }
                if (id.includes('axios') || id.includes('dompurify') || id.includes('marked')) {
                  return 'vendor-utils';
                }
                return 'vendor';
              }
            },
          },
        },
      },
    };
});
