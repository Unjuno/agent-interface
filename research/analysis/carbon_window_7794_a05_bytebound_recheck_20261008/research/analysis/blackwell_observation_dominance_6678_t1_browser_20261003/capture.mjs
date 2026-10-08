import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const root = path.dirname(new URL(import.meta.url).pathname);
const out = process.argv[2];
if (!out) throw new Error('usage: node capture.mjs OUT_DIR');
const fixture = await readFile(path.join(root, 'fixture.html'), 'utf8');
const states = JSON.parse(await readFile(path.join(root, 'states.json'), 'utf8'));
const schedule = JSON.parse(await readFile(path.join(root, 'schedule.json'), 'utf8'));
await mkdir(out, { recursive: false });
const browser = await chromium.launch({ headless: true, args: ['--disable-background-networking', '--disable-component-update', '--no-first-run'] });
const version = browser.version();
const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');
try {
  const manifest = { schema: 'blackwell-6678-t1-raw-manifest-v1', browser_version: version, fixture_sha256: sha256(fixture), captures: [] };
  for (const item of schedule.captures) {
    const state = states.states.find((s) => s.id === item.state);
    const context = await browser.newContext({ viewport: { width: 960, height: 640 }, deviceScaleFactor: 1, colorScheme: 'light', reducedMotion: 'reduce' });
    const page = await context.newPage();
    await page.route('**/*', (route) => route.request().url().startsWith('about:') ? route.continue() : route.abort('blockedbyclient'));
    await page.setContent(fixture, { waitUntil: 'load' });
    await page.locator('#left-target').evaluate((el, s) => {
      const active = s.left === 'LEFT TARGET ACTIVE'; el.className = `card ${active ? 'active-left' : 'inactive'}`;
      el.setAttribute('aria-label', s.left); el.textContent = s.left;
    }, state);
    await page.locator('#right-target').evaluate((el, s) => {
      const active = s.right === 'RIGHT TARGET ACTIVE'; el.className = `card ${active ? 'active-right' : 'inactive'}`;
      el.setAttribute('aria-label', s.right); el.textContent = s.right;
    }, state);
    await page.waitForTimeout(states.quiescence_ms);
    const full = await page.screenshot({ fullPage: true, animations: 'disabled' });
    const left = await page.locator('#left').screenshot({ animations: 'disabled' });
    const right = await page.locator('#right').screenshot({ animations: 'disabled' });
    const accessibility = await page.locator('body').ariaSnapshot();
    await page.evaluate(() => {
      window.__mutationEvents = [];
      const observer = new MutationObserver((records) => window.__mutationEvents.push(...records.map((r) => ({ type: r.type, attributeName: r.attributeName, added: r.addedNodes.length, removed: r.removedNodes.length }))));
      observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true, characterData: true });
      window.__t1Observer = observer;
    });
    await page.waitForTimeout(states.quiescence_ms);
    const mutationDelta = await page.evaluate(() => { window.__t1Observer.disconnect(); return window.__mutationEvents; });
    const dir = path.join(out, item.capture_id);
    await mkdir(dir);
    const artifacts = { full_png: full, left_roi_png: left, right_roi_png: right,
      accessibility_snapshot: Buffer.from(accessibility), mutation_delta: Buffer.from(JSON.stringify(mutationDelta)) };
    const hashes = {};
    for (const [name, bytes] of Object.entries(artifacts)) {
      const ext = name.endsWith('_png') ? '.png' : '.json';
      const file = `${name}${ext}`;
      await writeFile(path.join(dir, file), bytes, { flag: 'wx' });
      hashes[file] = sha256(bytes);
    }
    manifest.captures.push({ ...item, artifacts: hashes });
    await context.close();
  }
  await writeFile(path.join(out, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx' });
} finally {
  await browser.close();
}
