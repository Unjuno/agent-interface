# Admission deadline and semantic effect identity

Status: independently reviewed analytical counterexample and conditional repair. No policy function,
historical allocation, new matrix, GUI, model or experiment has been executed.
Project runtime acceptance remains HOLD_REAL_TARGET_BOUNDARY_UNTESTED.

## H/T/D/C/U

- H: If deadline_ms is solely proposal admission metadata, including it in an
  effect key permits multiple simulated effects for one supplied semantic opportunity.
  Dropping only that key component repairs this narrow counterexample without
  weakening the existing per-proposal deadline check or conflating time-dependent effects.
- T: Source inspection and induction on the existing sequential state machine,
  plus six independently authored literal two-proposal witnesses in WITNESSES.json.
  These are predictions/proof obligations, not observed run output.
- D: Accept only a scoped analytical conclusion if independent review confirms all
  six literal derivations, identical admission gates and the one-component key delta.
  Reject on a counterexample within the assumptions; HOLD if identity/observation
  assumptions cannot be established. No empirical allocation is necessary to
  decide the conditional theorem. No historical verdict is changed.
- C: If deadline represents an effect's temporal meaning, it belongs in semantic
  payload and deleting it there is wrong. Existing content-bound shared-work-ID
  admission can encode the same semantic tuple, so this does not require a new ledger.
- U: Supplied identity/currentness/completion, sequential atomic effects, no lost
  feedback, no parallel race, durability, actuator timing, latency or GUI transfer.
  Hash equality is treated as collision-free on the declared six inputs, not a
  general mathematical injectivity guarantee. No project-level runtime acceptance.

## Source and minimal candidate

Baseline is SEMANTIC_EFFECT_COALESCING from merged #5338, commit
ff93fdb5b6b1740d85a79e79764e9dc7789831fe, path
research/experiments/action_effect_coalescing_5265_v1/experiment.py.
Git blob fa1d6d4edc4c83e6b515586f1aa4f111653658b8 is unchanged at intake main
a1d0d0290b8619902d34b13d9e536c4bde063f74.
The copied file is documentary source, never imported or executed here.

Let S be the ordered nine fields intent_revision, state_generation, target_id,
target_incarnation, operation, effect_class, effect_opportunity,
expected_postcondition, parameters. Baseline key is SHA256(JSON(S, deadline_ms)).
The minimal conceptual candidate key is SHA256(JSON(S)). All other statements,
including validation, retry handling, completion and group bookkeeping, are unchanged.
In source terms delete only the `"deadline_ms",` entry from IDENTITY_FIELDS.

This is a specification delta, not an applied runtime patch. A group's stored
deadline_ms remains the first executed proposal's deadline; it must not be read as
authority, the later member's admission bound, or a renewed lease. Such a
production group-receipt design is outside this proof.

## Contract and equal treatment

Inputs are well-formed proposals with distinct producer/proposal IDs, no retry_of,
verified target/opportunity identities and integer now_ms/deadline_ms. Each arm
rejects exactly now_ms >= deadline_ms BEFORE completion or key reuse. Deadline is
valid strictly before its bound; equality expires. The admission point is a
synthetic proposal visit, not a precommit/physical-effect deadline or lease.
This matches #5338 and deliberately does not assert equivalence with other
contracts using a different boundary, or with #5371's retained construction.

Semantic identity means one desired occurrence in one verified opportunity. The
proposal deadline only limits whether that proposal may start; it does not make a
new opportunity, renew an expired proposal, or prove that an effect happened.
Temporal meaning (for example SCHEDULE_REMINDER's deliver_at_ms) is included in
parameters and expected_postcondition, independently of admission deadline_ms.
An unknown distinction between admission time and effect meaning requires YIELD;
this proof does not supply an open-world semantic classifier.

## Inductive argument

For either arm, admission-failing visits do not mutate executed or groups.
Likewise already_satisfied=True produces NO_ACTION and does not reserve a key.
For eligible, unsatisfied, complete proposals, the first occurrence of a key
adds exactly one executed entry and one EXECUTE. Every later occurrence of that
key appends membership and produces COALESCED, with no second EXECUTE. By induction
over visits, executions equal the count of distinct eligible unsatisfied keys.

Under the declared admission-only contract, two eligible proposals with equal S
are the same intended effect regardless of their deadlines. In the declared
both-valid witness, independently checked hashes distinguish the baseline keys
when deadlines differ and therefore yield two EXECUTEs; the candidate
has one key and yields one. Removing deadline cannot admit an expired proposal:
the identical earlier rejection branch is independent of either key. An expired
first proposal cannot poison the key because it reserves nothing. The declared
new-opportunity witness changes S and its checked hashes remain distinct.
Verified completion dominates key
reuse and produces NO_ACTION even after an extended deadline. Changing an actual
temporal parameter changes S and its checked hashes remain distinct in the
declared reminder witness. Universal semantic-tuple distinctness additionally
requires injective canonical representation and collision freedom on the chosen
domain; only the induction over keys is unconditional on hash distinctness.
These conclusions follow without executing a simulator. Dropping deadline's
identity-validation check is harmless here because preceding exact-integer
admission validation already excludes None and empty-string deadlines.

## Six independent literal witnesses

WITNESSES.json supplies the complete defaults, exact proposal overrides and
literal expected decisions/effect counts for both arms. Its expected section
was authored from the contract above, not by importing or calling a candidate.
Both-valid deadline-only pair: baseline 2, candidate 1. Expired-first/valid-second:
both 1. Both expired: both 0. Verified new opportunity: both 2. Completed opportunity
with extended deadline: both 1. Different reminder delivery times with the SAME
admission deadline: both 2. The last is a counterexample to stripping temporal
meaning out of semantic payload, not a test of a real reminder scheduler.

These witnesses describe six fresh proof obligations; none modifies, reruns or
relabels #5338's frozen same_effect_different_expiry result or #5371's construction.

## Overlap and execution boundary

At 2026-09-30 10:36–10:37 UTC, GitHub MCP read latest #5265 comments, PR queries
5265/deadline/admission+identity, and branches matching 5265/deadline. Only #5338
and #5371 cover this issue; no deadline-identity successor was found. This cannot
exclude unpushed work. No repository writes, push, PR or CI launch occurred.

Host inspection: CPython 3.12.14, Linux 6.18.44 x86_64; allowed CPUs 0..8.
Nested Docker is unavailable by task context. There is no pinned Docker image or
real-GUI validation claim. Preparation used file writes, source reads and metadata
inspection only. Any optional future verification is bounded to one CPU process,
256 MiB address space, 30 seconds, no network/model/GPU/native UI; it requires the
parent's source freeze and invocation approval first. The analytical deliverable
does not spend the proposed evidence allocation.
