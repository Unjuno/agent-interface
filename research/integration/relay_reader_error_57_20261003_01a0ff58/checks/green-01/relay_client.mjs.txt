/** Persistent host adapter to the existing sequential relay. No action selection or replay. */
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { mkdir, writeFile, appendFile, statfs } from 'node:fs/promises';
import { join, dirname } from 'node:path';

export async function createRelayClient({ command, args, evidenceDirectory,
    minimumEvidenceFreeBytes = 32 * 1024 * 1024 }) {
  if (typeof command !== 'string' || !command || !Array.isArray(args) ||
      args.some(arg => typeof arg !== 'string') || typeof evidenceDirectory !== 'string') {
    throw new TypeError('explicit command, argument array and fresh evidence directory required');
  }
  if (!Number.isSafeInteger(minimumEvidenceFreeBytes) || minimumEvidenceFreeBytes <= 0) {
    throw new TypeError('minimumEvidenceFreeBytes must be a positive safe integer');
  }
  async function capacity(path) {
    let fs;
    try { fs = await statfs(path, { bigint: true }); }
    catch (cause) {
      throw Object.assign(new Error('cannot inspect evidence capacity before relay startup', { cause }),
        { code: 'EVIDENCE_CAPACITY_UNKNOWN', observedPath: path });
    }
    if (fs.bsize <= 0n || fs.bavail < 0n) {
      throw Object.assign(new Error('invalid evidence capacity before relay startup'),
        { code: 'EVIDENCE_CAPACITY_UNKNOWN', observedPath: path });
    }
    const available = fs.bsize * fs.bavail;
    if (available < BigInt(minimumEvidenceFreeBytes)) {
      throw Object.assign(new Error(`insufficient evidence capacity before relay startup: ${available} bytes available, ${minimumEvidenceFreeBytes} required`),
        { code: 'EVIDENCE_CAPACITY', observedPath: path, availableBytes: available.toString(),
          minimumEvidenceFreeBytes });
    }
    return available;
  }
  // Check the existing parent before allocating on a known-full filesystem.
  await capacity(dirname(evidenceDirectory));
  await mkdir(evidenceDirectory); // Never overwrite an earlier session.
  // Inspect the actual new directory and retain a write before spawning a child.
  const available = await capacity(evidenceDirectory);
  await writeFile(join(evidenceDirectory, 'storage-preflight.json'), JSON.stringify({
    schema: 'agent-interface/evidence-storage-preflight-v1', observed_path: evidenceDirectory,
    observed_at: new Date().toISOString(), available_bytes: available.toString(),
    minimum_free_bytes: minimumEvidenceFreeBytes, child_started: false,
    capacity_reserved: false, future_writes_guaranteed: false,
    scope: 'Filesystem-reported availability at startup only; not physical backing capacity, quota, reservation, crash durability or subsequent-write proof.',
  }, null, 2) + '\n', { flag: 'wx' });
  let nextId = 1, current = null, blocked = null, terminal = null, closing = false;
  let journal = Promise.resolve();
  const record = (name, value) => writeFile(join(evidenceDirectory, name),
    JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  const child = spawn(command, args, { windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
  const exit = new Promise(resolve => child.once('close', (code, signal) => {
    terminal = { code, signal };
    journal = journal.then(() => record('exit.json', terminal));
    journal.then(() => resolve(terminal), error => resolve({ ...terminal, journal_error: String(error) }));
  }));
  function fail(error) {
    blocked = String(error);
    if (current && !current.settled) {
      current.settled = true;
      current.reject(new Error(blocked + '; delivery is uncertain: reconcile retained evidence, never replay'));
    }
  }
  child.on('error', fail);
  child.stdin.on('error', fail);
  child.once('exit', (code, signal) => {
    journal = journal.then(() => {
      if (current && !current.settled) fail(new Error(`relay exited (${code}, ${signal})`));
    });
    journal.catch(fail);
  });
  child.stderr.on('data', chunk => {
    journal = journal.then(() => appendFile(join(evidenceDirectory, 'stderr.log'), chunk));
    journal.catch(fail);
  });
  const reader = createInterface({ input: child.stdout, crlfDelay: Infinity });
  reader.on('error', fail);
  reader.on('line', line => {
    // Serialize persistence before releasing the result to the caller.
    const attempt = current;
    journal = journal.then(async () => {
      if (!attempt || attempt.settled) throw new Error('unsolicited relay response');
      await writeFile(join(evidenceDirectory, `reply-${attempt.number}.json`), line + '\n', { flag: 'wx' });
      const row = JSON.parse(line);
      const refused = row.status === 'refused' && row.dispatched === false;
      if (refused ? row.next_id !== attempt.request.id :
          row.id !== attempt.request.id || row.tool !== attempt.request.tool ||
          row.next_id !== attempt.request.id + 1 ||
          !['returned', 'unknown_requires_reconciliation'].includes(row.status)) {
        throw new Error('relay response identity/status mismatch');
      }
      nextId = row.next_id;
      attempt.settled = true;
      attempt.resolve(row);
    });
    journal.catch(fail);
  });
  let attempts = 0;
  return {
    send(tool, argumentsObject = {}) {
      if (blocked || terminal || closing || child.exitCode !== null) throw new Error(blocked || 'relay is not open');
      if (current && !current.settled) throw new Error('request outstanding; use wait(), do not resend');
      if (typeof tool !== 'string' || !argumentsObject || typeof argumentsObject !== 'object' || Array.isArray(argumentsObject)) {
        throw new TypeError('tool name and argument object required');
      }
      // Snapshot caller data once, before any asynchronous work.
      const request = JSON.parse(JSON.stringify({ id: nextId, tool, arguments: argumentsObject }, (_key, value) => {
        if (value === undefined || typeof value === 'function' || typeof value === 'symbol' ||
            (typeof value === 'number' && !Number.isFinite(value))) {
          throw new TypeError('request must contain only finite JSON values');
        }
        return value;
      }));
      const attempt = { number: ++attempts, request, settled: false };
      attempt.promise = new Promise((resolve, reject) => Object.assign(attempt, { resolve, reject }));
      attempt.promise.catch(() => {}); // Host timeout must not cause an unhandled rejection.
      current = attempt;
      journal = journal.then(async () => {
        await record(`request-${attempt.number}.json`, request);
        if (blocked || terminal || closing || child.exitCode !== null) throw new Error('relay ended before write');
        child.stdin.write(JSON.stringify(request) + '\n');
      });
      journal.catch(fail);
      return attempt.promise;
    },
    wait() {
      if (!current) throw new Error('no request to reconcile');
      return current.promise; // Same promise, including after it has settled.
    },
    state() {
      return { nextId, attempts, pending: !!current && !current.settled, blocked, terminal, closing };
    },
    async close() {
      if (current && !current.settled) throw new Error('request outstanding; wait before closing');
      closing = true;
      child.stdin.end();
      return exit; // Transport exit is not a GUI cleanup guarantee.
    },
  };
}

/** Preserve every content block; image bytes and text come from the same retained reply. */
export async function presentRelayResponse(row, { text, image }) {
  if (row.status !== 'returned' || !row.result || !Array.isArray(row.result.content)) {
    await text(row);
    return;
  }
  // Tool execution status is independent of text/image content, including
  // an empty content array. Preserve an explicit flag without inferring success.
  if (Object.hasOwn(row.result, 'isError')) {
    await text({ schema: 'agent-interface/mcp-result-status-v1', isError: row.result.isError });
  }
  for (const block of row.result.content) {
    if (block.type === 'text') await text(block.text);
    else if (block.type === 'image') await image({ bytes: Buffer.from(block.data, 'base64'), mimeType: block.mimeType });
    else await text(block);
  }
}
/** Record a caller's review against one explicit retained reply, never mutable latest state.
 * This records attribution, not proof that the caller saw or understood an image.
 */
export async function recordRelayReview({ replyPath, receiptPath, task, phase, reason }) {
  for (const value of [replyPath, receiptPath, task, phase, reason]) {
    if (typeof value !== 'string' || !value.trim()) throw new TypeError('explicit paths and review text required');
  }
  const { readFile } = await import('node:fs/promises');
  const { createHash } = await import('node:crypto');
  const bytes = await readFile(replyPath);
  const reply = JSON.parse(bytes);
  if (reply.status !== 'returned' || !Number.isSafeInteger(reply.id) || !Array.isArray(reply.result?.content)) {
    throw new Error('retained returned relay reply required');
  }
  const reports = [];
  const images = [];
  for (const block of reply.result.content) {
    if (block.type === 'text') {
      try {
        const value = JSON.parse(block.text);
        if (value?.call_id && (value?.source || value?.image_reference || value?.observation_report)) reports.push(value);
      } catch { /* Other text blocks are not report metadata. */ }
    } else if (block.type === 'image') {
      images.push({ mime_type: block.mimeType,
        sha256: createHash('sha256').update(Buffer.from(block.data, 'base64')).digest('hex') });
    }
  }
  if (reports.length !== 1 || images.length === 0) throw new Error('one sourced report and delivered image required');
  const report = reports[0];
  if (typeof report.call_id !== 'string') throw new Error('complete source identity required');
  let identity;
  if (report.source) {
    if (!Number.isSafeInteger(report.source.sequence) ||
        typeof report.source.observation_id !== 'string') throw new Error('complete source identity required');
    identity = {schema: 'agent-interface/primary-review-receipt-v1',
      source_sequence: report.source.sequence, observation_id: report.source.observation_id};
  } else {
    const reference = report.image_reference;
    const observationReport = report.observation_report;
    const observation = reference?.recorded_capture ?? observationReport?.observation;
    const artifactHash = reference?.sha256 ?? observation?.artifact?.sha256;
    if (report.image_status !== 'image' || images.length !== 1 ||
        (observationReport && observationReport.status !== 'returned') ||
        typeof artifactHash !== 'string' || !/^[a-f0-9]{64}$/.test(artifactHash) ||
        images[0].sha256 !== artifactHash || !observation ||
        typeof observation.target !== 'string' ||
        !Number.isSafeInteger(observation.native_window_id) ||
        !['window_client', 'screen_physical_px'].includes(observation.frame) ||
        !Array.isArray(observation.region) || observation.region.length !== 4 ||
        !observation.region.every(Number.isSafeInteger) ||
        !Number.isSafeInteger(observation.capture_started_ns) ||
        !Number.isSafeInteger(observation.capture_ended_ns) ||
        observation.capture_ended_ns < observation.capture_started_ns) {
      throw new Error('complete public capture identity and matching delivered image required');
    }
    identity = {schema: 'agent-interface/primary-review-receipt-v2-public-capture',
      source_sequence: null, observation_id: reference?.observation_id ?? observationReport?.observation_id ?? null,
      capture: {target: observation.target, native_window_id: observation.native_window_id,
        frame: observation.frame, region: observation.region,
        capture_started_ns: observation.capture_started_ns, capture_ended_ns: observation.capture_ended_ns,
        artifact_sha256: artifactHash},
      source_scope: 'retained public capture; no server-issued observation sequence or freshness'};
  }
  const receipt = {
    ...identity,
    task, phase, reason, recorded_at: new Date().toISOString(),
    relay_id: reply.id, tool: reply.tool, call_id: report.call_id,
    reply_sha256: createHash('sha256').update(bytes).digest('hex'), images,
    evidence_scope: 'caller-declared review; attribution only; not semantic success or measured model latency',
  };
  await writeFile(receiptPath, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  return receipt;
}
