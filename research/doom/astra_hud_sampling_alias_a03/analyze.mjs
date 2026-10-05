import { createHash } from 'node:crypto';

const sourceCommit = '5e5fa2e697109dc68a605bbfcb04e523e3103698';
const sourceUrl = `https://raw.githubusercontent.com/Unjuno/agent-interface/${sourceCommit}/research/doom/astra_continuous_hud_a01/samples.csv`;
const response = await fetch(sourceUrl);
if (!response.ok) throw new Error(`raw A01 CSV fetch failed: HTTP ${response.status}`);
const csv = await response.text();
const lines = csv.trimEnd().split(/\r?\n/);
const header = lines.shift().split(',');
const col = Object.fromEntries(header.map((name, index) => [name, index]));
const required = ['frame_index', 'source_control_elapsed_s', 'red_mask_xor_from_previous'];
for (const name of required) if (!(name in col)) throw new Error(`missing CSV column: ${name}`);
const rows = lines.map((line) => {
  const cells = line.split(',');
  return { frame: Number(cells[col.frame_index]), seconds: Number(cells[col.source_control_elapsed_s]), xor: Number(cells[col.red_mask_xor_from_previous]) };
});
if (rows.length !== 780 || rows.some((row, i) => row.frame !== i)) throw new Error('expected 780 contiguous frames');
const originalStep = rows[1].seconds - rows[0].seconds;
if (originalStep !== 0.2) throw new Error(`expected original 5 Hz cadence, got step ${originalStep}`);
const events = rows.filter((row) => row.seconds > 31 && row.xor > 60);
const sweep = (stride) => Array.from({ length: stride }, (_, phase) => {
  const observed = events.filter((event) => event.frame % stride === phase);
  return { phase, observed: observed.length, missed: events.length - observed.length, frames: observed.map((event) => event.frame) };
});
const result = {
  protocol: 'A03: phase-swept periodic downsampling of A01 visual-mask excursions',
  source_commit: sourceCommit,
  source_csv_sha256: createHash('sha256').update(csv).digest('hex'),
  rows: rows.length,
  source_sample_interval_seconds: originalStep,
  source_rate_hz: 1 / originalStep,
  event_definition: 'source_control_elapsed_s > 31 and red_mask_xor_from_previous > 60',
  event_count: events.length,
  stride_2_interval_seconds: 0.4,
  stride_2_phases: sweep(2),
  stride_4_interval_seconds: 0.8,
  stride_4_phases: sweep(4),
  interpretation: 'Visual-mask threshold samples only; phase affects how many are observed. No semantic, causal, usefulness, safety, or task-effect inference.'
};
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
