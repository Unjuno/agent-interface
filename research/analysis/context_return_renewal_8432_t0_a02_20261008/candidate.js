#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

function materialize(fixture) {
  const episodes = [];
  for (const context of fixture.context_paths) {
    for (const cue of fixture.cue_variants) {
      for (const treatment of fixture.history_treatments) {
        const history = treatment === 'none' ? [] : fixture.demonstration_phases.flatMap(phase =>
          fixture.demonstration_records_per_phase.map((record, index) => ({
            episode_id: `${context.id}|${cue}|${treatment}`,
            treatment,
            phase: phase.phase,
            phase_order: fixture.demonstration_phases.indexOf(phase),
            record_order: index,
            cue_id: record.cue_id,
            action: record.action,
            outcome: fixture.mapping_outcomes[phase.mapping_id][record.action],
            context_marker: treatment === 'context_tagged' ? phase.context_marker : null,
            source_id: `${phase.phase}:${record.cue_id}:${record.action}`
          }))
        );
        episodes.push({
          episode_id: `${context.id}|${cue}|${treatment}`,
          context_path: context.id,
          test_phase: context.test_phase,
          cue_id: cue,
          history_treatment: treatment,
          current_mapping: 'B',
          history,
          test: [fixture.baseline_test_phase, context].flatMap(testPhase =>
            Array.from({length: fixture.test_trials}, (_, trial) => ({
              phase: testPhase.phase,
              context_marker: testPhase.context_marker,
              trial_order: trial,
              cue_id: cue,
              available_actions: [...fixture.action_support],
              outcome_by_action: {...fixture.mapping_outcomes.B}
            }))
          )
        });
      }
    }
  }
  return episodes;
}

function main() {
  const [fixturePath, outputPath] = process.argv.slice(2);
  if (!fixturePath || !outputPath) throw new Error('usage: candidate.js FIXTURE OUTPUT');
  const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
  const episodes = materialize(fixture);
  const raw = {
    schema: 'context-return-renewal-a02-raw-v1',
    allocation_id: fixture.allocation_id,
    counts: {
      total_episodes: episodes.length,
      matched_history_episodes: episodes.filter(e => e.history_treatment !== 'none').length,
      no_history_controls: episodes.filter(e => e.history_treatment === 'none').length
    },
    episodes
  };
  fs.writeFileSync(outputPath, `${JSON.stringify(raw, null, 2)}\n`, {flag: 'wx'});
  process.stdout.write(`${JSON.stringify({allocation_id: raw.allocation_id, episode_count: episodes.length, output: path.basename(outputPath)})}\n`);
}

if (require.main === module) main();
module.exports = {materialize};
