import {defineConfig} from '@playwright/test';

export default defineConfig({
 testDir:'./qa',timeout:90000,expect:{timeout:15000},workers:1,retries:0,
 reporter:[['list'],['json',{outputFile:'../.runtime/evidencias/playwright.json'}]],
 outputDir:'../.runtime/playwright-output',
 use:{baseURL:process.env.IRPS_BASE_URL||`http://127.0.0.1:${process.env.IRPS_FRONTEND_PORT||5210}`,
 channel:'chrome',headless:true,trace:'off',screenshot:'off',actionTimeout:15000}
});
