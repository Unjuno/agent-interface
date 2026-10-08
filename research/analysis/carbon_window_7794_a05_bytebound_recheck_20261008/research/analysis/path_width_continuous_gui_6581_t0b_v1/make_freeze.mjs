import fs from 'node:fs/promises';
import crypto from 'node:crypto';

const root = new URL('.', import.meta.url);
const sha256 = async path => crypto.createHash('sha256').update(await fs.readFile(path === '.github/workflows/analysis-index.yml' ? new URL('../../../.github/workflows/analysis-index.yml', root) : new URL(path, root))).digest('hex');
const playwrightImage = 'mcr.microsoft.com/playwright@sha256:a51a0edc496f3e0cb386de2438eb1c2578de64cc7af60bfcbc7abfd410567fcd';
const auditorImage = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f';
const npmAudit = JSON.parse(await fs.readFile(new URL('construction_01/npm-audit-1551.json', root), 'utf8'));
if ((npmAudit.metadata?.vulnerabilities?.total ?? 1) !== 0) throw new Error('npm audit is not clean');
const packageInfo = JSON.parse(await fs.readFile(new URL('construction_01/npmproj_1551/node_modules/playwright/package.json', root), 'utf8'));
if (packageInfo.version !== '1.55.1') throw new Error('Playwright package version mismatch');
const sources = [
  'PREREGISTRATION.md', 'spec.json', 'fixture.html', 'run.mjs', 'audit.py',
  'test_contract.py', 'package.json', 'package-lock.json', 'make_freeze.mjs',
  '.github/workflows/analysis-index.yml'
];
const source_sha256 = {};
for (const path of sources) source_sha256[path] = await sha256(path);
const deps = await fs.readFile(new URL('construction_01/npm-deps-1551.json', root));
const freeze = {
  schema: 'path-width-gui-freeze-v1',
  allocation_id: 'PATH-WIDTH-CONTINUOUS-GUI-6581-T0B-20261002-01',
  main_base: '60e2e7bb8a69cb7270fc2082e0affc5bf2789876',
  branch: 'research/path-width-continuous-gui-6581-t0b-20261002',
  candidate_runs: 1,
  independent_auditor_runs: 1,
  formal_retries: 0,
  platform: 'linux/arm64',
  container: {
    machine: 'research-path-width-6581-t0b-20261002',
    os: 'Ubuntu 24.04 Noble ARM64',
    playwright_image: playwrightImage,
    playwright_package_version: packageInfo.version,
    node_version: '22.19.0',
    chromium_version: '140.0.7339.186',
    playwright_image_id: playwrightImage.slice(playwrightImage.indexOf('@') + 1),
    auditor_image: auditorImage,
    dependency_manifest_sha256: crypto.createHash('sha256').update(deps).digest('hex'),
    npm_audit_vulnerabilities: npmAudit.metadata.vulnerabilities.total,
    limits: { candidate: { cpus: 1, memory: '1g', pids: 256, network: 'none', rootfs: 'read-only' }, auditor: { cpus: 1, memory: '512m', pids: 128, network: 'none', rootfs: 'read-only' } }
  },
  source_sha256
};
await fs.writeFile(new URL('FREEZE.json', root), JSON.stringify(freeze, null, 2) + '\n', { flag: 'w' });
console.log(JSON.stringify({ playwright_package_version: packageInfo.version, source_count: sources.length, freeze_sha256: await sha256('FREEZE.json') }));
