// Construction-only fail-closed successor; not production runtime authority.
export function createPrimaryTrialCaller(host, route, sinks) {
  const tools = new Set(['interface_clock', 'interface_close', 'interface_results',
    'interface_validate', ...(route === 'guarded-local'
      ? ['interface_guarded_observe', 'interface_guarded_mint', 'interface_guarded_mint_many',
        'interface_guarded_input', 'interface_guarded_review_window']
      : ['interface_observe', 'interface_dispatch'])]);
  let stopped = null;
  function stop(reason) { stopped ??= reason; }
  function read(reply) {
    if (!reply || typeof reply !== 'object' || !reply.result ||
        typeof reply.result !== 'object' || typeof reply.result.isError !== 'boolean' ||
        !Array.isArray(reply.result.content)) {
      throw TypeError('malformed MCP response envelope');
    }
    const text = reply.result.content.find(c => c?.type === 'text')?.text;
    if (typeof text !== 'string') throw TypeError('response lacks textual receipt');
    if (reply.result.isError) return {text};
    try { return JSON.parse(text); } catch { return {text}; }
  }
  return {
    state: () => ({stopped}),
    async call(tool, args) {
      if (stopped && tool !== 'interface_close') throw Error('trial stopped: ' + stopped);
      if (!tools.has(tool)) {
        stop('unavailable tool ' + tool);
        throw Error(stopped);
      }
      let reply, meta;
      try {
        reply = await host.sendPresented(tool, args, sinks);
        meta = read(reply);
      } catch (error) {
        stop('transport, presentation, or response validation failure');
        throw error;
      }
      if (reply.result.isError) stop('unexpected MCP refusal');
      if (tool === 'interface_guarded_input' || tool === 'interface_dispatch') {
        const releases = meta.result?.execution?.releases;
        if (meta.status !== 'completed' || !releases?.length ||
            releases.some(r => r.verified !== true || r.keys_down?.length !== 0 || r.buttons_down?.length !== 0)) {
          stop('incomplete input or unverified neutral release');
        }
      }
      return reply;
    },
    async review(attempt, review) {
      if (!Number.isSafeInteger(attempt) || attempt < 1 ||
          !['task', 'phase', 'reason'].every(k => typeof review?.[k] === 'string' && review[k].trim())) {
        stop('invalid primary review arguments');
        throw TypeError(stopped);
      }
      try { return await host.review(attempt, review); }
      catch (error) { stop('review recording failure'); throw error; }
    }
  };
}
