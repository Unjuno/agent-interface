# A12 pre-run freeze: Issue #59 two-key dual-release loss

Run ID: a12-two-key-dual-release-loss-20261008
Issue: #59
Main base: 6c153c298ce551b24dc2f0ab645ee54c655217d8
Source closure: 712a71b25dc024b5406b24b568225c0663e7278b; 21 files; source-manifest SHA-256 bf7b2d911854cb6fdaabedabdb853bb2fc3bffd5049b3f4c8e5b3c1355a4222a
Candidate SHA-256 after test-input-only transformation: bc69c79cdcaee1e1a95c0e3cbbabe10afd4344b3661f3905c1b2e6142759a535

H: If the first XTest KeyRelease is silently dropped for both keys in one two-key UP batch, the owner keeps each identity joined to its own receipt, retries each still-down key independently, and terminates with both server-side keys released.
T: One normal arm and one treatment arm; each submits F8/F9 DOWN then ordered UPs. Treatment drops first KeyRelease for codes 38 and 39 exactly once. Require two ordered receipts, exact key/keycode identity, two attempts per treated key (down after attempt 1; up after attempt 2), verified terminal release, and empty final fake keymap.
D: PASS only if every auditor predicate and source hash matches; otherwise preserve FAIL/STOP with raw output.
C: Distinct from A09 one-key loss and A11 F9-only loss.
U: Fake-X state is not physical keyboard state or application consumption. This cannot establish live threat response, useful feedback, bounded recovery efficacy, or MAP01 outcome.

The 21 production source files are copied under source_snapshot/ from 712a71b25dc024b5406b24b568225c0663e7278b and Git-blob/SHA-256 checked against source-manifest.json. Candidate derives from retained A09 runner; only fake key mapping, two-key sequence, dual-drop injection, and run identifiers change. No candidate or auditor invocation has occurred at this freeze.

Reproduction from this directory with Python 3.12+ and Pillow:
PYTHONDONTWRITEBYTECODE=1 A09_ROOT=source_snapshot A09_OUT=results python3 -B candidate.py
PYTHONDONTWRITEBYTECODE=1 python3 -B audit.py
PYTHONDONTWRITEBYTECODE=1 python3 -B test_audit.py

No model, GUI, game, OS input, or live allocation is part of this construction.
