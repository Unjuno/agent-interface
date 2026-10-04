import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import spec from './spec.json' with { type: 'json' };

const SELF = fileURLToPath(import.meta.url);
const LIMIT = spec.capture_limit_per_edge_bytes;

export function payloadFor(id) {
  if (id === 'short-exit') return Buffer.from('E_IMPORT:missing-fixture\n');
  if (id === 'pipe-capacity-flood') return Buffer.from('E_FLOOD:'.repeat(spec.cases[1].stderr_bytes / 8));
  if (id === 'ready-timeout') return Buffer.from('E_BOOT_WAIT:still-starting\n');
  if (id === 'ready-success') return Buffer.from('E_DIAGNOSTIC:nonfatal\n');
  throw new Error(`unknown case ${id}`);
}

export function boundedSummary(bytes) {
  const input = Buffer.from(bytes);
  return {
    total_bytes: input.length,
    sha256: createHash('sha256').update(input).digest('hex'),
    prefix_hex: input.subarray(0, LIMIT).toString('hex'),
    tail_hex: input.subarray(Math.max(0, input.length - LIMIT)).toString('hex'),
    truncated: input.length > LIMIT * 2,
    retained_bytes: Math.min(input.length, LIMIT) + Math.max(0, Math.min(input.length - LIMIT, LIMIT)),
  };
}

function childMode(id) {
  const data = payloadFor(id);
  if (id === 'pipe-capacity-flood') {
    let offset = 0;
    const writeNext = () => {
      while (offset < data.length) {
        const end = Math.min(data.length, offset + 8192);
        const accepted = process.stderr.write(data.subarray(offset, end));
        offset = end;
        if (!accepted) { process.stderr.once('drain', writeNext); return; }
      }
      process.exitCode = 23;
    };
    writeNext();
    return;
  }
  process.stderr.write(data);
  if (id === 'ready-timeout') {
    setInterval(() => {}, 1000);
  } else if (id === 'ready-success') {
    process.stdout.write('{"event":"ready","fixture":"finite-fixture-v1"}\n');
    setTimeout(() => { process.exitCode = 0; }, 20);
  } else {
    process.exitCode = 19;
  }
}

function boundedCollector(stream) {
  const hash = createHash('sha256');
  let total = 0;
  let prefix = Buffer.alloc(0);
  let tail = Buffer.alloc(0);
  stream.on('data', chunk => {
    const bytes = Buffer.from(chunk);
    total += bytes.length;
    hash.update(bytes);
    if (prefix.length < LIMIT) prefix = Buffer.concat([prefix, bytes.subarray(0, LIMIT - prefix.length)]);
    tail = Buffer.concat([tail, bytes]).subarray(-LIMIT);
  });
  return () => ({
    total_bytes: total,
    sha256: hash.copy().digest('hex'),
    prefix_hex: prefix.toString('hex'),
    tail_hex: tail.toString('hex'),
    truncated: total > LIMIT * 2,
    retained_bytes: prefix.length + Math.max(0, Math.min(total - prefix.length, LIMIT)),
  });
}

function waitForReadyOrClose(child, timeoutMs) {
  return new Promise(resolve => {
    let done = false;
    let buffer = '';
    const finish = value => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      resolve(value);
    };
    const timer = setTimeout(() => finish({ primary: 'READY_DEADLINE_EXCEEDED' }), timeoutMs);
    child.stdout.setEncoding('utf8');
    child.stdout.on('data', chunk => {
      buffer += chunk;
      for (;;) {
        const newline = buffer.indexOf('\n');
        if (newline < 0) break;
        const line = buffer.slice(0, newline);
        buffer = buffer.slice(newline + 1);
        try {
          const row = JSON.parse(line);
          if (row.event === 'ready') finish({ primary: 'READY_RECEIVED', ready_event: row });
        } catch { finish({ primary: 'MALFORMED_STDOUT_EVENT' }); }
      }
    });
    child.once('close', (code, signal) => finish({ primary: 'SESSION_EXIT_BEFORE_READY', exit_code: code, signal }));
    child.once('error', error => finish({ primary: 'SPAWN_ERROR', error: error.message }));
  });
}

export async function runCase(row) {
  const started = performance.now();
  const child = spawn(process.execPath, [SELF, '--child', row.id], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { PATH: process.env.PATH || '', NODE_NO_WARNINGS: '1' },
  });
  const snapshotStderr = boundedCollector(child.stderr);
  const closePromise = new Promise(resolve => child.once('close', (code, signal) => resolve({ code, signal })));
  const first = await waitForReadyOrClose(child, spec.deadline_ms);
  if (first.primary === 'READY_DEADLINE_EXCEEDED') child.kill('SIGTERM');
  const closed = await Promise.race([
    closePromise.then(() => true),
    new Promise(resolve => setTimeout(() => resolve(false), 1000)),
  ]);
  if (!closed) child.kill('SIGKILL');
  const closedAfterKill = closed || await Promise.race([
    closePromise.then(() => true),
    new Promise(resolve => setTimeout(() => resolve(false), 250)),
  ]);
  return {
    id: row.id,
    primary: first.primary,
    ready_event: first.ready_event || null,
    exit_code: child.exitCode,
    signal: child.signalCode,
    closed: closedAfterKill,
    elapsed_ms: Number((performance.now() - started).toFixed(3)),
    stderr: snapshotStderr(),
  };
}

export async function runExperiment(outPath) {
  const rows = [];
  for (const row of spec.cases) rows.push(await runCase(row));
  const raw = { schema: spec.schema, rows };
  await writeFile(outPath, `${JSON.stringify(raw, null, 2)}\n`, { flag: 'wx' });
  return raw;
}

if (process.argv[2] === '--child') childMode(process.argv[3]);
else if (process.argv[1] && path.resolve(process.argv[1]) === SELF) {
  const out = process.argv[2];
  if (!out) throw new Error('output path required');
  const result = await runExperiment(out);
  process.stdout.write(`${JSON.stringify({ status: 'CANDIDATE_EXIT_0', rows: result.rows.length })}\n`);
}
