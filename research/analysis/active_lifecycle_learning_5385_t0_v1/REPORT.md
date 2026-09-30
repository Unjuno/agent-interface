# Issue #5385 T0 — bounded active lifecycle discovery

## Disposition

**PASS_BOUNDED_DISCOVERY_ONLY.** The one frozen host-CPU learner run recovered six observational DFA states, with all four named lifecycle states distinct. Its candidate was equivalent to the declared target under exhaustive BFS of the finite target/hypothesis product. The intentionally coarse hand suite matched a mutant that allowed compensation from stale state; the shortest unsafe acceptance absent from that suite was EBP. The separate raw-only auditor reported zero errors and rejected all four corruption controls.

This is a deterministic synthetic oracle result only. It is not a live lifecycle discovery, safety certification, or runtime/product result.

## H/T/D/C/U

- **H:** A membership-query learner with counterexample refinement would separate the four safety-relevant states and expose a false acceptance missed by the hand-authored examples.
- **T:** Standard-library-only L*-style observation table; six-state complete target DFA; finite product BFS equivalence teacher; four baseline traces; one independent raw-only audit and four mutations.
- **D:** The preregistered PASS gate was met: six learned states; lifecycle prefixes V/T/H/P map to four unique learned states; 187 membership queries; 3 equivalence queries; counterexamples EC and ERBP; 18 product pairs checked across equivalence queries; zero mismatches; shortest baseline-mutant false acceptance EBP; audit errors=[]; 4/4 mutations rejected.
- **C:** A complete explicit schema/test suite may distinguish these states more cheaply; the baseline hand suite is deliberately small and not representative of repository-wide coverage.
- **U:** The oracle and all transitions are hand-authored and deterministic. No nondeterminism, noisy teacher, instrumentation, actual interface, authority effect, performance, or population representativeness is tested. The DFA learner is exploratory, never authority.

## Frozen provenance and execution

- Freeze/intake main: bbeee4da02285281e960334f8babefc2d7070358.
- Main advanced before the run to b0190453a787102189429e4b8c32032cf60efd17. That commit updates the generated analytical index and adds Issue #5329 evidence; it does not modify this frozen package or its inputs. The experiment is self-contained.
- Exact GitHub-readback sources and SHA-256 are in FREEZE.json and RESULT.json.
- Construction: 7 checks passed before the run.
- Host: Windows local, CPython 3.11.9. C: had 0 bytes free; no files were written. Frozen Python bytes were compiled/executed from memory with -B.
- Learner command shape: py -3 -B -c <exec exact base64-decoded learner.py bytes>.
- Audit was a second CPython process, with audit.py reading only the retained raw JSON supplied on stdin.
- Invocation counts: learner 1; auditor 1; retries/tuning 0.
- No Docker/OrbStack CLI or container was invoked. The current #5085 coordination comment explicitly bars further Docker CLI calls without exact assignment/release, and there is no #5385 lease. This host-only substitution is recorded as a resource-bound deviation, not container evidence.

## Retained raw evidence

- raw.json SHA-256: 6b10540abad66c336e5ce446045ebc716043824b06aab7da75a293dc2cce4037 (1226 bytes).
- audit.json SHA-256: 576ffa597f3de6841b5c6cdfd020557d63e29912da72c363081b57a620e21ab4 (126 bytes).
- Learner output: 6 hypothesis states; V/T/H/P all distinct; false accepts/rejects 0.
- Independent audit output: PASS_READONLY, errors [], mutations 4/4 rejected.

The successor experiment should use an instrumented, sandboxed interface oracle with unknown transitions and explicit UNKNOWN/nondeterministic outcomes. No learned state or inferred transition may authorize effects.
