# Edge visual-grounding plumbing preflight 01

**Disposition: setup rejected before model inference; allocation closed.**

This one-call preflight used the synthetic static form in `form.png` to check
Codex CLI image/schema plumbing. It was explicitly excluded from all efficiency
allocations and supplies no browser interaction, task effect, input-release,
latency-comparison, or token-economy evidence. The frozen scoring rule is in
`preregistration.json`; because no model output was produced, no score applies.

The first CLI invocation failed locally because the prompt was parsed as
additional stdin after the variadic `--image` option; its event stream has no
started thread. The corrected invocation started one model turn, but the
service rejected the response schema with HTTP 400 `invalid_json_schema`
because this endpoint does not permit `oneOf`. The retained event stream is
`calls/run-02/events.jsonl`. There is no completed turn or usage receipt;
`usage_receipt: null` means unavailable, not zero. The CLI was Codex CLI
0.160.0 on Windows with the logged-in ChatGPT account; model and effort were
requested as `gpt-6.1-sol` / `medium`.

The preregistered allocation allowed one started attempt and no retries. That
attempt is spent. This construction/setup rejection is not evidence for or
against visual-grounding capability. A corrected schema would be a distinct,
prospectively frozen preflight with an explicit changed-method record; it must
not be treated as continuation of this allocation.

`audit.json` contains the machine-readable disposition. `sha256.json` records
the retained input and raw-call bytes for readback verification.
