import { createHash } from 'node:crypto';

const base = 'https://raw.githubusercontent.com/Unjuno/agent-interface/2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0/';
const paths = [
  'research/doom/results/map01-v39-coast-liveness-live-01/report.json',
  'research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl'
];
const [reportText, eventsText] = await Promise.all(paths.map(async (path) => {
  const response = await fetch(base + path);
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${path}`);
  return response.text();
}));
const report = JSON.parse(reportText);
const records = eventsText.replaceAll(String.fromCharCode(13), '')
  .trimEnd().split(String.fromCharCode(10)).map(JSON.parse);
const typed = records.filter((row) => row.event === 'typed_observation');
const windowsMs = [500, 1000, 1500, 2000, 2500, 3000, 4000];

// Independent formulation: enumerate every pair and sort all qualifying second
// observations, instead of short-circuiting at the first pair as candidate.mjs does.
const decisions = report.decisions.map((decision) => {
  const start = decision.controller_model_started_ns, end = decision.controller_model_ended_ns;
  const before = typed.filter((row) => row.capture_ns < start &&
    row.signals?.health?.status === 'observed' &&
    Number.isFinite(row.signals.health.value)).at(-1);
  const windowRows = typed.filter((row) => row.capture_ns >= start && row.capture_ns <= end);
  let last = before?.signals.health.value ?? null;
  const declines = [];
  for (const row of windowRows) {
    const signal = row.signals?.health;
    if (signal?.status !== 'observed' || !Number.isFinite(signal.value)) { last = null; continue; }
    if (last !== null && signal.value < last)
      declines.push({sequence: row.sequence, from: last, to: signal.value, time: row.capture_ns});
    last = signal.value;
  }
  const hits = windowsMs.map((windowMs) => {
    const qualifying = [];
    for (let i = 0; i < declines.length; i++) {
      for (let j = i + 1; j < declines.length; j++) {
        if (declines[j].time - declines[i].time <= windowMs * 1e6)
          qualifying.push(declines[j]);
      }
    }
    qualifying.sort((a, b) => a.time - b.time);
    const second = qualifying[0];
    return {window_ms: windowMs, sequence: second?.sequence ?? null,
      after_start_ms: second ? +((second.time - start) / 1e6).toFixed(3) : null,
      remaining_ms: second ? +((end - second.time) / 1e6).toFixed(3) : null};
  });
  return {decision: decision.iteration, no_policy: decision.cover_policy_source_iteration === null,
    baseline_health: before?.signals.health.value ?? null, typed_samples: windowRows.length,
    downward_transitions: declines.length, hits};
});
const sourceRawSha256 = {
  report: createHash('sha256').update(reportText).digest('hex'),
  events: createHash('sha256').update(eventsText).digest('hex')
};
process.stdout.write(JSON.stringify({audit: 'independent-all-pairs-enumeration-v2',
  source_raw_sha256: sourceRawSha256, event_records: records.length,
  typed_observations: typed.length, decisions}, null, 2) + '\n');
