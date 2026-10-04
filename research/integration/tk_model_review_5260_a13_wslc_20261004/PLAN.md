# A13: model-facing first-character review

This advances open #5260's explicit observation/review and same-model recovery
cost question. It is not a replay of the original failure or A12. Historical
closed #2558 supplies a host-local Codex exec adapter precedent; its consumed
golden/model allocations are not reused. Closed #4134's journal endpoint is not
model reasoning evidence. No same A13 path/branch worker found in current main,
96 open PRs, or #5260's latest comments.

## H/T/D/C/U

H: the same image-backed model identifies a single missing first character and
chooses a precise prefix suggestion, while refusing decoy misdelivery and an
ambiguous non-prefix error. Suggestions grant zero input authority.

T: four fresh private Tk apps in the pinned WSLc image, deterministic XTest
controlled stimuli. Requested/current TARGET/current DECOY:
hqu/hqu/empty (NO_REPAIR); hvr/vr/empty (INSERT_PREFIX h);
hsn/empty/hsn (REFUSE); htm/xm/empty (REFUSE). Requested text and labelled fields
are visible on each real captured screenshot. New payloads/geometries, no prior
formal rows reused. Candidate once, host model phase once (maximum four requests,
one fresh ephemeral thread per image), independent auditor once. No retries or
post-freeze tuning. The order is fixed, not randomized or a causal comparison.

The host-installed Codex CLI 0.160.0 is hash-frozen, following the repository's
existing #2558 gpt-5.6-luna/low model configuration. Each call is read-only,
ephemeral, ignores user configuration and rules, receives the same frozen prompt
and closed output schema, and has a 90-second first timeout. Tool use, malformed
answer, missing usage, process/transport error or timeout consumes the allocation
and stops further requests. GUI candidate uses no network; cloud model review
is separately on the host, not claimed to be in the network-none container.
Existing CLI authentication is used without inspecting or recording credential
contents. No private user document, GPU or real user desktop is read.

D: METHOD_PASS_FINITE_REVIEW_ONLY requires all four app/keypress/capture/source
identities and pixel-exact XWD-to-PNG conversion, original model events, exact
prompt/image/argv/process/UTC/usage custody and independent stream recomputation.
H_PASS_FINITE_REVIEW_ONLY requires four exact literal observations and decisions;
a completed valid wrong answer is H_FAIL_FINITE_REVIEW_ONLY, not method STOP.
Missing/contradictory provenance or model transport produces STOP_AUDIT /
UNQUALIFIED. Preserve the first outcome regardless of verdict. Actual CLI usage
and call wall times are descriptive; no price, performance ranking or latency
benefit inference. Model responses never cause GUI input, Save or task files.

C: controlled first-character absence, not evidence of the original failure's
cause. Four private, cooperative, same-font screens are not a formal held-out
population or broad GUI/model capability. Prompt contains the decision policy;
this tests image-grounded application of it, not unconstrained recovery planning.
No eventual recovery success, physical release, stale-action admission, optimal
wait, human tempo, resource enforcement, OOM improvement or runtime promotion.
All broader roadmap gates remain open. Source stays local through first runs,
then batch delivery; GitHub prospective registration is not remote source readback.

U: if qualified, integrate this finite model decision/cost evidence as a research
handoff. A separately frozen next rung would combine model-suggested repair with
fresh local authority and independently scored file task effect; do not infer it
from this no-action review. If FAIL/STOP, retain and diagnose without retries.

## Non-formal preparation

Environment discovery found PIL absent from the fixed image; no installation.
Test-first XWD/response/oracle checks: initial three RED, then three GREEN.
Actual private Linux construction (hzx requested, zx emitted) was RED while
candidate absent, then GREEN; its output is temporary and not a formal case.
Two process-custody tests RED while recorder absent, then one Windows test
exposed normal newline translation in its Python test subprocess; corrected the
test's platform literal, not captured evidence. Two independent pixel/event
checks RED while auditor absent, then GREEN. Latest eight Linux tests PASS;
Windows seven PASS/one explicit Linux-display skip. No formal model request or
four-case candidate invocation occurred in preparation.
