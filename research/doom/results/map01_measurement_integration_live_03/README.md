# MAP01 measurement-integration live-03 — retained first outcome

## H / T / D / C / U

- **H:** The frozen no-model/no-retry MAP01 v13 probe can retain direct input-release telemetry, independent scorer cadence, and a final score that agrees with scorer output.
- **T:** One run of allocation `map01-measurement-integration-live-03`, seed `990613`, under `.github/workflows/map01-measurement-integration-live-03.yml`. The GitHub Actions event was `push` from archival tag `archive/recovered/5776-probe-intervention-t1-01-original-20261002` (tag commit `76169df35bf56309724aa836baf93809c8fc8704`), not `workflow_dispatch` or a PR. The workflow's canonical launch-owner gate selected run `37010961990`; all frozen runtime source hashes matched base `5486ea20b417a80903619a384744cf9ac38d5a52`. Candidate=1, measurement audit=1, terminal-score audit=1, retries=0.
- **D:** The recorded measurement audit is `PASS measurement integration`; terminal comparison is `PASS terminal score agreement`. It retained 19 scorer samples, zero controller/scorer leaks, one strict-equal final scorer sample, one completed hold and zero interrupted holds. Two direct key-release transitions were recorded with zero invalid or unmatched releases; measured release-batch window was 538.7 μs. The measurement audit reports zero positive useful events, allowed by this measurement-only gate. Terminal score: 0 kills, 0 deaths, `map_exit=false`, `episode_finished=false`, `player_dead=false`.
- **C:** GitHub-hosted Ubuntu 24.04.5 x86_64; CPython 3.13.15; ViZDoom 1.3.0 with FreeDoom2 (`iwad_sha256=a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`); seed 990613; 60-second episode timeout. The run was not local WSLc or a container experiment and made zero model calls.
- **U:** This was a narrow telemetry/integration gate, not recovery-vs-coast efficacy, gameplay benefit, safety, speed, or MAP01 completion. The archival-tag push unintentionally triggered the existing workflow; preserve that provenance, do not rerun this consumed allocation, and do not treat this result as the separately authorized WSLc allocation.

## Immutable run artifacts

The complete downloaded Actions artifact is preserved under [`run-37010961990/`](run-37010961990/), including the launch-owner receipt, runner environment, controller/scorer events, raw runtime logs, frames, score, both audit outputs, and the original `formal-audit.stdout`. `SHA256SUMS` covers every extracted artifact file. GitHub artifact id `11228425736`, name `map01-measurement-integration-live-03-37010961990`, size 943,936 bytes, archive digest `sha256:eeee3ab549b8aef447cef3ae6e44e98c985e5ed37ca11eab845178861a3d6095`; GitHub retention expiry was 2026-11-01.

No candidate or auditor was rerun while packaging this first outcome. The hosted audit JSON and event stream are retained verbatim; this report summarizes, but does not upgrade, their scope.
