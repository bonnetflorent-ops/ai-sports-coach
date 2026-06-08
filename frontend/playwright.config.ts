import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  timeout: 30000,

  use: {
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  // Démarrer le serveur frontend avant les tests
  webServer: {
    command: 'npx next dev --port 3000',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    cwd: '.',
    timeout: 30000,
  },
});
