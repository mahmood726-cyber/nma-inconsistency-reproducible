// Runner config used for the v1.8.0 browser re-run (copied into the assembled site as hub/shared/tests/lane.config.mjs). Same settings as allmeta 1cb3f84
// hub/shared/tests/playwright.config.mjs, except: one worker, port 8088 (nma-inconsistency-parity and re-parity specs hard-code http://localhost:8088), msedge channel,
// and a static server that maps /r-shiny/shinylive/webr/ to a read-only checkout of the identical tree.
import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.mjs',
  timeout: 30_000,
  workers: 1,
  retries: 0,
  use: { baseURL: 'http://127.0.0.1:8088' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], channel: 'msedge' } }],
  webServer: {
    command: `python -I ${process.env.P16_RUNNER}/serve.py ../../.. ${process.env.ALLMETA_WEBR_DIR} 8088`,
    url: 'http://127.0.0.1:8088/nma-inconsistency/index.html',
    reuseExistingServer: false,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
