import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const SRC = '/src';
const OUT = '/out';
const freezePath = path.join(OUT, 'freeze.json');

function assertFrozenSources(freeze) {
  const actualNames = [];
  const visit = dir => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile()) actualNames.push(path.relative(SRC, full).split(path.sep).join('/'));
    }
  };
  visit(SRC);
  if (JSON.stringify(actualNames) !== JSON.stringify(Object.keys(freeze.files_sha256).sort((a, b) => a.localeCompare(b)))) {
    throw new Error('STOP_SOURCE_SET_DRIFT');
  }
  for (const [name, expected] of Object.entries(freeze.files_sha256)) {
    const actual = crypto.createHash('sha256').update(fs.readFileSync(path.join(SRC, name))).digest('hex');
    if (actual !== expected) throw new Error(`STOP_SOURCE_DRIFT:${name}`);
  }
}

function product(domains) {
  return Object.entries(domains).reduce((rows, [name, values]) =>
    rows.flatMap(row => values.map(value => ({ ...row, [name]: value }))), [{}]);
}

function dist(rows, select) {
  const counts = new Map();
  for (const row of rows) {
    const value = String(select(row));
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  const n = rows.length;
  return Object.fromEntries([...counts].sort(([a], [b]) => a.localeCompare(b))
    .map(([v, count]) => [v, `${count}/${n}`]));
}

function equalDist(a, b) {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  const parse = x => x.split('/').map(Number);
  for (const key of keys) {
    const [an, ad] = parse(a[key] ?? '0/1');
    const [bn, bd] = parse(b[key] ?? '0/1');
    if (an * bd !== bn * ad) return false;
  }
  return true;
}

function enumerate(spec) {
  const rows = [];
  for (const scenario of spec.scenarios) {
    for (const secret of spec.neighboring_secrets) {
      for (const latent of product(scenario.latent_domains)) {
        let a = latent.R;
        let b;
        if (scenario.id === 'shared_pad') b = latent.R ^ secret;
        else if (scenario.id === 'fresh_independent_pad') b = latent.R_prime ^ secret;
        else if (scenario.id === 'constant_output') b = 0;
        else throw new Error(`UNKNOWN_SCENARIO:${scenario.id}`);
        rows.push({
          type: 'row', scenario: scenario.id, secret, latent,
          lineage: scenario.lineage, a, b,
          recipient_history_before_b: [`A=${a}`],
          recipient_history_after_b: [`A=${a}`, `B=${b}`],
          weight: '1'
        });
      }
    }
  }
  return rows;
}

function summarize(spec, rows) {
  return spec.scenarios.map(scenario => {
    const group = rows.filter(row => row.scenario === scenario.id);
    const bMarginal = Object.fromEntries(spec.neighboring_secrets.map(secret => [
      String(secret), dist(group.filter(row => row.secret === secret), row => row.b)
    ]));
    const conditionalKernel = {};
    for (const a of [0, 1]) {
      conditionalKernel[String(a)] = Object.fromEntries(spec.neighboring_secrets.map(secret => [
        String(secret), dist(group.filter(row => row.a === a && row.secret === secret), row => row.b)
      ]));
    }
    const marginalOnlyAccept = equalDist(bMarginal['0'], bMarginal['1']);
    const conditionalAccept = [0, 1].every(a =>
      equalDist(conditionalKernel[String(a)]['0'], conditionalKernel[String(a)]['1']));
    return {
      type: 'summary', scenario: scenario.id, row_count: group.length,
      b_marginal_by_secret: bMarginal,
      conditional_kernel_b_given_a_and_secret: conditionalKernel,
      marginal_only_decision: marginalOnlyAccept ? 'ACCEPT_ZERO_DISCLOSURE' : 'REJECT_DISCLOSURE',
      conditional_kernel_decision: conditionalAccept ? 'ACCEPT_ZERO_DISCLOSURE' : 'REJECT_CONDITIONAL_DISCLOSURE',
      expected_decision: scenario.expected_conditional_decision
    };
  });
}

export function evaluate(spec) {
  const rows = enumerate(spec);
  return { rows, summaries: summarize(spec, rows) };
}

async function main() {
  if (!fs.existsSync(freezePath)) throw new Error('STOP_NO_FREEZE');
  if (fs.readdirSync(OUT).some(name => name !== 'freeze.json')) throw new Error('STOP_OUTPUT_NOT_EMPTY');
  const freezeBytes = fs.readFileSync(freezePath);
  const freeze = JSON.parse(freezeBytes);
  assertFrozenSources(freeze);
  const spec = JSON.parse(fs.readFileSync(path.join(SRC, 'spec.json')));
  const { rows, summaries } = evaluate(spec);
  const records = [
    { type: 'candidate_meta', allocation_id: spec.allocation_id,
      freeze_sha256: crypto.createHash('sha256').update(freezeBytes).digest('hex'),
      row_count: rows.length, summary_count: summaries.length },
    ...rows, ...summaries
  ];
  fs.writeFileSync(path.join(OUT, 'candidate.jsonl'), records.map(x => JSON.stringify(x)).join('\n') + '\n', { flag: 'wx' });
  process.stdout.write(JSON.stringify({ status: 'CANDIDATE_EXIT_0', rows: rows.length, summaries: summaries.length }) + '\n');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => { console.error(`CANDIDATE_STOP: ${error.stack ?? error}`); process.exitCode = 1; });
}
