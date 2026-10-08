// Experimental caller boundary for the next allocation; not runtime authority.
export function createPrimaryTrialCaller(host, route, sinks) {
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
    async call(tool, args) {
      if (stopped && tool !== 'interface_close') throw Error('trial stopped: ' + stopped);
      if (!tools.has(tool)) {
        stop('unavailable tool ' + tool);
        throw Error(stopped); // Local rejection before host dispatch.
      }
      let reply;
      try { reply = await host.sendPresented(tool, args, sinks); }
      catch (error) { stop('transport or presentation failure'); throw error; }
      const meta = read(reply);
      if (reply.result.isError) stop('unexpected MCP refusal');
      if (tool === 'interface_guarded_input' || tool === 'interface_dispatch') {
        const execution = meta.result?.execution;
        const releases = execution?.releases;
        if (meta.status !== 'completed' || !releases?.length ||
            releases.some(r => r.verified !== true || r.keys_down?.length !== 0 || r.buttons_down?.length !== 0)) {
          stop('incomplete input or unverified neutral release');
        }
      }
      // Return the original response even after latching STOP. The primary must
      // receive its text/image evidence; the next ordinary call is prohibited.
      return reply;
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
