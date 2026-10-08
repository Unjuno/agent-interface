// Experimental caller boundary for the next allocation; not runtime authority.
export function createPrimaryTrialCaller(host, route, sinks, expectations = []) {
  const controls = new Map(expectations.map(e => [e.id, structuredClone(e)]));
  if (controls.size !== expectations.length) throw Error('duplicate control id');
  const consumed = new Set();
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
    try { return JSON.parse(text); } catch { return { text }; }
  }
  return {
    state: () => ({ stopped }),
    async call(tool, args, controlId = null) {
      if (stopped && tool !== 'interface_close') throw Error('trial stopped: ' + stopped);
      if (!tools.has(tool)) {
        stop('unavailable tool ' + tool);
        throw Error(stopped); // Local rejection before host dispatch.
      }
      const expected = controlId === null ? null : controls.get(controlId);
      if (controlId !== null) {
        if (consumed.has(controlId)) { stop('control already consumed'); throw Error(stopped); }
        if (!expected || expected.tool !== tool || canonical(expected.args) !== canonical(args)) {
          stop('control request mismatch'); throw Error(stopped);
        }
        consumed.add(controlId);
      }
      let reply, meta, isError;
      try {
        reply = await host.sendPresented(tool, args, sinks);
        // Envelope extraction is inside the fail-and-latch boundary.
        meta = read(reply);
        if (meta === null || typeof meta !== 'object' || Array.isArray(meta)) {
          throw new TypeError('malformed response envelope');
        }
        isError = reply.result.isError === true;
      } catch (error) {
        stop('transport, presentation, or response-envelope failure');
        throw error;
      }
      const declaredRefusal = expected && isError && meta.status === 'refused' &&
        meta.replay_allowed === false && meta.session?.binding_revision === expected.revision &&
        meta.session?.recovery_required === false && (expected.kind === 'source'
          ? meta.input_dispatched === false && meta.error === expected.error
          : meta.result?.input_dispatched === false && !meta.result.execution &&
            meta.result.guard_checks?.length === 1 && meta.result.guard_checks[0].stage === 'before_admission' &&
            meta.result.guard_checks[0].status === 'MISSING' && meta.result.guard_checks[0].reason === expected.reason &&
            meta.result.guard_checks[0].handle === expected.alias);
      if (expected && !declaredRefusal) stop('control outcome mismatch');
      if (isError && !declaredRefusal) stop('unexpected MCP refusal');
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
      }
      // Return the original response even after latching STOP. The primary must
      // receive its text/image evidence; the next ordinary call is prohibited.
      return reply;
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
}
