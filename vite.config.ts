import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins:[react()],
  server:{
    host:'0.0.0.0',
    port:5173,
    // Fail loudly instead of silently moving to 5174 (a preview pointed at the
    // old port would look like a dead server).
    strictPort:true,
    allowedHosts:true,
    // REQUIRED for embedded previews. A sandboxed iframe has an opaque "null"
    // origin, making every module request cross-origin. Without
    // Access-Control-Allow-Origin the scripts are blocked and the app mounts
    // nothing (blank page). Dev-server only; the production server sets its own.
    cors:{origin:'*'},
    headers:{'Access-Control-Allow-Origin':'*'},
    proxy:{'/api':'http://127.0.0.1:3001'}
  }
});
