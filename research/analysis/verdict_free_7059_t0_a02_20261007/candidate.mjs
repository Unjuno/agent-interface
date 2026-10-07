import fs from 'node:fs';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';

const sha256 = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

export function buildRaw(fixture, fixtureBytes) {
  if (fixture.schema_version !== 1 || fixture.actual_reviewer_count !== 2) {
    throw new Error('unsupported frozen fixture');
  }
  const records = fixture.conditions.map((condition) => {
    const arms = ['ROSTER_NOT_ADVERTISED', 'ROSTER_TRUTHFULLY_ADVERTISED'];
    const armRecords = arms.map((arm) => {
      const announced = arm === 'ROSTER_TRUTHFULLY_ADVERTISED';
      const context = {
        task_id: fixture.task_id,
        prompt_base_id: fixture.prompt_base_id,
        source_digest: fixture.source_digest,
        evidence_pool: fixture.evidence_pool,
        per_reviewer_request_cap: fixture.per_reviewer_request_cap,
        actual_reviewer_count: fixture.actual_reviewer_count,
        reducer: fixture.reducer,
        roster_disclosed: announced,
        roster_text: announced
          ? 'A second independent reviewer is reviewing this same claim; no peer verdict or rationale is available.'
          : 'Review the claim independently using the supplied evidence.'
      };
      const events = [];
      let sequence = 0;
      const reviewers = condition.reviewers.map((source) => {
        const reviewer = {
          reviewer_id: source.reviewer_id,
          request_cap: fixture.per_reviewer_request_cap,
          queries: [...source.queries],
          verdict: source.verdict,
          finding: source.finding,
          tool_log_complete: source.tool_log_complete,
          commit_event_id: `${condition.case_id}:${arm}:${source.reviewer_id}:commit`
        };
        for (let ordinal = 0; ordinal < source.queries.length; ordinal += 1) {
          const query = source.queries[ordinal];
          const requestId = `${condition.case_id}:${arm}:${source.reviewer_id}:q${ordinal + 1}`;
          events.push({
            sequence: ++sequence,
            event_id: `${requestId}:request`,
            type: 'tool_request',
            reviewer_id: source.reviewer_id,
            request_id: requestId,
            evidence_id: query
          });
          if (!(condition.pattern === 'missing_tool_log' && source.reviewer_id === 'R2' && ordinal === 1)) {
            events.push({
              sequence: ++sequence,
              event_id: `${requestId}:result`,
              type: 'tool_result',
              reviewer_id: source.reviewer_id,
              request_id: requestId,
              evidence_id: query,
              result_digest: `sha256:${condition.case_id.toLowerCase()}:${query.toLowerCase()}`
            });
          }
        }
        events.push({
          sequence: ++sequence,
          event_id: reviewer.commit_event_id,
          type: 'first_pass_commit',
          reviewer_id: source.reviewer_id,
          verdict: source.verdict,
          finding: source.finding
        });
        return reviewer;
      });
      events.push({
        sequence: ++sequence,
        event_id: `${condition.case_id}:${arm}:peer-release`,
        type: 'peer_content_release',
        released_after: reviewers.map((reviewer) => reviewer.commit_event_id),
        content: reviewers.map(({reviewer_id, verdict, finding}) => ({reviewer_id, verdict, finding}))
      });
      return { arm, context, reviewers, events };
    });
    return {
      case_id: condition.case_id,
      pattern: condition.pattern,
      truth: condition.truth,
      arms: armRecords
    };
  });
  return {
    schema_version: 1,
    allocation_id: fixture.allocation_id,
    fixture_sha256: sha256(fixtureBytes),
    records
  };
}

function main() {
  const [fixturePath, outputPath] = process.argv.slice(2);
  if (!fixturePath || !outputPath) throw new Error('usage: candidate.mjs FIXTURE OUTPUT');
  const fixtureBytes = fs.readFileSync(fixturePath);
  const fixture = JSON.parse(fixtureBytes.toString('utf8'));
  const raw = buildRaw(fixture, fixtureBytes);
  fs.writeFileSync(outputPath, `${JSON.stringify(raw, null, 2)}\n`, {flag: 'wx', mode: 0o400});
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();
