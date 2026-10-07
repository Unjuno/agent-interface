import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const SOURCE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(SOURCE, '..');
const OUT = path.join(ROOT, 'raw');
const IMAGE = 'node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80';

function run(file, args) {
  return execFileSync(file, args, { cwd: ROOT, encoding: 'utf8' }).trim();
}

function filesUnder(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...filesUnder(full));
    else if (entry.isFile()) files.push(full);
  }
  return files;
}

const image = run('docker', ['image', 'inspect', IMAGE, '--format', '{{.Id}} {{json .RepoDigests}}']);
const dockerVersion = run('docker', ['version', '--format', '{{.Client.Version}}/{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}']);
const dockerInfo = run('docker', ['info', '--format', '{{.OSType}}/{{.Architecture}} {{.Driver}}']);
if (!dockerInfo.toLowerCase().includes('linux/aarch64 overlayfs')) throw new Error(`STOP_RUNTIME_MISMATCH:${dockerInfo}`);
if (fs.existsSync(OUT) && fs.readdirSync(OUT).length) throw new Error('STOP_OUTPUT_NOT_EMPTY');
const files = Object.fromEntries(filesUnder(SOURCE).map(file => [path.relative(SOURCE, file).split(path.sep).join('/'), crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')]));
const freeze = { schema: '5420-conditional-kernel-freeze-v1', allocation_id: '5420-COND-KERNEL-T0-01',
  repository_head: run('git', ['rev-parse', 'HEAD']), docker: dockerVersion, engine: dockerInfo,
  image: IMAGE, image_inspect: image, source_path: 'research/analysis/privacy_conditional_kernel_5420_t0_20261004/src',
  files_sha256: files, test_command: 'docker run --pull=never --rm --platform linux/arm64 --network none --read-only --pids-limit 16 --mount type=bind,src=<SRC>,dst=/src,readonly node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 node /src/test.mjs',
  candidate_command: 'docker run --pull=never --rm --platform linux/arm64 --network none --read-only --pids-limit 16 --mount type=bind,src=<SRC>,dst=/src,readonly --mount type=bind,src=<RAW>,dst=/out node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 node /src/candidate.mjs',
  auditor_command: 'docker run --pull=never --rm --platform linux/arm64 --network none --read-only --pids-limit 16 --mount type=bind,src=<SRC>,dst=/src,readonly --mount type=bind,src=<RAW>,dst=/out node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 node /src/audit.mjs',
  decision_gate: 'Exact raw-only reconstruction of 16 rows and 3 scenarios; shared conditional gate reject while fresh and constant accept; marginal comparator accepts shared; all 4 mutations rejected.' };
fs.mkdirSync(OUT, { recursive: false });
fs.writeFileSync(path.join(OUT, 'freeze.json'), JSON.stringify(freeze, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ status: 'FROZEN', files: Object.keys(files).length, repository_head: freeze.repository_head, image: IMAGE, docker: dockerVersion, engine: dockerInfo }) + '\n');
