# Integration handoff

Issue #5791. This additive construction complements, but does not replace, the controller-local source eligibility report in research/analysis/effect_path_antiwindup_5791_eligibility_v1/.

The exact runner wrapper passes the returned thread ID through exec resume and sends the next explicit no-visible-effect feedback prompt to the CLI boundary. The test uses a deterministic child-process stub, not the Codex CLI or provider. It establishes interface plumbing only; provider transcript semantics remain unobserved.

Do not treat this as a model behavior result, anti-windup eligibility result, live T1 authorization, or product success. Preserve candidate-output/ and the initial preflight STOP. Any real-provider follow-up must be a separately authorized model allocation with transcript/raw evidence and no retry.
