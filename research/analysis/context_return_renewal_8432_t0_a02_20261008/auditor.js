#!/usr/bin/env node
'use strict';

const fs = require('node:fs');

function assert(ok, message) { if (!ok) throw new Error(message); }
function equal(a, b) { return JSON.stringify(a) === JSON.stringify(b); }

function audit(fixture, raw) {
  const issues = [];
  const check = (condition, message) => { if (!condition) issues.push(message); };
  const expected = [];
  for (const context of fixture.context_paths) for (const cue of fixture.cue_variants) for (const treatment of fixture.history_treatments) {
    expected.push({context, cue, treatment, id: `${context.id}|${cue}|${treatment}`});
  }
  check(raw.schema === 'context-return-renewal-a02-raw-v1', 'raw schema');
  check(raw.allocation_id === fixture.allocation_id, 'allocation identity');
  check(Array.isArray(raw.episodes) && raw.episodes.length === expected.length, 'episode denominator');
  const byId = new Map((raw.episodes || []).map(e => [e.episode_id, e]));
  check(byId.size === expected.length, 'unique episode IDs');
  const expectedActions = fixture.demonstration_records_per_phase.map(r => `${r.cue_id}:${r.action}`).sort();
  const tags = [];
  for (const item of expected) {
    const e = byId.get(item.id);
    check(!!e, `missing ${item.id}`);
    if (!e) continue;
    check(e.context_path === item.context.id && e.test_phase === item.context.test_phase && e.cue_id === item.cue, `context/cue identity ${item.id}`);
    check(e.history_treatment === item.treatment, `treatment identity ${item.id}`);
    check(e.current_mapping === 'B', `current mapping ${item.id}`);
    const hasHistory = item.treatment !== 'none';
    check(Array.isArray(e.history) && e.history.length === (hasHistory ? 8 : 0), `history support ${item.id}`);
    if (hasHistory && Array.isArray(e.history)) {
      const phaseOrder = e.history.map(row => row.phase_order);
      check(phaseOrder.length === 8 && phaseOrder.every((v, i) => Number.isInteger(v) && v === Math.floor(i / 4)), `phase order ${item.id}`);
      for (const phase of fixture.demonstration_phases) {
        const rows = e.history.filter(row => row.phase === phase.phase);
        check(rows.length === 4, `phase record count ${item.id}/${phase.phase}`);
        check(equal(rows.map(r => `${r.cue_id}:${r.action}`).sort(), expectedActions), `cue/action support ${item.id}/${phase.phase}`);
        check(rows.every(r => r.outcome === fixture.mapping_outcomes[phase.mapping_id][r.action]), `mapping outcome ${item.id}/${phase.phase}`);
        check(rows.every((r, i) => r.record_order === i), `record order ${item.id}/${phase.phase}`);
        check(rows.every(r => item.treatment === 'context_tagged' ? r.context_marker === phase.context_marker : r.context_marker === null), `history tagging ${item.id}/${phase.phase}`);
      }
      check(new Set(e.history.map(r => r.source_id)).size === 8, `source identity ${item.id}`);
    }
    check(Array.isArray(e.test) && e.test.length === fixture.test_trials * 2, `test trial count ${item.id}`);
    if (Array.isArray(e.test)) {
      const expectedPhases = [fixture.baseline_test_phase, item.context];
      for (const [phaseIndex, phase] of expectedPhases.entries()) {
        const phaseRows = e.test.slice(phaseIndex * fixture.test_trials, (phaseIndex + 1) * fixture.test_trials);
        check(phaseRows.length === fixture.test_trials && phaseRows.every((t, i) => t.phase === phase.phase && t.context_marker === phase.context_marker && t.trial_order === i && t.cue_id === item.cue), `test identity/order ${item.id}/${phase.phase}`);
      }
      check(e.test.every(t => equal(t.available_actions, fixture.action_support) && equal(t.outcome_by_action, fixture.mapping_outcomes.B)), `test support/outcome ${item.id}`);
    }
    tags.push({id: item.id, hasHistory});
  }
  const counts = {
    total_episodes: expected.length,
    matched_history_episodes: tags.filter(x => x.hasHistory).length,
    no_history_controls: tags.filter(x => !x.hasHistory).length
  };
  check(equal(counts, fixture.expected_counts), 'fixture expected counts');
  check(equal(raw.counts, counts), 'raw count summary');

  const diagnostics = fixture.diagnostics;
  const noSignal = Object.values(diagnostics.no_signal);
  const score = trace => trace.reduce((sum, action) => sum + diagnostics.outcomes[action], 0) / trace.length;
  check(new Set(noSignal.map(score)).size === 1, 'no-signal scorer context equality');
  const seeded = diagnostics.seeded_control;
  const recurrence = trace => trace.filter((action, i) => i > 0 && action === trace[i - 1]).length;
  const regret = trace => trace.reduce((sum, action) => sum + 1 - diagnostics.outcomes[action], 0);
  check(recurrence(seeded.return_A) > recurrence(seeded.continue_B) && recurrence(seeded.return_A) > recurrence(seeded.novel_C), 'seeded recurrence contrast');
  check(regret(seeded.return_A) > regret(seeded.continue_B) && regret(seeded.return_A) > regret(seeded.novel_C), 'seeded regret contrast');

  return {status: issues.length ? 'FAIL_METHOD_GATE' : 'PASS_METHOD_SCOPED', counts, diagnostics: {no_signal_scores: noSignal.map(score), seeded_recurrence: Object.fromEntries(Object.entries(seeded).map(([k,v])=>[k, recurrence(v)])), seeded_regret: Object.fromEntries(Object.entries(seeded).map(([k,v])=>[k, regret(v)]))}, issues};
}

function main() {
  const [fixturePath, rawPath, outputPath] = process.argv.slice(2);
  if (!fixturePath || !rawPath || !outputPath) throw new Error('usage: auditor.js FIXTURE RAW OUTPUT');
  const result = audit(JSON.parse(fs.readFileSync(fixturePath, 'utf8')), JSON.parse(fs.readFileSync(rawPath, 'utf8')));
  fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, {flag: 'wx'});
  process.stdout.write(`${JSON.stringify(result)}\n`);
  if (result.status !== 'PASS_METHOD_SCOPED') process.exitCode = 1;
}

if (require.main === module) main();
module.exports = {audit};
