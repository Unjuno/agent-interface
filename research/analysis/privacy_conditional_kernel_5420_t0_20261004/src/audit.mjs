import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const SRC = '/src';
const OUT = '/out';

function products(domains) {
  let rows = [{}];
  for (const [key, values] of Object.entries(domains)) {
    rows = rows.flatMap(row => values.map(value => Object.assign({}, row, { [key]: value })));
  }
  return rows;
}

function referenceRows(spec) {
  const rows = [];
  for (const item of spec.scenarios) {
    for (const secret of spec.neighboring_secrets) {
      const latentRows = products(item.latent_domains);
      for (const latent of latentRows) {
        let second;
        switch (item.id) {
          case 'shared_pad': second = (latent.R + secret) % 2; break;
          case 'fresh_independent_pad': second = (latent.R_prime + secret) % 2; break;
          case 'constant_output': second = 0; break;
          default: throw new Error(`unrecognized spec item ${item.id}`);
        }
        const first = latent.R;
        rows.push({ type: 'row', scenario: item.id, secret, latent,
          lineage: item.lineage, a: first, b: second,
          recipient_history_before_b: [`A=${first}`],
          recipient_history_after_b: [`A=${first}`, `B=${second}`], weight: '1' });
      }
    }
  }
  return rows;
}

function probabilityMap(rows, project) {
  const count = new Map();
  for (const row of rows) {
    const key = String(project(row));
    count.set(key, (count.get(key) || 0) + 1);
  }
  const den = rows.length;
  return Object.fromEntries(Array.from(count.entries()).sort((x, y) => x[0].localeCompare(y[0]))
    .map(([key, value]) => [key, `${value}/${den}`]));
}

function sameLaw(left, right) {
  const all = new Set([...Object.keys(left), ...Object.keys(right)]);
  for (const value of all) {
    const [ln, ld] = (left[value] || '0/1').split('/').map(Number);
    const [rn, rd] = (right[value] || '0/1').split('/').map(Number);
    if (ln * rd !== rn * ld) return false;
  }
  return true;
}

function refSummaries(spec, rows) {
  return spec.scenarios.map(item => {
    const rowsForScenario = rows.filter(row => row.scenario === item.id);
    const marginal = {};
    const conditional = {};
    for (const secret of spec.neighboring_secrets) {
      marginal[String(secret)] = probabilityMap(rowsForScenario.filter(row => row.secret === secret), row => row.b);
    }
    for (const first of [0, 1]) {
      conditional[String(first)] = {};
      for (const secret of spec.neighboring_secrets) {
        conditional[String(first)][String(secret)] = probabilityMap(
          rowsForScenario.filter(row => row.a === first && row.secret === secret), row => row.b);
      }
    }
    const marginalPass = sameLaw(marginal['0'], marginal['1']);
    const conditionalPass = [0, 1].every(first => sameLaw(conditional[String(first)]['0'], conditional[String(first)]['1']));
    return { type: 'summary', scenario: item.id, row_count: rowsForScenario.length,
      b_marginal_by_secret: marginal,
      conditional_kernel_b_given_a_and_secret: conditional,
      marginal_only_decision: marginalPass ? 'ACCEPT_ZERO_DISCLOSURE' : 'REJECT_DISCLOSURE',
      conditional_kernel_decision: conditionalPass ? 'ACCEPT_ZERO_DISCLOSURE' : 'REJECT_CONDITIONAL_DISCLOSURE',
      expected_decision: item.expected_conditional_decision };
  });
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`;
  return JSON.stringify(value);
}

export function validate(records, spec) {
  const errors = [];
  const meta = records.find(record => record.type === 'candidate_meta');
  const rows = records.filter(record => record.type === 'row');
  const summaries = records.filter(record => record.type === 'summary');
  const expectedRows = referenceRows(spec);
  const expectedSummaries = refSummaries(spec, expectedRows);
  if (!meta || meta.allocation_id !== spec.allocation_id) errors.push('allocation_identity');
  if (canonical(rows) !== canonical(expectedRows)) errors.push('raw_rows_or_lineage');
  if (canonical(summaries) !== canonical(expectedSummaries)) errors.push('summary_or_decision');
  if (meta?.row_count !== expectedRows.length || meta?.summary_count !== spec.scenarios.length) errors.push('record_counts');
  for (const item of spec.scenarios) {
    const s = expectedSummaries.find(entry => entry.scenario === item.id);
    if (s.conditional_kernel_decision !== item.expected_conditional_decision) errors.push(`gate:${item.id}`);
  }
  if (expectedSummaries.find(s => s.scenario === 'shared_pad')?.marginal_only_decision !== 'ACCEPT_ZERO_DISCLOSURE') {
    errors.push('marginal_comparator');
  }
  return errors;
}

function copyRecords(records) { return JSON.parse(JSON.stringify(records)); }

export function corruptionControls(records, spec) {
  const controls = [
    ['replace_conditional_kernel_with_product_of_marginals', raw => {
      const s = raw.find(x => x.type === 'summary' && x.scenario === 'shared_pad');
      s.conditional_kernel_b_given_a_and_secret = { '0': s.b_marginal_by_secret, '1': s.b_marginal_by_secret };
    }],
    ['erase_shared_pad_lineage', raw => {
      raw.find(x => x.type === 'row' && x.scenario === 'shared_pad').lineage.b_pad = 'UNKNOWN';
    }],
    ['flip_shared_pair_decision_to_accept', raw => {
      raw.find(x => x.type === 'summary' && x.scenario === 'shared_pad').conditional_kernel_decision = 'ACCEPT_ZERO_DISCLOSURE';
    }],
    ['remove_recipient_prior_history', raw => {
      delete raw.find(x => x.type === 'row' && x.scenario === 'shared_pad').recipient_history_before_b;
    }]
  ];
  return controls.map(([id, mutate]) => {
    const altered = copyRecords(records);
    mutate(altered);
    return { id, rejected: validate(altered, spec).length > 0 };
  });
}

async function main() {
  const rawPath = path.join(OUT, 'candidate.jsonl');
  const bytes = fs.readFileSync(rawPath);
  const lines = bytes.toString('utf8').trimEnd().split('\n');
  const records = lines.map(line => JSON.parse(line));
  const spec = JSON.parse(fs.readFileSync(path.join(SRC, 'spec.json')));
  const freezeBytes = fs.readFileSync(path.join(OUT, 'freeze.json'));
  const freeze = JSON.parse(freezeBytes);
  const errors = validate(records, spec);
  const meta = records.find(record => record.type === 'candidate_meta');
  if (meta?.freeze_sha256 !== crypto.createHash('sha256').update(freezeBytes).digest('hex')) errors.push('freeze_identity');
  const actualFiles = {};
  for (const name of fs.readdirSync(SRC).sort()) {
    const full = path.join(SRC, name);
    if (fs.statSync(full).isFile()) actualFiles[name] = crypto.createHash('sha256').update(fs.readFileSync(full)).digest('hex');
  }
  if (canonical(actualFiles) !== canonical(freeze.files_sha256)) errors.push('source_freeze');
  const mutations = corruptionControls(records, spec);
  if (!mutations.every(item => item.rejected)) errors.push('mutation_controls');
  const output = { status: errors.length ? 'FAIL_AUDIT' : 'PASS_METHOD_SCOPED',
    row_count: records.filter(record => record.type === 'row').length,
    scenario_count: records.filter(record => record.type === 'summary').length,
    raw_sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
    errors, corruption_controls: mutations,
    scope: 'exact binary channel fixture; no DP guarantee for arbitrary UI or production claim' };
  fs.writeFileSync(path.join(OUT, 'audit.json'), JSON.stringify(output, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify(output) + '\n');
  if (errors.length) process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => { console.error(`AUDIT_STOP: ${error.stack ?? error}`); process.exitCode = 1; });
}
