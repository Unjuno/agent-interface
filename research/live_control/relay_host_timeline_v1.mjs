/** Opt-in host instrumentation. No model, task policy, input retry or action queue. */
import { readFile, writeFile, appendFile } from 'node:fs/promises';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { createRelayClient, presentRelayResponse, recordRelayReview } from './native_relay_client_v1.mjs';

export async function createInstrumentedRelayClient(options) {
  const evidenceDirectory = options.evidenceDirectory;
  const client = await createRelayClient(options);
  const eventsPath = join(evidenceDirectory, 'host-events.jsonl');
  try { await writeFile(eventsPath, '', { flag: 'wx' }); }
  catch (error) { await client.close(); throw error; }
  let sequence = 0, busy = null, blocked = null, pending = null, closed = false;
  const delivered = new Set();
  const event = async (kind, fields = {}) => {
    const row = { schema: 'agent-interface/relay-host-event-v1', sequence: ++sequence,
      host_monotonic_ms: performance.now(), kind, ...fields };
    await appendFile(eventsPath, JSON.stringify(row) + '\n');
    return row;
  };
  function begin(kind) {
    if (busy) throw new Error('host operation outstanding; wait, do not queue or resend');
    if (blocked || closed) throw new Error(blocked || 'instrumented client closed');
    busy = kind;
  }
  function failed(error) { blocked = String(error); throw error; }
  async function retained(attempt) {
    if (!Number.isSafeInteger(attempt) || !delivered.has(attempt)) throw new Error('explicit delivered attempt required');
    const replyPath = join(evidenceDirectory, `reply-${attempt}.json`);
    const bytes = await readFile(replyPath);
    return { replyPath, reply: JSON.parse(bytes), reply_sha256: createHash('sha256').update(bytes).digest('hex') };
  }
  return {
    send(tool, args = {}) {
      begin('send');
      // Snapshot synchronously, before the instrumentation's asynchronous write.
      let snapshot;
      try {
        snapshot = JSON.parse(JSON.stringify(args, (_key, value) => {
          if (value === undefined || typeof value === 'function' || typeof value === 'symbol' ||
              (typeof value === 'number' && !Number.isFinite(value))) throw new TypeError('finite JSON required');
          return value;
        }));
        if (typeof tool !== 'string' || !snapshot || Array.isArray(snapshot) || typeof snapshot !== 'object') throw new TypeError('tool and argument object required');
      } catch (error) { busy = null; throw error; }
      const attempt = client.state().attempts + 1;
      pending = (async () => {
        try {
          await event('send_requested', { attempt, tool });
          const reply = await client.send(tool, snapshot);
          const bytes = await readFile(join(evidenceDirectory, `reply-${attempt}.json`));
          await event('reply_available', { attempt, tool, relay_id: reply.id ?? null,
            reply_sha256: createHash('sha256').update(bytes).digest('hex') });
          delivered.add(attempt);
          return reply;
        } catch (error) { return failed(error); }
        finally { busy = null; }
      })();
      pending.catch(() => {});
      return pending;
    },
    wait() {
      if (!pending) throw new Error('no request to reconcile');
      return pending;
    },
    async present(attempt, callbacks) {
      begin('present');
      try {
        const saved = await retained(attempt);
        await event('presentation_started', { attempt, reply_sha256: saved.reply_sha256 });
        await presentRelayResponse(saved.reply, callbacks);
        await event('presentation_callbacks_completed', { attempt, reply_sha256: saved.reply_sha256 });
      } catch (error) { return failed(error); }
      finally { busy = null; }
    },
    async review(attempt, { task, phase, reason }) {
      begin('review');
      try {
        const saved = await retained(attempt);
        const receipt = await recordRelayReview({ replyPath: saved.replyPath,
          receiptPath: join(evidenceDirectory, `review-${attempt}.json`), task, phase, reason });
        await event('review_recorded', { attempt, reply_sha256: receipt.reply_sha256,
          call_id: receipt.call_id, source_sequence: receipt.source_sequence, task, phase });
        return receipt;
      } catch (error) { return failed(error); }
      finally { busy = null; }
    },
    state() { return { ...client.state(), host_busy: busy, host_blocked: blocked, host_closed: closed, event_sequence: sequence }; },
    async close() {
      if (busy) throw new Error('host operation outstanding; cannot close');
      if (closed) throw new Error('instrumented client already closed');
      busy = 'close';
      try {
        // Always permit transport cleanup after an instrumentation failure.
        const result = await client.close(); closed = true;
        await event('transport_closed', { code: result.code, signal: result.signal });
        return result;
      } catch (error) { return failed(error); }
      finally { busy = null; }
    },
  };
}