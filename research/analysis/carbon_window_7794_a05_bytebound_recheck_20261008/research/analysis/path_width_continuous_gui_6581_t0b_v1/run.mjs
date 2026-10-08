import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import { chromium } from '/deps/node_modules/playwright/index.mjs';

const specBytes = await fs.readFile('/src/spec.json');
const htmlBytes = await fs.readFile('/src/fixture.html');
const freezeBytes = await fs.readFile('/src/FREEZE.json');
const spec = JSON.parse(specBytes.toString('utf8'));
const playwrightPackage = JSON.parse(await fs.readFile('/deps/node_modules/playwright/package.json', 'utf8'));
const freeze = JSON.parse(freezeBytes.toString('utf8'));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const freezeSha = sha(freezeBytes);
const imageRef = process.env.PATHWIDTH_IMAGE_REF || '';
if (freeze.container.playwright_image !== imageRef) throw new Error('runtime Playwright image differs from frozen image');
if (freeze.container.playwright_package_version !== playwrightPackage.version) throw new Error('runtime Playwright package differs from frozen version');
if (freeze.container.node_version !== process.versions.node) throw new Error('runtime Node.js differs from frozen version');
for (const relative of ['spec.json', 'fixture.html', 'run.mjs', 'package.json', 'package-lock.json']) {
  const expected = freeze.source_sha256[relative];
  if (!expected || sha(await fs.readFile(`/src/${relative}`)) !== expected) throw new Error(`frozen source hash mismatch: ${relative}`);
}
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
try {
  if (browser.version() !== freeze.container.chromium_version) throw new Error('runtime Chromium differs from frozen version');
  const page = await browser.newPage({ viewport: { width: 520, height: 520 }, deviceScaleFactor: 1 });
  await page.addInitScript(value => { window.__spec = value; }, spec);
  await page.goto('file:///src/fixture.html');
  const box = await page.locator('#surface').boundingBox();
  if (!box || Math.abs(box.width - 480) > 0.01 || Math.abs(box.height - 480) > 0.01) {
    throw new Error(`unexpected browser canvas bounds: ${JSON.stringify(box)}`);
  }
  const scenarios = [];
  for (const item of spec.scenarios) {
    await page.evaluate(id => window.beginScenario(id), item.id);
    const xy = ([x, y]) => [box.x + x * spec.coordinate_system.scale, box.y + y * spec.coordinate_system.scale];
    const start = xy(item.trace[0]);
    await page.mouse.move(...start);
    await page.mouse.down();
    for (const p of item.trace.slice(1)) await page.mouse.move(...xy(p));
    await page.mouse.up();
    const result = await page.evaluate(() => window.__last);
    if (!result || result.scenario_id !== item.id) throw new Error(`missing browser receipt for ${item.id}`);
    await page.screenshot({ path: `/out/${item.id}.png` });
    scenarios.push(result);
  }
  const raw = {
    schema: 'path-width-gui-raw-v1',
    allocation_id: 'PATH-WIDTH-CONTINUOUS-GUI-6581-T0B-20261002-01',
    run_role: process.env.RUN_ROLE || 'formal',
    freeze_sha256: freezeSha,
    runtime_image_ref: imageRef,
    fixture_spec_sha256: sha(specBytes),
    fixture_html_sha256: sha(htmlBytes),
    browser: { name: 'Chromium', version: browser.version(), playwright_package: playwrightPackage.version, platform: process.platform, arch: process.arch },
    scenarios
  };
  await fs.writeFile('/out/candidate.raw.json', JSON.stringify(raw, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({allocation_id: raw.allocation_id, browser: raw.browser, scenarios: scenarios.length,
    event_counts: scenarios.map(s => [s.scenario_id, s.raw_events.length]), raw_sha256: sha(Buffer.from(JSON.stringify(raw, null, 2) + '\n'))}));
} finally {
  await browser.close();
}
