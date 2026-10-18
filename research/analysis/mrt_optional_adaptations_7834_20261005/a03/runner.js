const fs = require("node:fs");

const mode = process.argv[2];
const input = JSON.parse(fs.readFileSync("/src/fixture.json", "utf8"));
const candidateSource = fs.readFileSync("/src/candidate.js", "utf8");
const auditorSource = fs.readFileSync("/src/auditor.js", "utf8");

if (mode === "candidate") {
  const candidate = eval("(" + candidateSource + ")");
  const report = candidate(input);
  fs.writeFileSync("/out/candidate.raw.json", JSON.stringify(report, null, 2) + "\n");
  process.stdout.write(JSON.stringify({
    mode,
    allocation: report.allocation,
    rows: report.rows.length,
    eligible_weight: report.eligible_weight
  }) + "\n");
} else if (mode === "audit") {
  const report = JSON.parse(fs.readFileSync("/input/candidate.raw.json", "utf8"));
  const auditor = eval("(" + auditorSource + ")");
  const audit = auditor(input, report);
  fs.writeFileSync("/out/audit.raw.json", JSON.stringify(audit, null, 2) + "\n");
  process.stdout.write(JSON.stringify({
    mode,
    allocation: audit.allocation,
    base_audit: audit.base_audit,
    expected_rows: audit.expected_rows,
    observed_rows: audit.observed_rows,
    mutation_count: audit.mutation_count,
    rejected_mutations: audit.mutations.filter(x => x.rejected).length
  }) + "\n");
  if (!audit.base_audit || audit.mutations.some(x => !x.rejected)) process.exitCode = 1;
} else {
  throw new Error("mode must be candidate or audit");
}
