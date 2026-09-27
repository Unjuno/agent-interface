/** Persistent host adapter to the existing sequential relay. No action selection or replay. */
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { mkdir, writeFile, appendFile } from 'node:fs/promises';
import { join } from 'node:path';

export async function createRelayClient({ command, args, evidenceDirectory }) {
  if (typeof command !== 'string' || !command || !Array.isArray(args) ||
      args.some(arg => typeof arg !== 'string') || typeof evidenceDirectory !== 'string') {
    throw new TypeError('explicit command, argument array and fresh evidence directory required');
  }
  await mkdir(evidenceDirectory); // Never overwrite an earlier session.
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
  for (const block of row.result.content) {
    if (block.type === 'text') await text(block.text);
    else if (block.type === 'image') await image({ bytes: Buffer.from(block.data, 'base64'), mimeType: block.mimeType });
    else await text(block);
  }
}