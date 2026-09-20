// Post-run independent bytewise cross-check; does not import runner/reducer.
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
const bundle = JSON.parse(fs.readFileSync(path.join(root, 'rows.json'), 'utf8'));
const mismatches = [];
for (const row of bundle.rows) {
  const before = fs.readFileSync(path.join(root, 'frames', row.frame_paths[0]));
  const after = fs.readFileSync(path.join(root, 'frames', row.frame_paths[1]));
  const changed = !before.equals(after);
  const expectedEffect = row.task_effect_count > 0;
  if (changed !== expectedEffect) mismatches.push({case: row.case, policy: row.policy, changed, expectedEffect});
}
if (bundle.rows.length !== 32 || mismatches.length) throw new Error(JSON.stringify(mismatches));
process.stdout.write(JSON.stringify({audit: 'PASS', rows: bundle.rows.length, bytewise_frame_pairs: 32, effect_mismatches: 0}) + '\n');
