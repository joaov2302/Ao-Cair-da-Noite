import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./e2e', timeout:60000, fullyParallel:false, workers:1,
  reporter:'list', use:{baseURL:'http://127.0.0.1:5173',trace:'retain-on-failure'},
  webServer:[
    {command:`${process.platform==='win32'?'..\\.venv\\Scripts\\python.exe':'../.venv/bin/python'} ../backend/manage.py runserver 127.0.0.1:8000 --noreload`,url:'http://127.0.0.1:8000/api/session',reuseExistingServer:!process.env.CI,timeout:30000},
    {command:'npm run dev',url:'http://127.0.0.1:5173',reuseExistingServer:!process.env.CI,timeout:30000},
  ]
});
