# Preservation qualification — 2026-10-02

This append-only note qualifies integration of the original historical package. It does not amend its PLAN, RUN, REPORT, fixture, source, raw output, audit, or SHA256SUMS and does not record a new experiment.

## Preserved result and scope

Retain `FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER` exactly as a deterministic synthetic source-composition counterexample. The retained push-run anchor is `34971205791`; row `90000000001` is explicitly synthetic and must never be described as an observed or dispatched GitHub run. Per-event singleton payloads are admitted in the retained output. This does not prove a duplicate live execution, scheduling/concurrency behavior, API pagination behavior, runtime safety, task effect, or MAP01 efficacy. The historical live-04 measurement result remains unchanged.

Historical “current-main”/“current source” references in the unchanged package refer to freeze `2b899413d30fcee0ce97e7c69d83f7b2f69e89dd`, not a continuously refreshed runtime finding. At review main `e080330d1b84e8ebecef8bf5f8e91d0eb70487f1`, the live-04 workflow blob `45279028918eff71332e627b1f783dfb11d27e49` and helper blob `f07f928f67a7a6c670d399efb23d67246506c802` still matched the freeze, and all eight explicit workflow runtime-source blob pins matched. The source still contains push/workflow_dispatch and `event=$GITHUB_EVENT_NAME` query partitioning. These static facts do not establish workflow activation state or newly observed operational reachability.

## Provenance and missing records

All ten original package files match first publication commit `8162444eac950ce9f4e9eefc929fb92163d2d357` and pre-integration head `c7e2b989dc59b6ce6196fdcbf22ace58fa4fad1e`. All nine original SHA256SUMS entries match.

RUN retains both the malformed initial construction command and malformed first auditor CLI, followed by a corrected construction invocation and one valid independent audit. Do not erase these deviations, count the CLI failure as an oracle result, or describe the ledger as having only one auditor process invocation. Historical execution/test counts and exit statuses remain the ledger's assertions: separate original stderr/exit-status receipts and the helper-suite test log are not present in this ten-file package.

The ledger lists pre-execution SHA-256 hashes, but the two-commit PR history first publishes source and outcomes together. A separate earlier Git freeze commit was not identified. This limits independently verifiable Git ordering; it does not prove the local preregistration did not occur. No missing process record or prospective timestamp is reconstructed here.

## Successor and authority boundary

Merged [PR #5985](https://github.com/Unjuno/agent-interface/pull/5985) already retains the larger eight-case event/head synthetic factorial. This package adds its earlier provenance and is not a new untested experiment. Merged [PR #5995](https://github.com/Unjuno/agent-interface/pull/5995) retains a scoped four-row/two-page all-events history method; it explicitly does not repair the production live-04 workflow or validate live pagination/races. [PR #5948](https://github.com/Unjuno/agent-interface/pull/5948) remains subject to its explicit owner Draft hold and is not cleared by this preservation.

[Issue #59](https://github.com/Unjuno/agent-interface/issues/59) remains open. Its [current reviewed execution-gate record](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5945480863) requires a fresh exact owner/resource assignment and separately frozen one-shot protocol. No historical allocation, source freeze, resource window, CPU/Xvfb/GPU assignment or test result is renewed here.

Only static metadata, Git-blob/SHA-256, Python AST and JSON inspection was used for this qualification. Ordinary maintenance CI, if run for publication, is verification of repository maintenance only; it is not a candidate/auditor rerun or new scientific PASS.

## Original-byte custody inventory

| Original file | Git blob | SHA-256 |
| --- | --- | --- |
| PLAN.md | `ccc5987cc09d0351a23dda96cf7822e65b2973ea` | `a2d494a18f436a31597c19feadcfa656034b3206c7cd86ce7659a04d9fbfc51f` |
| REPORT.md | `78a9dc62ff536882416f36312274f0ad331a69f0` | `f412ce868cfe546f2e21fa6fa0b342b9e8ba431e8dd7ec145c90a4408f1187d5` |
| RUN.md | `6a4b6baafd6a1f3a903814b3c182e343558e6c0f` | `23f2f306704a24656fbafe917550879317c2c6a1855b1978ade872d022418915` |
| SHA256SUMS | `d2377f46a36cc169de1a7be5ea778bef2566338b` | `4cd0032f30c44fa64e527787726aabca73826111237b6bf6932ac477f36814c3` |
| audit.json | `1317fe64b08f6c4636a54209e9fec7307b7f6f70` | `3633393e8a424361832ff39fff3dae848b182b9d56f56fceb0482c7bda60d2f7` |
| auditor.py | `68eed8f6ee275aea7610312914d2e1ce49e54273` | `e5d0ece96c352d40b04d59dc43b63e7433f81d4aacf87406706602241bd8e4e3` |
| candidate.py | `e147a2a129edb8eb820db742b070c0a39ddd2542` | `cb762de43411497d754cdbb389b2cdb35b5fe7bd020d89b3a2be4ab6c4aba026` |
| candidate_output.json | `845f7e8d9d1db9d8c1e0497b5400d9975b82fb12` | `5c8b719a5bd531c6826412d8ec165768a420a4d33dafdc1c15bb78a6fecbc0dd` |
| fixture.json | `68e362543314c3ad759913847f80f707089d3f94` | `f17953da59d6b86dced430783fef8bfc16dcb9b53157e1bec70b46a774a370ac` |
| test_construction.py | `bf17295d0e6c9dd63f0ae8c1e6cc262716448057` | `17090e6a9be422b78d1ac4329d44279d8419197ffbb569c5c0de5186648245e4` |
