import { createHash } from 'node:crypto';

const base = 'https://raw.githubusercontent.com/Unjuno/agent-interface/2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0/';
const paths = [
  'research/doom/results/map01-v39-coast-liveness-live-01/report.json',
  'research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl'
];
const raw = await Promise.all(paths.map(async (path) => {
  const response = await fetch(base + path);
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${path}`);
  return response.text();
}));
const report = JSON.parse(raw[0]);
const cr = String.fromCharCode(13), lf = String.fromCharCode(10);
const lines = raw[1].replaceAll(cr, '').trimEnd().split(lf);
if (lines.length !== 634) throw new Error(`expected 634 JSONL rows; got ${lines.length}`);
const records = lines.map((line) => JSON.parse(line));
const observations = records.filter((row) => row.event === 'typed_observation')
  .map((row) => ({time: row.capture_ns, sequence: row.sequence,
    status: row.signals?.health?.status, health: row.signals?.health?.value}))
  .sort((a, b) => a.time - b.time);
if (observations.length !== 218 || report.decisions.length !== 6)
  throw new Error('pinned trace count mismatch');
const windowsMs = [500, 1000, 1500, 2000, 2500, 3000, 4000];
const decisions = report.decisions.map((decision) => {
  const start = decision.controller_model_started_ns;
  const end = decision.controller_model_ended_ns;
  const before = observations.filter((row) => row.time < start &&
    row.status === 'observed' && Number.isFinite(row.health)).at(-1);
  let previous = before ? {time: before.time, health: before.health} : null;
  const inWait = observations.filter((row) => row.time >= start && row.time <= end);
  const decreases = [];
  for (const row of inWait) {
    if (row.status !== 'observed' || !Number.isFinite(row.health)) {
      previous = null;
      continue;
    }
    if (previous && row.health < previous.health)
      decreases.push({sequence: row.sequence, from: previous.health, to: row.health, time: row.time});
    previous = {time: row.time, health: row.health};
  }
  const sweep = windowsMs.map((windowMs) => {
    let trigger = null;
    for (let i = 0; i < decreases.length && !trigger; i++) {
      for (let j = i + 1; j < decreases.length; j++) {
        if (decreases[j].time - decreases[i].time <= windowMs * 1e6) {
          trigger = decreases[j];
          break;
        }
      }
    }
    return {window_ms: windowMs, trigger: trigger ? {
      sequence: trigger.sequence, from: trigger.from, to: trigger.to,
      after_start_ms: +((trigger.time - start) / 1e6).toFixed(3),
      remaining_ms: +((end - trigger.time) / 1e6).toFixed(3)
    } : null};
  });
  return {decision: decision.iteration,
    no_policy: decision.cover_policy_source_iteration === null,
    baseline_health: before?.health ?? null, typed_samples: inWait.length,
    downward_transitions: decreases.length,
    decreases: decreases.map((d) => ({sequence: d.sequence, from: d.from, to: d.to,
      after_start_ms: +((d.time - start) / 1e6).toFixed(3)})),
    sweep, actual_interrupt: decision.planner_interrupt?.outcome ?? null,
    terminal: decision.planner_turn_status};
});
const result = {
  schema: 'v39-typed-health-window-a02-v1',
  status: 'CANDIDATE_REPLAY_COMPLETE',
  source_commit: '2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0',
  source_blob_shas: {
    report: 'bff2459036dcdcc44ed100b0c0bc657e1bb8e69a',
    events: 'cbaeed9c7ba27b53cef9d10730ae33313371ad9a',
    guard: 'c0955f976e3a0af6ce926f22cee4a5ddf70ef543'
  },
  source_raw_sha256: {
    report: createHash('sha256').update(raw[0]).digest('hex'),
    events: createHash('sha256').update(raw[1]).digest('hex')
  },
  event_records: records.length,
  typed_observations: observations.length,
  windows_ms: windowsMs,
  decisions
};
process.stdout.write(JSON.stringify(result, null, 2) + '\n');
