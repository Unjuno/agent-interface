# V39 candidate preflight failure receipt A01

## Question and decision

**H:** When `verify_frozen` or `install_support` fails after the output path and freeze are accepted, the candidate should retain an incomplete `candidate.json` with the STOP reason. A failure before the backend or X11 session starts must not disappear as an uncaught exception.

**T:** Exercise `candidate.main()` with temporary output/freeze fixtures and mocked network verification or support extraction. On current-main parent `0621713407d42c5a3922572b2fe57222f175e9a2`, make `verify_frozen` raise `STOP_NETWORK_NAMESPACE:fixture`; check both the exit and retained output. Then add regression coverage and keep the same injected failure.

**D:** On the parent, the injected network STOP raised uncaught, `candidate.json_exists=False`, and the output directory remained empty. After the repair, the network and support preflight fixtures both return exit code 2, retain `candidate.json` with `candidate_completed=false` and the exact injected STOP in `issues`, and do not create `candidate_started.json`. The support-failure receipt also preserves the verified network-interface snapshot.

Executed from `research/doom/map01-v39-per-key-release-live-t0-20261004/`:

```text
python3 -B -m unittest test_candidate test_audit -v
Ran 15 tests ... OK
python3 -B -m py_compile candidate.py test_candidate.py test_audit.py audit.py
git diff --check
```

The initial parent reproduction used the same temporary freeze/output structure and yielded:

```text
raised= STOP_NETWORK_NAMESPACE:fixture
candidate.json_exists= False
out_entries= []
```

The candidate and auditor tests are synthetic construction evidence. No X11 session, input, game, model, container, formal allocation, or consumed-allocation retry occurred. This source edit changes a file covered by the historical candidate freeze; that freeze is stale for any future invocation. This result does not qualify physical key state, input release, application consumption, task effect, or current live behavior.

## Retained evidence

- Parent: `0621713407d42c5a3922572b2fe57222f175e9a2` (#8710 current-main integration).
- Candidate and focused test sources are the two changed files in this package's implementation diff; the tests preserve the two synthetic failure injections.
- Baseline discrepancy was independently observed before editing, then converted into a regression that passed with the existing candidate/auditor suite.
- Scope is only startup STOP retention. The consumed 2026-10-04 allocation remains untouched.
