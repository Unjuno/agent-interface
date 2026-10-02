# Issue #6684 T0 — formal execution STOP record

**Disposition: `STOP_INFRA_SESSION_CREATE`; candidate=0, independent formal auditor=0.**

## Frozen question and scope

The bounded question is whether a DBM-style relational bound can admit the authored common-translation safe cases that independent coordinate interval boxes refuse, without admitting unsafe states or gaining on the independent-shift control. The construction fixture is an integer-pixel 2-D target and one forbidden neighbor; it has no GUI, model, user data, network input, or OS effect.

## Construction evidence (not the formal allocation)

- Preregistered H/T/D/C/U and finite case roster: `PLAN.md`, `fixture.json`, `truth.json`.
- Candidate: `candidate.py`; independent raw-only audit implementation: `audit.py`.
- Pre-freeze SHA-256 values: `PRE_FREEZE_SHA256SUMS.txt`.
- Host construction/adversarial tests: 5/5 passed. Candidate construction plus separate auditor reported `PASS_METHOD_SCOPED` for the 11 authored rows. This does not satisfy the required formal WSLc candidate/auditor execution.

## Formal launch attempts and boundary

No formal candidate or formal auditor process started. No image was pulled and no existing WSLc session was reused, inspected beyond read-only inventory, altered, or terminated.

1. Read-only `wslc info --format json` and `wslc images --digests --format json` returned no usable image inventory; a query naming a not-yet-created session returned `WSLC_E_SESSION_NOT_FOUND`.
2. After checking the installed CLI's own help and Microsoft Learn instructions, the documented disposable-session path was attempted once with a new, dedicated storage directory: `wslc system session enter --name ai-6684-t0-20261002 C:\Users\junny\Documents\Codex\6684-wslc-isolated-store-20261002`.
3. Session creation exited 1 before a session or container was created: `ERROR_FILE_NOT_FOUND`. A subsequent read-only `wslc system session list --verbose` showed two pre-existing sessions; neither was selected or modified.

Therefore image digest/platform, container identity, runtime invocation, raw formal output, and kernel-confirmed resource enforcement are **not available**. Do not label construction output as formal, retry this allocation, or infer a scientific outcome from the startup failure. A new allocation requires external WSLc service/storage readiness and its own fresh authorization/freeze.

## Scoped disposition

The construction indicates only a finite authored-method contrast. Formal status remains `STOP_INFRA_SESSION_CREATE`; the hypothesis is neither formally passed nor scientifically failed. No GUI safety, application effect, runtime benefit, or product claim follows.
