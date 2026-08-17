import { defineConfig } from 'vite';
import cesium from 'vite-plugin-cesium';

export default defineConfig({
  plugins: [cesium()],
  server: {
    port: 5174,
    proxy: {
      // Point at the backend's host-port (8001:8000 from docker-compose.yml) so
      // dev doesn't require the `full`-profile nginx (:8080). Production still
      // routes through nginx via the built image — that's unaffected.
      '/api': { target: 'http://localhost:8001', changeOrigin: true },
      '/output': { target: 'http://localhost:8001', changeOrigin: true },
    },
  },
  build: {
    target: 'es2020',
  },
});