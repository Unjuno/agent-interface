# Primary use of opt-in report references

The primary agent used the existing public MCP `compact=true, report_refs=true`
route in one private Docker Xvfb/Tk session. It viewed the initial image, authored
one bounded dispatch, read the v3 response and its image, and declared visible
`refs-83` / `saved:refs-83` completion before reading the fixture's saved effect.
The declaration and saved effect agree; input release was verified. The full
report was directly accessible in the same response at `receipt.source.raw_report`.

One subsequent read-only lookup requested the normal v1 format for comparison.
Expansion of the original v3 receipt exactly matches v1; PNG bytes and outcome
summaries match. All six retained call files remain unchanged. There was one
initial observation, one dispatch, and one lookup; no input replay. The lookup
was a verification step, not necessary to resolve the v3 reference.

Canonical receipt JSON sizes were 9366 bytes for v1 and 5154 for v3 (about 45%
smaller). This excludes images, MCP envelope and transport formatting. No actual
model-input tokens, cost, first-useful-feedback latency or speed comparison were
measured. Existing synthetic cost research PR #4414 was read as context, not
independently re-audited or promoted. Defaults and execution semantics stay unchanged.

## Local compatibility check

Before live use, all 11 report.json inputs from the named retained MCP and two
Calc bundles were projected in three modes (33 rows). All reconstructed exactly
and preserved outcome summaries. Total canonical receipt JSON was 79508 bytes
for plain or compact-only and 44933 for report_refs. This convenience sample is
not a balanced benchmark. It reads archive members without extracting or running
them; no GUI, image conversion, model or provider was invoked.

## Scope and provenance

Live source revision was `09caefb54475808c196794e058717f4d28981bd1`; source closure,
hashes, owner and plan were saved before launch. This contains the persistence
implementation subsequently merged in #4494. The SDK client is a mediator for
primary decisions, not a second agent. This is not a host-registered tool call.
The caller asserted source/binding 1/0 and the owner set a 10-second monotonic
deadline immediately before dispatch; no server-issued freshness is implied.
No disconnect or storage fault was injected. The owner/container exited 0;
tracked Tk and Xvfb exits were -15 and 0, not general descendant cleanup proof.

The evidence archive retains all local plan, source, decision, response, image,
effect, checker and result files. Original absolute paths refer to the allocation.
The post-run PROCESS_EXIT record explicitly identifies when it was recorded.
The new tool-description guidance was added after this use and was not present
in the live session. This evidence does not measure the effect of that wording.

Run the read-only consistency check from the repository root:

```sh
python runtime/results/mcp-report-refs-use-01/verify.py
```

It reads the archive without extraction or execution and verifies hashes plus
saved comparison evidence. It does not repeat the live task, turn a primary
declaration into independent evaluation, or close the broader desktop integration
and matched-baseline requirements.
