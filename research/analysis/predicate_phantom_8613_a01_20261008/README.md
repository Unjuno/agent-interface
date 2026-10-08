# #8613 A01: Phantom membership model, immutable first outcome

**Result:** PASS_PHANTOM_DETECTED_SCOPED (artificial finite method only; NOT GUI/current-runtime/product acceptance). All 77,700 histories were evaluated exactly once; independent raw audit errors=[]; nine copied-evidence mutations rejected. NODE_ONLY had 13,465 unsafe admissions; ALWAYS_REQUERY 1,266; MEMBERSHIP_CERT zero false admits and zero false refusals under complete-history assumptions. See REPORT.md and Issue #8613.

Chronology: prospectively published unmodified source freeze commit df729d5e9ea23761156406c34f0f9e5d09c94ba4, then first outcome Issue comment, then additive result capsule.
FROZEN_SOURCE.tar.xz SHA256 9df12e0fbdc32d278c3bafcec6154798602b08b2ae6fdeff69a04fbf310dad32.
RESULT_CAPSULE.tar.xz SHA256 60149c6489f4c872dc98b197f8c1689c3f74287fc69cc369c9c91aa781e4ef25.
Original raw SHA256 e6c4e05f105a8009abe3242da19f9d845bedbdc660cb334f30d4808441d218a7.

Read-only revalidation from a fresh trusted directory:
```bash
mkdir -p /tmp/phantom8613-revalidate
tar -xJf RESULT_CAPSULE.tar.xz -C /tmp/phantom8613-revalidate
cd /tmp/phantom8613-revalidate
python -B verify_saved.py
```
Verifier checks frozen source hashes, raw/audit digests and reruns only saved-evidence audit/control, NEVER the consumed source/run.py. Use a fresh path on a trusted local filesystem; not a security sandbox. No shared runtime/workflow/policy changed. Merge only with real nonauthor review and applicable checks; global #57/#59/ROADMAP open.
