import fs from 'node:fs';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';

const sha256 = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const fail = (errors, code, detail) => errors.push({code, detail});

export function auditRaw(fixture, fixtureBytes, raw) {
  const errors = [];
  if (raw.schema_version !== 1 || raw.allocation_id !== fixture.allocation_id) fail(errors, 'ROOT_IDENTITY', 'schema/allocation mismatch');
  if (raw.fixture_sha256 !== sha256(fixtureBytes)) fail(errors, 'FIXTURE_DIGEST', 'fixture bytes differ');
  if (!Array.isArray(raw.records) || raw.records.length !== fixture.conditions.length) {
    fail(errors, 'CASE_DENOMINATOR', 'case set mismatch');
    return {errors, rows: []};
  }
  const rows = [];
  const expectedArms = ['ROSTER_NOT_ADVERTISED', 'ROSTER_TRUTHFULLY_ADVERTISED'];
  const treatmentText = 'A second independent reviewer is reviewing this same claim; no peer verdict or rationale is available.';
  for (let i = 0; i < fixture.conditions.length; i += 1) {
    const expected = fixture.conditions[i];
    const observed = raw.records[i];
    if (observed.case_id !== expected.case_id || observed.pattern !== expected.pattern || observed.truth !== expected.truth) {
      fail(errors, 'CASE_IDENTITY', expected.case_id);
      continue;
    }
    if (!Array.isArray(observed.arms) || observed.arms.length !== 2) {
      fail(errors, 'ARM_DENOMINATOR', expected.case_id);
      continue;
    }
    for (let a = 0; a < 2; a += 1) {
      const arm = observed.arms[a];
      const announced = a === 1;
      if (arm.arm !== expectedArms[a]) fail(errors, 'ARM_LABEL', expected.case_id);
      const expectedContext = {
        task_id: fixture.task_id,
        prompt_base_id: fixture.prompt_base_id,
        source_digest: fixture.source_digest,
        evidence_pool: fixture.evidence_pool,
        per_reviewer_request_cap: fixture.per_reviewer_request_cap,
        actual_reviewer_count: fixture.actual_reviewer_count,
        reducer: fixture.reducer,
        roster_disclosed: announced,
        roster_text: announced ? treatmentText : 'Review the claim independently using the supplied evidence.'
      };
      if (JSON.stringify(arm.context) !== JSON.stringify(expectedContext)) fail(errors, 'CONTEXT_OR_TOPOLOGY', `${expected.case_id}/${arm.arm}`);
      if (!Array.isArray(arm.reviewers) || arm.reviewers.length !== 2) {
        fail(errors, 'REVIEWER_DENOMINATOR', `${expected.case_id}/${arm.arm}`);
        continue;
      }
      const ids = arm.reviewers.map((reviewer) => reviewer.reviewer_id);
      if (new Set(ids).size !== 2 || ids.some((id) => !['R1', 'R2'].includes(id))) fail(errors, 'REVIEWER_IDENTITY', `${expected.case_id}/${arm.arm}`);
      const eventSeq = new Map();
      const requestEvents = new Map();
      const resultEvents = new Map();
      const commits = new Map();
      let previous = 0;
      for (const event of arm.events) {
        if (!Number.isInteger(event.sequence) || event.sequence <= previous) fail(errors, 'EVENT_ORDER', `${expected.case_id}/${arm.arm}`);
        previous = event.sequence;
        eventSeq.set(event.event_id, event.sequence);
        if (event.type === 'tool_request') {
          if (requestEvents.has(event.request_id)) fail(errors, 'DUPLICATE_REQUEST', event.request_id);
          requestEvents.set(event.request_id, event);
        } else if (event.type === 'tool_result') {
          if (resultEvents.has(event.request_id)) fail(errors, 'DUPLICATE_RESULT', event.request_id);
          resultEvents.set(event.request_id, event);
        } else if (event.type === 'first_pass_commit') {
          if (commits.has(event.reviewer_id)) fail(errors, 'DUPLICATE_COMMIT', event.reviewer_id);
          commits.set(event.reviewer_id, event);
        }
      }
      for (let r = 0; r < 2; r += 1) {
        const reviewer = arm.reviewers[r];
        const expectedReviewer = expected.reviewers[r];
        if (reviewer.reviewer_id !== expectedReviewer.reviewer_id || reviewer.request_cap !== fixture.per_reviewer_request_cap || JSON.stringify(reviewer.queries) !== JSON.stringify(expectedReviewer.queries) || reviewer.verdict !== expectedReviewer.verdict || reviewer.finding !== expectedReviewer.finding || reviewer.tool_log_complete !== expectedReviewer.tool_log_complete) {
          fail(errors, 'REVIEW_RECORD', `${expected.case_id}/${arm.arm}/${expectedReviewer.reviewer_id}`);
        }
        if (reviewer.queries.length > fixture.per_reviewer_request_cap) fail(errors, 'REQUEST_CAP', reviewer.reviewer_id);
        for (let q = 0; q < reviewer.queries.length; q += 1) {
          const requestId = `${expected.case_id}:${arm.arm}:${reviewer.reviewer_id}:q${q + 1}`;
          const request = requestEvents.get(requestId);
          const result = resultEvents.get(requestId);
          const intentionallyMissing = expected.pattern === 'missing_tool_log' && reviewer.reviewer_id === 'R2' && q === 1;
          if (!request || request.reviewer_id !== reviewer.reviewer_id || request.evidence_id !== reviewer.queries[q]) fail(errors, 'REQUEST_JOIN', requestId);
          if (intentionallyMissing) {
            if (result) fail(errors, 'MISSING_LOG_FALSE_COMPLETION', requestId);
          } else if (!result || result.reviewer_id !== reviewer.reviewer_id || result.evidence_id !== reviewer.queries[q] || eventSeq.get(result.event_id) <= eventSeq.get(request?.event_id)) {
            fail(errors, 'RESULT_JOIN', requestId);
          }
        }
        const commit = commits.get(reviewer.reviewer_id);
        const expectedCommitId = `${expected.case_id}:${arm.arm}:${reviewer.reviewer_id}:commit`;
        if (!commit || commit.event_id !== expectedCommitId || commit.verdict !== reviewer.verdict || commit.finding !== reviewer.finding) fail(errors, 'COMMIT_JOIN', expectedCommitId);
        if (commit && arm.events.some((event) => event.reviewer_id === reviewer.reviewer_id && ['tool_request', 'tool_result'].includes(event.type) && event.sequence >= commit.sequence)) fail(errors, 'TOOL_AFTER_COMMIT', expectedCommitId);
      }
      const peer = arm.events.find((event) => event.type === 'peer_content_release');
      const commitValues = [...commits.values()];
      if (!peer || commitValues.length !== 2 || commitValues.some((commit) => peer.sequence <= commit.sequence)) fail(errors, 'PEER_RELEASE_BEFORE_COMMIT', `${expected.case_id}/${arm.arm}`);
      if (peer && JSON.stringify(peer.released_after) !== JSON.stringify(arm.reviewers.map((reviewer) => reviewer.commit_event_id))) fail(errors, 'PEER_RELEASE_LINK', `${expected.case_id}/${arm.arm}`);
      const missing = arm.reviewers.some((reviewer) => !reviewer.tool_log_complete);
      const falsePass = expected.truth === 'FAULTY_EFFECT' && arm.reviewers.some((reviewer) => reviewer.verdict === 'PASS');
      const correct = arm.reviewers.every((reviewer) => expected.truth === 'AMBIGUOUS_EFFECT'
        ? reviewer.verdict === 'UNKNOWN'
        : expected.truth === 'VALID_EFFECT'
          ? reviewer.verdict === 'PASS'
          : reviewer.verdict === 'FAIL');
      rows.push({
        case_id: expected.case_id,
        arm: arm.arm,
        reviewer_count: arm.reviewers.length,
        request_count: arm.reviewers.reduce((sum, reviewer) => sum + reviewer.queries.length, 0),
        truth: expected.truth,
        false_pass: falsePass,
        correctness: correct ? 'CORRECT' : falsePass ? 'INCORRECT' : missing ? 'HOLD_MISSING_TOOL_LOG' : 'INCORRECT',
        incomplete_tool_log: missing,
        peer_content_after_commit: Boolean(peer && commitValues.length === 2 && commitValues.every((commit) => peer.sequence > commit.sequence))
      });
    }
  }
  if (errors.length === 0 && rows.length !== 10) fail(errors, 'ROW_DENOMINATOR', `expected 10, saw ${rows.length}`);
  return {errors, rows};
}

function clone(value) { return JSON.parse(JSON.stringify(value)); }

export function runAudit(fixture, fixtureBytes, raw) {
  const baseline = auditRaw(fixture, fixtureBytes, raw);
  const mutationChecks = [];
  const mutations = [
    ['missing_tool_event', (copy) => { copy.records[0].arms[0].events = copy.records[0].arms[0].events.filter((event) => event.type !== 'tool_result'); }],
    ['peer_content_exposure', (copy) => { const arm = copy.records[0].arms[0]; arm.events.find((event) => event.type === 'peer_content_release').sequence = 1; }],
    ['duplicate_reviewer_identity', (copy) => { copy.records[0].arms[0].reviewers[1].reviewer_id = 'R1'; }],
    ['request_context_mutation', (copy) => { copy.records[0].arms[1].context.source_digest = 'sha256:mutated'; }],
    ['event_order_mutation', (copy) => { const events = copy.records[0].arms[0].events; [events[0].sequence, events[1].sequence] = [events[1].sequence, events[0].sequence]; }],
    ['early_peer_content_release', (copy) => { const arm = copy.records[1].arms[1]; const peer = arm.events.find((event) => event.type === 'peer_content_release'); peer.released_after = [arm.reviewers[0].commit_event_id]; }]
  ];
  for (const [name, mutate] of mutations) {
    const copy = clone(raw);
    mutate(copy);
    const result = auditRaw(fixture, fixtureBytes, copy);
    mutationChecks.push({name, rejected: result.errors.length > 0, error_count: result.errors.length});
  }
  const result = {
    schema_version: 1,
    allocation_id: fixture.allocation_id,
    fixture_sha256: sha256(fixtureBytes),
    raw_sha256: sha256(Buffer.from(`${JSON.stringify(raw, null, 2)}\n`)),
    status: baseline.errors.length === 0 && mutationChecks.every((check) => check.rejected) ? 'PASS_METHOD_SCOPED' : 'FAIL_AUDIT',
    errors: baseline.errors,
    case_count: fixture.conditions.length,
    row_count: baseline.rows.length,
    rows: baseline.rows,
    mutation_checks: mutationChecks,
    mutation_rejections: mutationChecks.filter((check) => check.rejected).length,
    model_or_human_calls: 0,
    limitations: ['authored synthetic measurement ledger only', 'no model or human behavior measured', 'no GUI, user data, authority, or task-effect claim']
  };
  return result;
}

function main() {
  const [fixturePath, rawPath, outputPath] = process.argv.slice(2);
  if (!fixturePath || !rawPath || !outputPath) throw new Error('usage: audit.mjs FIXTURE RAW OUTPUT');
  const fixtureBytes = fs.readFileSync(fixturePath);
  const fixture = JSON.parse(fixtureBytes.toString('utf8'));
  const raw = JSON.parse(fs.readFileSync(rawPath, 'utf8'));
  const result = runAudit(fixture, fixtureBytes, raw);
  fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`, {flag: 'wx', mode: 0o400});
  if (result.status !== 'PASS_METHOD_SCOPED') process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();
