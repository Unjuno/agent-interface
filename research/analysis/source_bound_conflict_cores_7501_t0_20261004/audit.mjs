import fs from 'node:fs';

function allAssignments(vars) {
  const result = [];
  for (let n = 0; n < 2 ** vars.length; n++) {
    const assignment = {};
    vars.forEach((v, i) => { assignment[v] = Math.floor(n / (2 ** i)) % 2 === 1; });
    result.push(assignment);
  }
  return result;
}

function formulaHolds(clauses, valuation) {
  for (const clause of clauses) {
    let clauseHolds = false;
    for (const literal of clause.literals) {
      const positive = literal[0] !== '!';
      const variable = positive ? literal : literal.slice(1);
      if (valuation[variable] === positive) { clauseHolds = true; break; }
    }
    if (!clauseHolds) return false;
  }
  return true;
}

function reference(caseData) {
  const clauses = caseData.clauses;
  if (caseData.compiled_revision !== caseData.current_revision) return {status: 'STALE_REVISION', cores: [], dispatch: false, complete: false, work: 0};
  if (clauses.some(c => c.kind === 'unknown' || !Array.isArray(c.literals))) return {status: 'UNKNOWN', cores: [], dispatch: false, complete: false, work: 0};
  if (new Set(clauses.map(c => c.source_span)).size !== clauses.length) return {status: 'INVALID_PROVENANCE', cores: [], dispatch: false, complete: false, work: 0};

  const valuations = allAssignments(caseData.vars);
  const unsatisfiable = [];
  let work = 0;
  // Independent ordering: inspect every bit-mask subset, then reduce by set inclusion.
  for (let mask = 1; mask < 2 ** clauses.length; mask++) {
    const subset = clauses.filter((_, index) => Math.floor(mask / (2 ** index)) % 2 === 1);
    work++;
    if (!valuations.some(v => formulaHolds(subset, v))) unsatisfiable.push(subset.map(c => c.id));
  }
  const minima = unsatisfiable.filter(core => !unsatisfiable.some(other =>
    other.length < core.length && other.every(id => core.includes(id))));
  minima.sort((a, b) => a.length - b.length || a.join('\0').localeCompare(b.join('\0')));
  if (work > caseData.budget) return {status: 'INCOMPLETE', cores: [], dispatch: false, complete: false, work: Math.min(work, caseData.budget)};
  if (minima.length === 0) return {status: 'SAT', cores: [], dispatch: true, complete: true, work};
  const touchesHard = minima.some(core => core.some(id => clauses.some(c => c.id === id && c.kind === 'hard')));
  return {status: touchesHard ? 'BLOCKED_BY_HARD_CONSTRAINT' : 'CONFLICT_CORE_COMPLETE', cores: minima, dispatch: false, complete: true, work};
}

function validate(fixture, candidate) {
  if (candidate.format !== 'source-bound-conflict-core-candidate-v1' || !Array.isArray(candidate.rows)) return false;
  if (candidate.rows.length !== fixture.cases.length) return false;
  const ids = candidate.rows.map(r => r.id);
  if (new Set(ids).size !== ids.length) return false;
  const allowed = ['complete', 'cores', 'dispatch_allowed', 'id', 'status', 'work_units'];
  for (const caseData of fixture.cases) {
    const row = candidate.rows.find(r => r.id === caseData.id);
    if (!row || Object.keys(row).sort().join('|') !== allowed.join('|')) return false;
    const expected = reference(caseData);
    if (row.status !== expected.status || JSON.stringify(row.cores) !== JSON.stringify(expected.cores)) return false;
    if (row.dispatch_allowed !== expected.dispatch || row.complete !== expected.complete || row.work_units !== expected.work) return false;
    if (row.status !== 'SAT' && row.dispatch_allowed) return false;
    for (const core of row.cores) {
      const selected = caseData.clauses.filter(c => core.includes(c.id));
      if (selected.length !== core.length || allAssignments(caseData.vars).some(v => formulaHolds(selected, v))) return false;
      for (const id of core) {
        const reduced = selected.filter(c => c.id !== id);
        if (!allAssignments(caseData.vars).some(v => formulaHolds(reduced, v))) return false;
      }
    }
  }
  return true;
}

function mutationTests(fixture, candidate) {
  const outcomes = {};
  const mutate = (name, fn) => { const changed = structuredClone(candidate); fn(changed.rows); outcomes[name] = !validate(fixture, changed); };
  const row = (rows, id) => rows.find(r => r.id === id);
  mutate('drop_core_member', rs => row(rs, 'pairwise_conflict').cores[0].pop());
  mutate('include_irrelevant_member', rs => row(rs, 'overlapping_muses_with_irrelevant_clause').cores[0].push('u4'));
  mutate('omit_second_mus', rs => row(rs, 'overlapping_muses_with_irrelevant_clause').cores.pop());
  mutate('promote_unknown', rs => Object.assign(row(rs, 'unknown_unparseable_clause'), {status: 'CONFLICT_CORE_COMPLETE', complete: true}));
  mutate('claim_incomplete_complete', rs => Object.assign(row(rs, 'bounded_search_timeout'), {status: 'SAT', complete: true, dispatch_allowed: true}));
  mutate('offer_hard_clause_for_relaxation', rs => row(rs, 'hard_authority_conflict').relaxation_offer = ['h1']);
  mutate('reuse_stale_revision', rs => Object.assign(row(rs, 'stale_compiled_revision'), {status: 'SAT', complete: true, dispatch_allowed: true}));
  mutate('dispatch_after_unsat_or_unknown', rs => rs.filter(r => ['CONFLICT_CORE_COMPLETE', 'BLOCKED_BY_HARD_CONSTRAINT', 'UNKNOWN'].includes(r.status)).forEach(r => r.dispatch_allowed = true));
  return outcomes;
}

const [, , fixturePath, candidatePath, outputPath, stdoutPath] = process.argv;
if (!fixturePath || !candidatePath || !outputPath || !stdoutPath) throw new Error('usage: audit.mjs FIXTURES.json CANDIDATE.json OUTPUT.json STDOUT.json');
const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
const candidate = JSON.parse(fs.readFileSync(candidatePath, 'utf8'));
const base = validate(fixture, candidate);
const controls = mutationTests(fixture, candidate);
const output = {base_oracle_match: base, mutation_controls_rejected: controls, all_mutations_rejected: Object.values(controls).every(Boolean), node: process.version, arch: process.arch, uid: process.getuid?.() ?? null};
fs.writeFileSync(outputPath, JSON.stringify(output) + '\n');
fs.writeFileSync(stdoutPath, JSON.stringify(output) + '\n');
console.log(JSON.stringify(output));
process.exitCode = base && output.all_mutations_rejected ? 0 : 1;
