'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {materialize} = require('./candidate');
const {audit} = require('./auditor');

const dir = __dirname;
const fixture = JSON.parse(fs.readFileSync(path.join(dir, 'fixture.json'), 'utf8'));
const episodes = materialize(fixture);
const raw = {
  schema: 'context-return-renewal-a02-raw-v1', allocation_id: fixture.allocation_id,
  counts: {total_episodes: episodes.length, matched_history_episodes: episodes.filter(e => e.history_treatment !== 'none').length, no_history_controls: episodes.filter(e => e.history_treatment === 'none').length}, episodes
};
const baseline = audit(fixture, raw);
assert.equal(baseline.status, 'PASS_METHOD_SCOPED', JSON.stringify(baseline.issues));
assert.deepEqual(baseline.counts, {total_episodes: 18, matched_history_episodes: 12, no_history_controls: 6});

const mutants = [
  value => value.episodes.pop(),
  value => { value.episodes.find(e => e.episode_id.endsWith('|context_tagged')).history[0].context_marker = 'B'; },
  value => { value.episodes.find(e => e.episode_id.endsWith('|chronological')).test.splice(0, 1); },
  value => { value.episodes.find(e => e.episode_id.startsWith('return_A|')).context_path = 'continue_B'; },
  value => { value.episodes[0].current_mapping = 'A'; },
  value => { value.counts.total_episodes = 17; }
];
for (const [index, mutate] of mutants.entries()) {
  const changed = structuredClone(raw);
  mutate(changed);
  const result = audit(fixture, changed);
  assert.equal(result.status, 'FAIL_METHOD_GATE', `mutation ${index + 1} unexpectedly accepted`);
}

// Exercise the exact candidate/auditor CLIs before freezing.
const temp = fs.mkdtempSync(path.join(os.tmpdir(), '8432-a02-construction-'));
try {
  const rawPath = path.join(temp, 'raw.json');
  const auditPath = path.join(temp, 'audit.json');
  const candidate = spawnSync(process.execPath, [path.join(dir, 'candidate.js'), path.join(dir, 'fixture.json'), rawPath], {encoding: 'utf8'});
  assert.equal(candidate.status, 0, candidate.stderr);
  const cliAudit = spawnSync(process.execPath, [path.join(dir, 'auditor.js'), path.join(dir, 'fixture.json'), rawPath, auditPath], {encoding: 'utf8'});
  assert.equal(cliAudit.status, 0, cliAudit.stderr || cliAudit.stdout);
  assert.equal(JSON.parse(fs.readFileSync(auditPath, 'utf8')).status, 'PASS_METHOD_SCOPED');
} finally {
  fs.rmSync(temp, {recursive: true, force: true});
}
console.log('construction PASS: 18/12/6, controls and 6/6 mutations rejected; formal invocations 0/0');
