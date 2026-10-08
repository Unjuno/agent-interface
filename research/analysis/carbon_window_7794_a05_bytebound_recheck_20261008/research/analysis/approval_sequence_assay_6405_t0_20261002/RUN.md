# Formal run receipt

Allocation: `APPROVAL-SEQUENCE-ASSAY-6405-T0-20261002-01`

Source/base: `d0e2a0f7b10bd3eecf4741f045e90d15ee43e3ad`

Run time: 2026-10-02 01:40 UTC (UTC minute resolution)

Runtime: macOS arm64, CPython 3.14.5; no container, network, model, GUI,
participant, or live approval path.

## Start gate

- Exact main/base SHA matched the freeze at the pre-run check.
- Candidate and audit output files were both absent.
- Frozen source and fixture hashes matched `FREEZE.md`.
- Construction tests: 8/8; Python compilation and `git diff --check`: pass.
- `wslc.exe` was unavailable here; OrbStack context had pre-existing
  `unjuno-native-ci-6092` running. Neither runtime nor container was modified.

## Commands and counts

1. `python3 candidate.py --input fixtures/sequence.json --output results/formal-01/candidate.json`
   — one formal invocation, exit 0; stderr empty. Candidate stdout and exit
   sidecar are retained beside the candidate JSON.
2. `python3 audit.py --input fixtures/sequence.json --candidate results/formal-01/candidate.json --output results/formal-01/audit.json`
   — one separate formal invocation after candidate exit 0, exit 0; stderr
   empty. Auditor stdout and exit sidecar are retained beside the audit JSON.

Formal retries: 0. No formal command was rerun. Construction tests ran before
formal execution and are separately labeled; they do not consume or replace the
two formal invocation counts above.

## Audited outcome

`PASS_METHOD_SCOPED`, 5 request rows, 3 display arms, zero baseline errors,
6/6 mutations rejected. Candidate JSON SHA-256:
`a76beaf471490cfee9d0c9e0ed6de395517d685db4a326d97655420de2320b0a`.
Audit JSON SHA-256:
`e1db759512f295a9d87c39f1aef4325aa076b0c5ce1c82dfbf2e6e9fc0e6589d`.
Both stderr streams are empty (SHA-256 of empty bytes).

The auditor independently derives differences and digests from the retained
fixture and candidate output; it does not import candidate code. The pass says
only that this finite display/receipt contract and its six authored controls
behaved as frozen. See [`REPORT.md`](REPORT.md) for scope limits.

## Ancillary check diagnostics

- The first attempt to refresh the analysis index ran from this package
  directory with a repository-root-relative path and failed to locate the
  script. Re-running from the repository root refreshed the index and the
  check passed at 386 entries; no source or result was affected.
- The first checksum-manifest command used package-relative paths from the
  repository root and produced file-not-found diagnostics. It was rerun from
  the package directory; all 16 manifest entries then verified.
- Broad `unittest discover -s research` is not the repository CI invocation:
  two unrelated suites rely on package-local import paths and produced import
  errors under that broader invocation (34 tests passed, 2 imports failed).
  The exact workflow command then passed 21/21 workspace tests.
- Public Navigation initially failed while this package was still
  untracked. After staging the exact package and navigation-index files, the
  repository checker passed with 26 documents and 1,250 relative links.
- An initial staged diff check found trailing whitespace in Markdown hard
  line breaks. Those separators were replaced with blank lines; the final
  staged diff check is rerun after this note is added.
