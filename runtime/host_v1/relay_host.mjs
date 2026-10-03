/** Opt-in host instrumentation. No model, task policy, input retry or action queue. */
import { readFile, writeFile, appendFile } from 'node:fs/promises';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { createRelayClient, presentRelayResponse, recordRelayReview } from './relay_client.mjs';

export async function createInstrumentedRelayClient(options) {
  const reuseImages = options.reuseReviewedImages ?? false;
  if (typeof reuseImages !== 'boolean') throw new TypeError('reuseReviewedImages must be boolean');
  const evidenceDirectory = options.evidenceDirectory;
  const client = await createRelayClient(options);
  const eventsPath = join(evidenceDirectory, 'host-events.jsonl');
  try { await writeFile(eventsPath, '', { flag: 'wx' }); }
  catch (error) { await client.close(); throw error; }
  let sequence = 0, busy = null, blocked = null, pending = null, closed = false, reservation = null;
  const delivered = new Map();
  const completedPresentations = new Map();
  // One bounded, explicitly reviewed PNG base, scoped to this live host instance.
  // Equality is byte-for-byte encoded PNG equality, never a hash/perceptual gate.
  let imageBase = null, lastPresentation = null;
  function singlePng(reply) {
    const images = reply.result?.content?.filter(block => block.type === 'image') ?? [];
    if (reply.status !== 'returned' || images.length !== 1) return null;
    const block = images[0];
    if (block.mimeType !== 'image/png' || typeof block.data !== 'string' ||
        block.data.length > 16 * 1024 * 1024) return null;
    const bytes = Buffer.from(block.data, 'base64');
    if (!bytes.length || bytes.toString('base64') !== block.data) return null;
    return { data: block.data, mime_type: block.mimeType,
      image_sha256: createHash('sha256').update(bytes).digest('hex') };
  }
  const event = async (kind, fields = {}) => {
    const row = { schema: 'agent-interface/relay-host-event-v1', sequence: ++sequence,
      host_monotonic_ms: performance.now(), kind, ...fields };
    await appendFile(eventsPath, JSON.stringify(row) + '\n');
    return row;
  };
  function begin(kind, reservationToken = null) {
    if (busy || (reservation && reservation !== reservationToken)) throw new Error('host operation outstanding; wait, do not queue or resend');
    if (blocked || closed) throw new Error(blocked || 'instrumented client closed');
    busy = kind;
  }
  function failed(error) {
    imageBase = null; lastPresentation = null;
    blocked = String(error) + '; host evidence incomplete: reconcile retained files; never infer no input or replay';
    throw new Error(blocked, { cause: error });
  }
  async function retained(attempt) {
    if (!Number.isSafeInteger(attempt) || !delivered.has(attempt)) throw new Error('explicit delivered attempt required');
    const replyPath = join(evidenceDirectory, `reply-${attempt}.json`);
    const bytes = await readFile(replyPath);
    const reply_sha256 = createHash('sha256').update(bytes).digest('hex');
    if (reply_sha256 !== delivered.get(attempt)) throw new Error('retained bytes differ from original delivered reply');
    return { replyPath, reply: JSON.parse(bytes), reply_sha256 };
  }
  function snapshotAttribution(value) {
    if (value === null) return null;
    const required = ['evaluation_id', 'phase', 'model_stage_id'];
    const allowed = [...required, 'primary_call_id'];
    if (!value || Array.isArray(value) || typeof value !== 'object' ||
        Object.keys(value).some(key => !allowed.includes(key))) throw new TypeError('bounded caller attribution required');
    const row = {};
    for (const key of allowed) {
      if (!Object.hasOwn(value, key)) {
        if (required.includes(key)) throw new TypeError('missing caller attribution');
        continue;
      }
      const field = value[key];
      if (typeof field !== 'string' || !field.trim() || field.length > 128) throw new TypeError('bounded attribution string required');
      row[key] = field;
    }
    if (!['setup', 'preflight', 'cold_acquisition', 'warm_reuse', 'invalidation',
          'bounded_repair', 'subsequent_reuse', 'termination'].includes(row.phase)) throw new TypeError('known evaluation phase required');
    return row;
  }
  function send(tool, args = {}, reservationToken = null, attribution = null) {
      const attributionSnapshot = snapshotAttribution(attribution);
      begin('send', reservationToken);
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
          await event('send_requested', { attempt, tool, ...(attributionSnapshot ? { caller_attribution: attributionSnapshot } : {}) });
          const reply = await client.send(tool, snapshot);
          const bytes = await readFile(join(evidenceDirectory, `reply-${attempt}.json`));
          await event('reply_available', { attempt, tool, relay_id: reply.id ?? null,
            reply_sha256: createHash('sha256').update(bytes).digest('hex'),
            ...(attributionSnapshot ? { caller_attribution: attributionSnapshot } : {}) });
          delivered.set(attempt, createHash('sha256').update(bytes).digest('hex'));
          // Host-only identity; persisted relay bytes and protocol IDs stay unchanged.
          return { ...reply, attempt };
        } catch (error) { return failed(error); }
        finally { busy = null; }
      })();
      pending.catch(() => {});
      return pending;
    }
  async function present(attempt, callbacks, { forceImage = false } = {}, reservationToken = null) {
      if (typeof forceImage !== 'boolean') throw new TypeError('forceImage must be boolean');
      begin('present', reservationToken);
      try {
        const saved = await retained(attempt);
        const picture = reuseImages ? singlePng(saved.reply) : null;
        if (forceImage) imageBase = null;
        const delivery = reuseImages && picture && imageBase &&
            picture.mime_type === imageBase.mime_type && picture.data === imageBase.data
          ? { mode: 'reviewed-image-reference', base_attempt: imageBase.attempt,
              base_reply_sha256: imageBase.reply_sha256, base_review_sha256: imageBase.review_sha256,
              image_sha256: picture.image_sha256, mime_type: picture.mime_type }
          : { mode: 'full' };
        const extra = reuseImages ? { image_delivery: delivery } : {};
        await event('presentation_started', { attempt, reply_sha256: saved.reply_sha256, ...extra });
        const selectedCallbacks = delivery.mode === 'reviewed-image-reference'
          ? { text: callbacks.text, image: async () => callbacks.text({
              schema: 'agent-interface/reviewed-image-reference-v1', attempt,
              reply_sha256: saved.reply_sha256, ...delivery,
              scope: 'Same PNG bytes as the explicitly reviewed base. Current reply metadata is separate; no redraw or task-completion inference.' }) }
          : callbacks;
        await presentRelayResponse(saved.reply, selectedCallbacks);
        await event('presentation_callbacks_completed', { attempt, reply_sha256: saved.reply_sha256, ...extra });
        completedPresentations.set(attempt, saved.reply_sha256);
        if (reuseImages) {
          if (delivery.mode === 'full') imageBase = null;
          lastPresentation = { attempt, reply_sha256: saved.reply_sha256, picture, delivery };
        }
      } catch (error) { return failed(error); }
      finally { busy = null; }
    }
  return {
    send(tool, args = {}, attribution = null) { return send(tool, args, null, attribution); },
    sendPresented(tool, args, callbacks, attribution = null) {
      const sinks = { text: callbacks?.text, image: callbacks?.image };
      if (typeof sinks.text !== 'function' || typeof sinks.image !== 'function') {
        throw new TypeError('text and image callbacks required before dispatch');
      }
      const attributionSnapshot = snapshotAttribution(attribution);
      begin('send_presented');
      const token = Symbol('send_presented');
      busy = null; reservation = token;
      const combined = (async () => {
        try {
          const reply = await send(tool, args, token, attributionSnapshot);
          await present(reply.attempt, sinks, {}, token);
          return reply;
        } finally { reservation = null; }
      })();
      pending = combined;
      pending.catch(() => {});
      return pending;
    },
    wait() {
      if (!pending) throw new Error('no request to reconcile');
      return pending;
    },
    present(attempt, callbacks, options) { return present(attempt, callbacks, options); },
    async acknowledgeText(attempt, { task, phase, reason } = {}) {
      if (![task, phase, reason].every(value => typeof value === 'string' && value.trim())) {
        throw new TypeError('nonempty task, phase and reason required');
      }
      begin('acknowledge_text');
      try {
        const saved = await retained(attempt);
        if (completedPresentations.get(attempt) !== saved.reply_sha256) {
          throw new Error('completed presentation of the unchanged reply required');
        }
        const reply = saved.reply;
        const content = reply.result?.content;
        if (reply.status !== 'returned' || !Number.isSafeInteger(reply.id) ||
            !Array.isArray(content) || !content.length ||
            !content.every(block => block?.type === 'text' && typeof block.text === 'string')) {
          throw new Error('returned text-only content required; use image review for images');
        }
        if (Object.hasOwn(reply.result, 'isError') && typeof reply.result.isError !== 'boolean') {
          throw new TypeError('isError must be boolean when present');
        }
        const receipt = { schema: 'agent-interface/text-acknowledgment-v1',
          task, phase, reason, recorded_at: new Date().toISOString(), attempt,
          relay_id: reply.id, tool: reply.tool, reply_sha256: saved.reply_sha256,
          text_blocks: content.length,
          ...(Object.hasOwn(reply.result, 'isError') ? { isError: reply.result.isError } : {}),
          evidence_scope: 'Caller attribution to presented original text only. No image review, semantic comprehension, input authority, task success or model-latency inference.' };
        await writeFile(join(evidenceDirectory, `text-acknowledgment-${attempt}.json`),
          JSON.stringify(receipt) + '\n', { flag: 'wx' });
        await event('text_acknowledgment_recorded', { attempt, reply_sha256: saved.reply_sha256,
          relay_id: reply.id, tool: reply.tool, task, phase });
        return receipt;
      } catch (error) { return failed(error); }
      finally { busy = null; }
    },
    async review(attempt, { task, phase, reason }) {
      begin('review');
      try {
        const saved = await retained(attempt);
        const receipt = await recordRelayReview({ replyPath: saved.replyPath,
          receiptPath: join(evidenceDirectory, `review-${attempt}.json`), task, phase, reason });
        const presented = reuseImages && lastPresentation?.attempt === attempt &&
          lastPresentation.reply_sha256 === saved.reply_sha256 ? lastPresentation : null;
        await event('review_recorded', { attempt, reply_sha256: receipt.reply_sha256,
          call_id: receipt.call_id, source_sequence: receipt.source_sequence, task, phase,
          ...(reuseImages ? { image_delivery: presented?.delivery ?? null } : {}) });
        if (presented?.picture && presented.delivery.mode === 'full') {
          const reviewBytes = await readFile(join(evidenceDirectory, `review-${attempt}.json`));
          imageBase = { ...presented.picture, attempt, reply_sha256: saved.reply_sha256,
            review_sha256: createHash('sha256').update(reviewBytes).digest('hex') };
        }
        return receipt;
      } catch (error) { return failed(error); }
      finally { busy = null; }
    },
    state() { return { ...client.state(), host_busy: busy ?? (reservation ? 'send_presented' : null), host_blocked: blocked, host_closed: closed, event_sequence: sequence }; },
    async close() {
      if (busy || reservation) throw new Error('host operation outstanding; cannot close');
      if (closed) throw new Error('instrumented client already closed');
      busy = 'close';
      try {
        // Always permit transport cleanup after an instrumentation failure.
        const result = await client.close(); closed = true; imageBase = null; lastPresentation = null;
        await event('transport_closed', { code: result.code, signal: result.signal });
        return result;
      } catch (error) { return failed(error); }
      finally { busy = null; }
    },
  };
}
