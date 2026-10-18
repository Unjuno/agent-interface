# Issue #5749 A02 — label-blind action-only pipeline

## Outcome

`PASS_LABEL_BLIND_METHOD_SCOPED`. On six newly authored episodes (21 turns), the candidate emitted 63 policy rows without reading the separate target key or placing target/score fields in its output. Candidate, scorer, and auditor each exited 0 exactly once on the frozen formal inputs. The independent auditor reconstructed all 63 rows, returned no errors, rejected four raw-output mutations and two score/key mutations, and observed zero authority grants.

The protocol named five corruption classes; the auditor instantiated the combined score/key class as two separate mutations (`score_outcome` and `score_key_mutation`), so six concrete controls ran. This is additional rejection coverage, not a changed acceptance threshold.

This repairs a method/dataflow limitation recorded by action-only A01; it is not a causal or human-benefit confirmation. The fixture's post-hoc synthetic labels yield these descriptive counts: static default 17 wrong / 21 proposals / 0 queries; clarify-each-turn 0 wrong / 5 proposals / 21 queries / 16 yields; action-only 10 wrong / 14 proposals / 0 queries / 7 yields. Because actions and labels are authored and do not respond to the policies, these counts must not be interpreted as comparative efficacy, a preference-learning benefit, or measured interruption burden.

## Reproduction and retained evidence

Freeze and preregistration identities are in `FREEZE.json` (freeze SHA-256 `97be4520b4e790677a938f738f98309bfe4cebc789c128ac9defc28e851763e1`) and Issue #5749. Formal commands and first exits:

1. `python3 -B candidate.py --freeze FREEZE.json fixtures/policy_input.json results/formal01/candidate.raw.json` — exit 0.
2. `python3 -B scorer.py results/formal01/candidate.raw.json fixtures/scoring_key.json results/formal01/score.json --freeze FREEZE.json` — exit 0.
3. `python3 -B auditor.py fixtures/policy_input.json fixtures/scoring_key.json results/formal01/candidate.raw.json results/formal01/score.json --freeze FREEZE.json` — exit 0; `PASS_LABEL_BLIND_METHOD_SCOPED`, 63 rows, errors `[]`, raw mutations 4/4, score/key mutations 2/2.

- Candidate raw SHA-256: `14dda3718a5a252d1a3a38fca07eae23ff5fb5afd987f709b3cea8e943753601`.
- Scorer output SHA-256: `c95a8610c8331764580dd5ac7acff72240cafb30c655f01006c3df43ef67c764`.
- Pre-formal construction suite: 5/5 PASS; Python compilation and `git diff --check` PASS. The exact package-local unittest discovery also passed 5/5 after formal execution. One separate post-run command used a repo-relative test path while the shell was already in the package directory and returned unittest loader `ImportError`; no formal output was touched, and the README's exact package-local command succeeded. This is a command-path error, not a study outcome.

## Runtime and limits

OrbStack read-only `docker info` identified 29.4.0 linux/aarch64, but cached `python:3.12-slim` image inspection failed with containerd `operation not supported`. No repair, restart, pull, build, prune, or retry occurred. As authorized by this finite T0's “preferably container” wording, the frozen fallback used native macOS 27.0 arm64 / CPython 3.14.5; it makes no container-isolation claim. Host observation: 10 CPUs, 64 GiB RAM, 35% free at preflight, 12.34 GiB swap used; this workload was short-lived and standard-library-only.

The auditor is a separate implementation and process, not independent human review. Candidate and key shared a host filesystem, so separation proves the declared dataflow and strict schema rather than adversarial secrecy. No actual user, GUI, model, network, effect, safety outcome, privacy property, or transfer behavior was tested. Earlier T0, source-routing A01 and action-only A01 packages/results were not edited.
