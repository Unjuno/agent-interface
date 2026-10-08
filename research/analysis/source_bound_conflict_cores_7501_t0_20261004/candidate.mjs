import fs from 'node:fs';

function assignments(vars) {
  return Array.from({length: 1 << vars.length}, (_, mask) =>
    Object.fromEntries(vars.map((v, i) => [v, Boolean(mask & (1 << i))])));
}

function satisfies(clauses, value) {
  return clauses.every(c => c.literals.some(lit => lit.startsWith('!') ? !value[lit.slice(1)] : value[lit]));
}

function* choose(items, size, start = 0, prefix = []) {
  if (prefix.length === size) { yield prefix; return; }
  for (let i = start; i <= items.length - (size - prefix.length); i++) {
    yield* choose(items, size, i + 1, [...prefix, items[i]]);
  }
}

function solve(caseData) {
  const clauses = caseData.clauses;
  const row = {id: caseData.id, status: '', complete: true, dispatch_allowed: false, cores: [], work_units: 0};
  if (caseData.compiled_revision !== caseData.current_revision) {
    row.status = 'STALE_REVISION'; row.complete = false; return row;
  }
  if (clauses.some(c => c.kind === 'unknown' || !Array.isArray(c.literals))) {
    row.status = 'UNKNOWN'; row.complete = false; return row;
  }
  if (new Set(clauses.map(c => c.source_span)).size !== clauses.length) {
    row.status = 'INVALID_PROVENANCE'; row.complete = false; return row;
  }
  const values = assignments(caseData.vars);
  const minimal = [];
  let exhausted = false;
  for (let size = 1; size <= clauses.length && !exhausted; size++) {
    for (const subset of choose(clauses, size)) {
      if (row.work_units >= caseData.budget) { exhausted = true; break; }
      row.work_units++;
      const unsat = !values.some(value => satisfies(subset, value));
      if (unsat && !minimal.some(core => core.every(id => subset.some(c => c.id === id)))) {
        minimal.push(subset.map(c => c.id));
      }
    }
  }
  if (exhausted) {
    row.status = 'INCOMPLETE'; row.complete = false; row.cores = minimal; return row;
  }
  if (minimal.length === 0) {
    row.status = 'SAT'; row.dispatch_allowed = true; return row;
  }
  row.cores = minimal;
  row.status = minimal.some(core => core.some(id => clauses.some(c => c.id === id && c.kind === 'hard')))
    ? 'BLOCKED_BY_HARD_CONSTRAINT' : 'CONFLICT_CORE_COMPLETE';
  return row;
}

const [, , fixturePath, outputPath, stdoutPath] = process.argv;
if (!fixturePath || !outputPath || !stdoutPath) throw new Error('usage: candidate.mjs FIXTURES.json OUTPUT.json STDOUT.json');
const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
const rows = fixture.cases.map(solve);
const output = {format: 'source-bound-conflict-core-candidate-v1', rows};
fs.writeFileSync(outputPath, JSON.stringify(output) + '\n');
const statuses = Object.fromEntries([...new Set(rows.map(r => r.status))].sort().map(s => [s, rows.filter(r => r.status === s).length]));
const summary = {case_count: rows.length, statuses, node: process.version, arch: process.arch, uid: process.getuid?.() ?? null};
fs.writeFileSync(stdoutPath, JSON.stringify(summary) + '\n');
console.log(JSON.stringify(summary));
