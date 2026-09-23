# Interrupt-stack evidence-bound resume contract — Result

Issue #4201, successor to #2869. Allocation `interrupt-stack-resume-4201-20260923-01`.

## Result

**`PASS_INTERRUPT_STACK_RESUME_CONTRACT_SCOPED`** from one prospectively source/hash-frozen 96-state finite allocation. Formal invocation/reruns/replacements/tuning: **1/0/0/0**.

- independent raw-only audit: **884 checks, errors=[]**
- candidate unsafe RESUME: **0**
- candidate safe RESUME: **2**
- candidate false refusal: **0**
- POP_ONLY unsafe RESUME: **22**
- QUEUE_VERSION_ONLY unsafe RESUME: **10**
- UNKNOWN-result candidate resumes: **0**
- authority violations: **0**
- corruption controls rejected: **12/12**

Candidate typed dispositions across all 96 states: `{"CANCELED": 48, "RECONCILE_RESULT": 8, "REPLAN_QUEUE": 4, "RESUME": 2, "REVALIDATE_TARGET": 2, "WAIT_INTERRUPT": 24, "YIELD_STALE": 8}`.

## H / T / D / C / U

- **H:** stack pop or queue-version equality alone is insufficient resume evidence; liveness, interrupt resolution, pending-result disposition, source freshness, queue version and target identity must remain compatible under the declared finite contract.
- **T:** exhaustive 2×2×2×2×2×3 = 96 authored states, three policies, CPython 3.13.5 standard library in the provided Linux container. No GUI/input/model/provider/network.
- **D:** candidate exactly matches a separately implemented oracle, resumes exactly the two safe states, never resumes UNKNOWN-result states, and the two weaker controls expose directed unsafe resumes. All frozen integrity gates and 12 corruption controls pass.
- **C:** the state vector is complete by construction. Real applications can have additional dependencies or richer equivalence relations.
- **U:** no live interruption/task effect, model utility, natural frequency, latency/token benefit, crash durability or production promotion.

## Integrity / provenance

Construction: 7/7 hand-authored unit checks and py_compile passed. Before formal, a static review found three no-op corruption mutations in the first source freeze; with formal rows still zero, only those mutation targets were moved to an effective safe row and the freeze was republished. The scientific corpus, policies, oracle, denominator and gates did not change.

Formal raw: 74365 bytes; SHA-256 `2de15af3c6b24b277883ae84c5c4c92de3076dab017d2caa8961a8bee5f6e8b6`. `FORMAL_RESULT.json.zlib.b64` is a lossless compressed representation; `unpack_formal.py` verifies and restores the exact original bytes.

## Integration meaning

A saved interrupt frame is continuation context, not automatic authority. A later live successor should test one-level interruption with independently observed target/queue/result evidence and task effects. This result does not close #2869 or #2789.
