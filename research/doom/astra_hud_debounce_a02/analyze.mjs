import { createHash } from 'node:crypto';

// Analyze the immutable A01 raw ROI series; this does not inspect a game.
const sourceCommit = '5e5fa2e697109dc68a605bbfcb04e523e3103698';
const sourceUrl = `https://raw.githubusercontent.com/Unjuno/agent-interface/${sourceCommit}/research/doom/astra_continuous_hud_a01/samples.csv`;
const response = await fetch(sourceUrl);
if (!response.ok) throw new Error(`raw A01 CSV fetch failed: HTTP ${response.status}`);
const csv = await response.text();
const lines = csv.trimEnd().split(/\r?\n/);
const header = lines.shift().split(',');
const col = Object.fromEntries(header.map((name, index) => [name, index]));
for (const required of ['frame_index', 'source_control_elapsed_s', 'red_mask_xor_from_previous']) {
  if (!(required in col)) throw new Error(`missing CSV column: ${required}`);
}
const rows = lines.map((line) => {
  const cells = line.split(',');
  return { frame: Number(cells[col.frame_index]), sourceSeconds: Number(cells[col.source_control_elapsed_s]), xor: Number(cells[col.red_mask_xor_from_previous]) };
});
if (rows.length !== 780 || rows.some((row, i) => row.frame !== i)) throw new Error(`expected contiguous 780 frames, got ${rows.length}`);

const cutoffSeconds = 31;
const threshold = 60;
const prefix = rows.filter((row) => row.sourceSeconds <= cutoffSeconds);
const remainder = rows.filter((row) => row.sourceSeconds > cutoffSeconds);
const events = remainder.filter((row) => row.xor > threshold);
const adjacentEvents = events.filter((row) => remainder.some((next) => next.frame === row.frame + 1 && next.xor > threshold));
const frame311 = rows.find((row) => row.frame === 311);
const result = {
  protocol: 'A02: one-frame threshold recurrence / two-frame debounce check',
  source_commit: sourceCommit,
  source_csv_sha256: createHash('sha256').update(csv).digest('hex'),
  rows: rows.length,
  threshold_changed_pixels_strictly_greater_than: threshold,
  stable_prefix_source_seconds_lte: cutoffSeconds,
  stable_prefix_frames: prefix.length,
  stable_prefix_max_xor: Math.max(...prefix.map((row) => row.xor)),
  stable_prefix_exceedances: prefix.filter((row) => row.xor > threshold).length,
  remainder_exceedances: events.length,
  remainder_two_adjacent_exceedances: adjacentEvents.length,
  frame_311_xor: frame311.xor,
  frame_311_has_adjacent_threshold_exceedance: adjacentEvents.some((row) => row.frame === 310 || row.frame === 311),
  remainder_exceedance_frames: events.map((row) => row.frame),
  interpretation: 'A two-consecutive-frame debounce suppresses every >60-pixel event in this retained trace, including frame 311. Visual-mask temporal resolution only; no event is labeled damage, threat, useful feedback, or safe action trigger.'
};
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
