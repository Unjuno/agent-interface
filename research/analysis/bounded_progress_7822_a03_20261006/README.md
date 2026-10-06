# Issue #7822 A03 — controllability-closed bounded-progress cross-check

**PASS_FINITE_CROSSCHECK_SCOPED. No runtime promotion.**

One prospectively frozen supplied-Linux-container allocation tested the exact unchanged A02 candidate on 2,405 new graphs. The candidate and separate stationary-policy/cycle auditor each executed once and exited 0; both stderr files are empty. No formal retry, replacement, exclusion or post-freeze source change occurred. Original A01/A02 and their results are untouched.

## Results and interpretation

| Measurement | Observed graph count |
|---|---:|
| All graphs and complete returned policy layers | 2,405 |
| Finite bounded policy proposed | 68 |
| No finite bound; SAFE_YIELD | 2,337 |
| Bound/policy disagreements against independent oracle | 0 |
| Filtered diagnostic true, no compliant nonblocking supervisor exists | 96 |
| Filtered diagnostic false, a compliant supervisor exists | 1 |
| Compliant nonblocking possible, no finite sure-progress bound | 36 |

The diagnostic rows are different predicates, not disjoint bins or failure probabilities. Twelve effective well-formed copied-record mutations were rejected, with original rows passing and changed bytes/hashes retained. Ten preformal unit tests passed; the initial stub's seven expected failing assertions and all construction records are preserved.

The subject's `nonblocking_baseline` first removes unsafe/unobserved edges, then asks whether every reachable state has some goal path. That filtered graph can discard mandatory uncontrollable events. It also enables every remaining controllable edge, including avoidable dead ends. Therefore it is neither a sufficient nor a necessary test for existence of a compliant nonblocking supervisor. It remains a legitimate graph projection, and the bounded solver itself correctly handled all new inputs.

**Witness G0078:** q0 -> q1 is safe C; q1 -> q0 is unsafe U; q1 -> goal is safe C. Filtering out the unsafe U produces goal reachability, but an implementable supervisor cannot disable that U. The bounded solver yields.

**Witness D3:** one safe controllable edge reaches goal and another reaches a dead end. Disabling the optional dead-end edge gives a valid one-step policy, despite the filtered all-enabled graph not being nonblocking.

**Witness G0064:** a safe uncontrollable return from q1 to q0 can prevent termination indefinitely despite a goal option at q1. Nonblocking possibility is not all-path bounded progress; no fairness was assumed.

## H/T/D/C/U

H: unchanged synthesis agrees with an independent complete stationary-policy oracle; filtered coaccessibility differs from achievable safe/evidenced nonblocking control.

T: 2,401 graphs exhaust four directed slots with seven absent/type/safety/evidence choices, plus four directed boundary controls. Goals are terminal; horizon cap is three events. All public graphs and full candidate results are retained, not regenerated summaries. Auditor independently reconstructs input membership by base-seven arithmetic, enumerates all C subsets while preserving every U, and checks reachable compliance, coaccessibility, cycles, longest paths and every policy layer. It imports no candidate/runner/generator.

D: all 2,405 records, source identities, observed role exits and policy checks pass; errors empty and all 12 mutations rejected. No completion or action authority is emitted. Scientific scope and publication/CI status remain separate.

C: fully observed honest complete graph, correct evidence flags, terminal goals, finite event-step game and memoryless sufficiency as proved in PROTOCOL.md. The independent algorithm shares the declared model assumptions, not candidate code. Same-author separate implementation/process is not independent human review.

U: no GUI, model/provider, task effect, native input, learned markers, partial observation, unknown transitions, wall-clock deadline, release safety, speed/token benefit, natural failure rate or production claim. Linux x86_64 / CPython 3.13.5 / stdlib in the supplied execution container; no Docker/OrbStack/WSLc image attestation, GPU/shared Engine, install or experiment network.

## Exact chronology and evidence

Intake main: a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028.
Source subject: A02 PR #8228 head 7c6f599cf250e7991f2115ccc5911d26cf53e7cb, candidate blob 32f363f8dac04b66fb02eb65d91901ac03c0cfef.

Issue #7822 ownership comment6014242656 preceded construction completion. Complete source archive plus exact FREEZE and candidate were published at commit44a105f4657b955d46ad72ca905632a87d0694a8 and read back before freeze comment6014596046 and either measured role. Candidate began 2026-10-06T10:46:23Z; auditor began 10:46:37Z. First result comment6014613895 preceded result packaging.

- FREEZE SHA256: 9ff4c5ca178bb49232dbb6c5161af07ed019d5554ba74b77f048e6156a9368c5 (21 pins unchanged).
- Full raw compressed SHA256: a55917a540eacd6ccdbe58f2aeb98b79913d60837779984930dec7ef7966cfb3.
- Audit SHA256: 2d76c2e5be814d46adae81bb75e6e9659e5f0a51b85a07f8203e2786905eef63.

SOURCE.part00..02 retain 22 exact source/freeze/construction members. RESULT.part00..04 retain nine exact result/consumption-marker/actual-exit/stdout/stderr members. ARCHIVES.json binds every original file and archive byte. Together they preserve all31 original files /71,137 member bytes; RAW.jsonl.xz contains all2,405 observed graph/result rows. Readable subject, independent oracle, audit summary and execution receipts accompany the archives; full auditor and protocol sources are in the source archive. Hash binding is integrity, not authentication.

## Read-only verification

From this directory with Python3.13 stdlib:

```sh
python -S -B verify.py
```

It restores into a new temporary directory, checks all31 member hashes and21 source pins, verifies actual role exit/output receipts, runs only the saved-data auditor and ten unit tests, and requires byte-identical audit output. It never invokes run.py or invoke.py and never repeats the candidate. Preserve consumed markers. Archive/destination parents are trusted and quiescent; this is not an adversarial filesystem sandbox.

## Integration decision and remaining work

Use distinct names/contracts for filtered graph coaccessibility, existence of a controllable nonblocking supervisor and a finite all-path progress bound. Do not infer an application milestone from any of them without independent task evidence. This contributes method evidence to #7822/#5550; #57/#59/global ROADMAP remain open.

Only this additive namespace changes. Applicable exact-head CI and scoped independent review remain required before main merge. No previous branch is deleted and no independent approval is asserted. The authoritative result document here is this README; complete proof and original prospective contract are PROTOCOL.md inside the source archive and its readable copy.
