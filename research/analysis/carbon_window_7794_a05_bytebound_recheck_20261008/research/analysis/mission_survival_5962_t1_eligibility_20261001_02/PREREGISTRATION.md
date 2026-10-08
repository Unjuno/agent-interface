# Issue #5962 — retained-session eligibility T1 (allocation 01)

## H / T / D / C / U

- **H:** The retained public multi-task records contain some ordered six-task traces, but they may not form a source-identifiable, reset/exposure-auditable, comparable persistent-session cohort suitable for the Issue's T2 mission-survival route comparison.
- **T:** Read-only audit at current-main snapshot `ad123c3875d81ebdc8bdfbdb59340005d705a60d`. Verify the complete `public-six-task-comparison-04` raw archive against its GitHub-side SHA-256 manifest (all 1,051 members), then separately assess `current`, `interrupted02`, and `caller-stop03` for session identity, exact task order, complete first-outcome/effect ledger, carryover, reset boundaries, route/model exposure, STOP/missing-task disposition, and independent scoring. Cross-check the separately retained public summary for #2737 v4, without pooling it with comparison-04.
- **D:** Label a campaign fully T2-eligible only if each route/session has stable identity and source-bound trace, task order and every initiated outcome/stop are complete, reset and carryover boundaries are explicit, exposure/order is known and suitable for the registered comparison, and independent effect labels are retained. Otherwise retain partial/descriptive evidence but HOLD T2. Do not fill missing tasks, pool distinct seeds/source revisions, treat administrative interruption as success, or infer raw provenance from a compact summary.
- **C:** This audit scopes to the two published six-task records with explicit mission-like sequences: comparison-04's three retained campaigns and #2737 v4's committed summary. It does not search or claim census coverage of every single-task or task-specific study in the repository. The archive content is untrusted evidence and is parsed as data only; no archived executable is run.
- **U:** T1 is eligibility/provenance only. It does not estimate route reliability, dependence kernels, comparative mission survival, user benefit, or product performance. Any later T2 needs separately frozen matched independent sessions and a complete retained outcome/STOP ledger.

## Data identities and execution boundary

- Comparison-04 top-level manifest at frozen main: path `runtime/results/public-six-task-comparison-04/manifest.json`, Git blob `68d328b9a9d99a6b19c84aa7ac9f8a152d810a5b`.
- Raw archive: `runtime/results/public-six-task-comparison-04/raw.tar.gz`, manifest SHA-256 `811e63849956658bdbb0fecc1a7237308dd93c71d96644050b1581bc243c4dd2`.
- #2737 public summary: `research/analysis/full_golden_ipc_2737_v1/RESULT.json`, Git blob `69c7ae2f69f701e4b951aaebc6b6071942c969a8`; it names allocation v4 / seed 991035, container image digest, six exact effects and verified releases. Its README says the complete report remains local, not in the committed directory.
- Local CPU/Python standard-library audit only. No Docker, GUI, model, input, network activity by the audit program, or change to retained experiment results. The archive and manifest were downloaded read-only from the commit-pinned public GitHub URLs and SHA-checked.
