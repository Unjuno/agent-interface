# Issue #2001 successor — approximate change gate with exact fallback

## H/T/D/C/U

- **H:** An approximate global gate may be a performance hint, but an exact fallback is required to prevent suppression of task-relevant micro-changes while retaining raw frames.
- **T:** Freeze six GUI-like cases: unchanged, sparse noise, task-relevant micro-change, task-relevant large change, panel change, and unchanged panel. Compare coarse global average-hash equality with exact byte comparison and fallback forwarding.
- **D:** `experiment.py`, case labels, raw frame-derived rows, fallback decisions, and SHA-256 digest.
- **C:** The approximate gate must expose a task-relevant false-suppression case; exact fallback must forward it; unchanged controls must remain suppressible; raw evidence remains represented by exact frame comparison.
- **U:** Natural GUI prevalence, CPU/latency savings, model/token impact, region-aware hashing, and runtime promotion remain unknown.
- **STOP:** One finite local/container-independent fixture; no model, GUI, network, runtime, or user data.

## Result

Command: `python experiment.py`

- 6 cases.
- Global approximate gate alone falsely suppresses **1 task-relevant micro-change**.
- Exact fallback catches **4 changed cases**, including the task-relevant micro-change.
- Unchanged and unchanged-panel controls remain suppressible.
- Result digest: `05a943e5aae7e76ba0a38f9fe48dab927c2406fc94c5732fba2858807788ca7b`.

**Decision: PASS_EXACT_FALLBACK_REQUIRED_SCOPED.**

This supports only the safety requirement for an exact fallback in this fixture. It does not establish natural prevalence, latency savings, model/token benefit, GUI correctness, or runtime promotion.
