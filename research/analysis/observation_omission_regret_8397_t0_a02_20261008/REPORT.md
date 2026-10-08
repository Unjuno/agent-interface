# Issue #8397 T0 A02 — state-conditioned observation-omission fixture

**Result: `PASS_METHOD_SCOPED`.** The one-shot candidate emitted eight finite trace records; the separate raw-only auditor reconstructed all eight exactly with no errors.

## H / T / D / C / U

**H.** In this fixed deterministic fixture, the effect of omitting optional observations depends on task state and interval placement: some intervals preserve exact effects while reducing model-visible cost; one interval crossing a target transition creates a wrong-target effect and recovery.

**T.** The fixture includes matched baseline/omission records before an observation-sensitive decision, across a target transition, and after an independently verified terminal effect, plus a captured-but-undelivered transport control and a mandatory-safety-cue rejection control. Every row records interval, captured and delivered counts, visible bytes, mandatory-cue status, decision, exact effect, recovery steps, and stop outcome. The raw-only auditor defines its own expected rows and does not import the candidate.

**D.** The auditor matched all eight exact records; distinguished captures from deliveries; found the pre-decision omission preserved the effect while reducing delivered observations from 3 to 2 and visible bytes from 300 to 200; found the transition-crossing omission produced `wrong_A_then_B_recovered` with one recovery step; found post-completion omission preserved the verified effect while reducing the same costs; and confirmed the captured-but-undelivered control remained distinct. The mandatory-cue omission request was rejected, the cue stayed delivered, and no external effect occurred. No errors; `PASS_METHOD_SCOPED`.

**C.** These hand-authored traces may overstate how often real GUI tasks contain harmless or observation-sensitive intervals. The synthetic effect labels are not a real application oracle.

**U.** This does not measure a model, screenshots, GUI behavior, timing, actual API cost, safety, or a deployable observation scheduler. The finite fixture cannot establish rare-event risk or transfer to another task or policy.

## Execution and provenance

- Allocation: `OBS-OMISSION-REGRET-8397-T0-A02-20261008`
- Branch: `research/8397-observation-omission-t0-a02-20261008`
- Base/current-main SHA: `2f36f501f11931e052dbc3fb0000a9200bff7f50`
- Pre-run freeze commit: `86ca4388d77c96f7b53024e4701ee5cce346ef75`
- Candidate and auditor: each one formal invocation, exit 0; retries 0. Raw-only audit status `PASS_METHOD_SCOPED`, rows 8, errors empty.
- Runtime: native macOS CPython 3.14.5 under `sandbox-exec` with `(deny network*)`. No container, model, GUI, OS input, user data, or external effect. This is not Docker/OrbStack reproduction and makes no container-isolation/resource-cap claim.
- OrbStack preflight: `docker ps` succeeded; image list/metadata inspection failed on a content-store blob with `operation not supported`. Host volume had 146 GiB available at 97% use. No pull, build, prune, daemon restart, or repair was attempted.
- Freeze source digests, exact commands, construction history, candidate/audit JSON, stdout, and outcome hashes are retained alongside this report.
