import { defineConfig } from '@playwright/test';
const python = process.env.ACDN_TEST_PYTHON;
const manage = process.env.ACDN_TEST_MANAGE;
if (!/^acdn_e2e_[0-9a-f]{12}$/.test(process.env.ACDN_E2E_RUN || '') ||
    process.env.POSTGRES_DB !== process.env.ACDN_E2E_RUN ||
    process.env.DJANGO_SETTINGS_MODULE !== 'config.settings_test' || !python || !manage || !process.env.ACDN_ARTIFACT_DIR) {
  throw new Error('Execute npm run test:e2e para criar um banco PostgreSQL exclusivo.');
}
export default defineConfig({
  testDir:'./e2e', timeout:60000, fullyParallel:false, workers:1,
  outputDir:`${process.env.ACDN_ARTIFACT_DIR}/browser`,
  reporter:'list', use:{baseURL:'http://127.0.0.1:5175',trace:'retain-on-failure'},
  webServer:[
    {command:`"${python}" "${manage}" runserver 127.0.0.1:8011 --noreload`,url:'http://127.0.0.1:8011/api/session',reuseExistingServer:false,timeout:30000},
    {command:'npm run dev -- --port 5175 --strictPort',url:'http://127.0.0.1:5175',env:{ACDN_API_URL:'http://127.0.0.1:8011'},reuseExistingServer:false,timeout:30000},
  ]
});
