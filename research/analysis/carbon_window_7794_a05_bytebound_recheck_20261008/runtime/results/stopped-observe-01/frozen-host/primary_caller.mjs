// Opt-in sequential primary caller policy; not runtime input authority.
export function createPrimaryCaller(host, route, sinks, expectations = [], options = {}) {
  const controls = new Map(expectations.map(e => [e.id, structuredClone(e)]));
  if (controls.size !== expectations.length) throw Error('duplicate control id');
  const consumed = new Set();
  const observationArguments = route === 'guarded-local' ? {} :
    structuredClone(options.observationArguments);
  const reviewWindowId = options.reviewWindowId;
  const canonical = value => JSON.stringify(value, (_key, v) => v && typeof v === 'object' && !Array.isArray(v)
    ? Object.fromEntries(Object.keys(v).sort().map(k => [k,v[k]])) : v);
  const tools = new Set(['interface_clock', 'interface_close', 'interface_results',
    'interface_validate', ...(route === 'guarded-local'
      ? ['interface_guarded_observe', 'interface_guarded_mint', 'interface_guarded_mint_many',
        'interface_guarded_input', 'interface_guarded_review_window']
      : ['interface_observe', 'interface_dispatch'])]);
  let stopped = null;
  function stop(reason) { stopped ??= reason; }
  function read(reply) {
    const text = reply.result.content.find(c => c.type === 'text')?.text;
    if (typeof text !== 'string') throw TypeError('missing response JSON text');
    const meta = JSON.parse(text);
    if (!meta || typeof meta !== 'object' || Array.isArray(meta)) {
      throw TypeError('response metadata must be an object');
    }
    return meta;
  }
  function inputArguments(values) {
    const [alias, offset, interaction, tail] = values;
    if (route !== 'guarded-local' || values.length !== 4 ||
        typeof alias !== 'string' || !alias.trim() ||
        !Array.isArray(offset) || offset.length !== 2 ||
        !Array.from(offset).every(Number.isSafeInteger) ||
        !['click', 'keyboard', 'move'].includes(interaction) || !Array.isArray(tail)) {
      stop('invalid primary input arguments');
      throw TypeError(stopped);
    }
    let copiedTail;
    try { copiedTail = structuredClone(tail); }
    catch (error) { stop('invalid primary input tail'); throw error; }
    return { alias, offset: [...offset], interaction, tail: copiedTail,
      detail: 'brief', observation_refs: true };
  }
  async function performCall(tool, args, controlId = null, stoppedObservation = false) {
      if (stopped && tool !== 'interface_close' && !(stoppedObservation && tool === 'interface_guarded_observe')) throw Error('trial stopped: ' + stopped);
      if (!tools.has(tool)) {
        stop('unavailable tool ' + tool);
        throw Error(stopped); // Local rejection before host dispatch.
      }
      if (tool === 'interface_guarded_input' && args?.interaction !== undefined &&
          !['click', 'keyboard', 'move'].includes(args.interaction)) {
        stop('invalid guarded interaction');
        throw TypeError(stopped); // Match the public MCP enum before dispatch.
      }
      const expected = controlId === null ? null : controls.get(controlId);
      if (controlId !== null) {
        if (consumed.has(controlId)) { stop('control already consumed'); throw Error(stopped); }
        if (!expected || expected.tool !== tool || canonical(expected.args) !== canonical(args)) {
          stop('control request mismatch'); throw Error(stopped);
        }
        consumed.add(controlId);
      }
      let reply;
      try { reply = await host.sendPresented(tool, args, sinks); }
      catch (error) { stop('transport or presentation failure'); throw error; }
      try {
        if (reply.result.isError === true && !expected) {
          stop('unexpected MCP refusal');
          return reply; // Framework errors may contain free text, not typed JSON.
        }
        const meta = read(reply);
        const declaredRefusal = expected && reply.result.isError === true && meta.status === 'refused' &&
          meta.replay_allowed === false && meta.session?.binding_revision === expected.revision &&
          meta.session?.recovery_required === false && (expected.kind === 'source'
            ? meta.input_dispatched === false && meta.error === expected.error
            : meta.result?.input_dispatched === false && !meta.result.execution &&
              meta.result.guard_checks?.length === 1 && meta.result.guard_checks[0].stage === 'before_admission' &&
              meta.result.guard_checks[0].status === 'MISSING' && meta.result.guard_checks[0].reason === expected.reason &&
              meta.result.guard_checks[0].handle === expected.alias);
        if (expected && !declaredRefusal) stop('control outcome mismatch');
        if (reply.result.isError && !declaredRefusal) stop('unexpected MCP refusal');
        if (!declaredRefusal && tool === 'interface_guarded_mint_many') {
          // Registration can partially mutate the server store. Keep its original
          // response, but never continue input or retry an uncertain batch.
          if (meta.status !== 'minted' || meta.source_sequence !== args?.source_sequence ||
              !Array.isArray(args?.references) || !Array.isArray(meta.minted) ||
              meta.minted.length !== args.references.length ||
              meta.minted.some((reference, index) => reference?.alias !== args.references[index]?.alias)) {
            stop('incomplete or inconsistent batch mint result');
          }
        }
        if (!declaredRefusal && (tool === 'interface_guarded_input' || tool === 'interface_dispatch')) {
          const summary = tool === 'interface_dispatch' && meta.schema === 'agent-interface/review-v1' &&
            meta.receipt?.schema === 'agent-interface/receipt-view-dispatch-summary-v1';
          const execution = summary ? meta.receipt.execution_summary : meta.result?.execution;
          const releases = execution?.releases;
          const completed = summary ? meta.outcome_summary?.execution_status === 'completed' &&
            meta.outcome_summary.input_release_verified === true && meta.outcome_summary.recovery_required === false &&
            meta.outcome_summary.error === null : meta.status === 'completed';
          if (!completed || meta.image_status !== 'image' || !releases?.length ||
              releases.some(r => r.verified !== true || r.keys_down?.length !== 0 || r.buttons_down?.length !== 0)) {
            stop('incomplete input or unverified neutral release');
          }
          if (tool === 'interface_guarded_input' && args?.feedback !== undefined) {
            const cue = meta.feedback;
            if (cue?.status !== 'matched' || cue.expected_title !== args.feedback.expected_title ||
                canonical(cue.rejected_titles) !== canonical(args.feedback.rejected_titles ?? []) ||
                cue.title !== cue.expected_title || cue.after_title !== cue.title ||
                cue.task_success !== null || cue.authority_granted !== false || cue.input_dispatched !== false) {
              stop('missing or inconsistent requested feedback');
            }
          }
        }
        // Return the original response even after latching STOP. The primary must
        // receive its text/image evidence; the next ordinary call is prohibited.
        return reply;
      } catch (error) {
        // sendPresented already delivered the original evidence. Extraction or
        // outcome validation must fail closed before the primary can catch it.
        stop('response extraction or validation failure');
        throw error;
      }
  }
  const caller = {
    state: () => ({ stopped }),
    async input(...values) {
      return caller.call('interface_guarded_input', inputArguments(values));
    },
    async inputWithFeedback(...values) {
      let policy;
      try { policy = structuredClone(values[4]); }
      catch (error) { stop('invalid primary feedback policy'); throw error; }
      if (values.length !== 5 || !policy || typeof policy !== 'object' || Array.isArray(policy) ||
          Object.keys(policy).some(key => !['expected_title','rejected_titles','timeout_ms'].includes(key)) ||
          typeof policy.expected_title !== 'string' || policy.expected_title.length === 0 ||
          (policy.rejected_titles !== undefined && (!Array.isArray(policy.rejected_titles) ||
            !Array.from(policy.rejected_titles).every(title => typeof title === 'string' && title.length && title !== policy.expected_title))) ||
          (policy.timeout_ms !== undefined && (!Number.isSafeInteger(policy.timeout_ms) || policy.timeout_ms < 0 || policy.timeout_ms > 10000))) {
        stop('invalid primary feedback policy');
        throw TypeError(stopped);
      }
      const args = inputArguments(values.slice(0,4));
      args.feedback = { expected_title: policy.expected_title,
        rejected_titles: [...(policy.rejected_titles ?? [])], timeout_ms: policy.timeout_ms ?? 2000 };
      return caller.call('interface_guarded_input', args);
    },
    async reviewWindow(...unexpected) {
      if (route !== 'guarded-local' || unexpected.length ||
          !Number.isSafeInteger(reviewWindowId) || reviewWindowId < 1) {
        stop('invalid primary window review configuration or arguments');
        throw TypeError(stopped);
      }
      return caller.call('interface_guarded_review_window', { window_id: reviewWindowId });
    },
    async mint(...values) {
      const [alias, sourceSequence, point, regionSize] = values;
      const pair = value => Array.isArray(value) && value.length === 2 &&
        value.every(Number.isSafeInteger);
      if (route !== 'guarded-local' || values.length !== 4 ||
          typeof alias !== 'string' || !alias.trim() ||
          !Number.isSafeInteger(sourceSequence) || sourceSequence < 1 ||
          !pair(point) || !pair(regionSize) || regionSize.some(v => v < 4 || v > 96)) {
        stop('invalid primary mint arguments');
        throw TypeError(stopped);
      }
      return caller.call('interface_guarded_mint', {
        alias, source_sequence: sourceSequence,
        point: [...point], region_size: [...regionSize]
      });
    },
    async mintMany(...values) {
      const [sourceSequence, references] = values;
      const pair = value => Array.isArray(value) && value.length === 2 &&
        Array.from(value).every(Number.isSafeInteger);
      const validReference = reference => reference && typeof reference === 'object' &&
        !Array.isArray(reference) &&
        Object.keys(reference).sort().join(',') === 'alias,point,region_size' &&
        typeof reference.alias === 'string' && /^[a-z][a-z0-9_]{0,31}$/.test(reference.alias) &&
        pair(reference.point) && pair(reference.region_size) &&
        reference.region_size.every(value => value >= 4 && value <= 96);
      if (route !== 'guarded-local' || values.length !== 2 ||
          !Number.isSafeInteger(sourceSequence) || sourceSequence < 1 ||
          !Array.isArray(references) || references.length < 1 || references.length > 8 ||
          !Array.from(references).every(validReference) ||
          new Set(references.map(reference => reference.alias)).size !== references.length) {
        stop('invalid primary batch mint arguments');
        throw TypeError(stopped);
      }
      return caller.call('interface_guarded_mint_many', {
        source_sequence: sourceSequence, references: structuredClone(references)
      });
    },
    async observe(...unexpected) {
      if (unexpected.length || !observationArguments ||
          typeof observationArguments !== 'object' || Array.isArray(observationArguments)) {
        stop('invalid primary observation arguments');
        throw TypeError(stopped);
      }
      return caller.call(route === 'guarded-local' ? 'interface_guarded_observe' :
        'interface_observe', structuredClone(observationArguments));
    },
    async call(tool, args, controlId = null) {
      return performCall(tool, args, controlId);
    },
    async observeAfterStop(...unexpected) {
      if (route !== 'guarded-local' || !stopped || unexpected.length) {
        stop('explicit stopped guarded observation requires no arguments');
        throw TypeError('explicit stopped guarded observation requires no arguments');
      }
      // One explicit read only. STOP remains sticky; no action, review-window,
      // remint, recovery or ordinary call is implicitly enabled by this image.
      return performCall('interface_guarded_observe', {}, null, true);
    },
    async acknowledgeText(attempt, attribution) {
      if (!Number.isSafeInteger(attempt) || attempt < 1 ||
          !['task', 'phase', 'reason'].every(k => typeof attribution?.[k] === 'string' && attribution[k].trim())) {
        stop('invalid primary acknowledgment arguments');
        throw TypeError(stopped);
      }
      try { return await host.acknowledgeText(attempt, attribution); }
      catch (error) { stop('text acknowledgment recording failure'); throw error; }
    },
    async review(attempt, review) {
      if (!Number.isSafeInteger(attempt) || attempt < 1 ||
          !['task', 'phase', 'reason'].every(k => typeof review?.[k] === 'string' && review[k].trim())) {
        stop('invalid primary review arguments');
        throw TypeError(stopped); // Do not poison the underlying evidence host.
      }
      try { return await host.review(attempt, review); }
      catch (error) { stop('review recording failure'); throw error; }
    }
  };
  return caller;
}
