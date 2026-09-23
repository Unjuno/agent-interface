# XTerm XTEST -> raw PTY delivery construction

Issue #1539. Construction-only; formal0 by design.

Disposition: PASS_XTERM_XTEST_RAW_PTY_DELIVERY_CONSTRUCTION.

## Finding

The deterministic route is:
1. launch stock XTerm with the raw-PTY helper;
2. wait for the helper READY side-channel after tty.setraw();
3. focus the XTerm top-level window;
4. read back GetInputFocus and require exact target equality;
5. inject one XTEST x press/release with 8 ms hold.

The first top-level discovery session delivered exactly byte 0x78, global X key ended UP, and XTerm/helper exited0. Two fresh confirmation sessions using only this rule also passed 2/2.

Mapped hierarchy after READY contained the top-level plus one viewable descendant. Descendant testing was not consumed because the first frozen candidate rule passed.

This isolates the #1537 construction failure: window mapping alone was an insufficient readiness condition. #1537 sent input before proving the raw PTY helper was ready; its semantic-effect hypothesis remains untested.

## Integrity
- result SHA-256: 0d4c201d004cc234118f06fbfe6b7b8d38643ddde668da0e3a33c18fb78f7352
- experiment source SHA-256: 0b010c45ec8b9f5bf74215a1016592894a678d37dc18796f56bb36726ad5511b
- helper source SHA-256: ec83c0e2cd3be6f7d5a93135467e4f8cd30e2dd662085587aa38661ab68e96dc
- local git hash-object values at construction: experiment 58bfa9254f10c322994a94646cb15364c97f2c72, helper 87ba88edec2c878c8043795361c909823b91bfac, raw result 3150bcc0056c38898a8e5b5f3fb982799764bfa3. Only helper.py is retained byte-for-byte in this branch; the experiment hash identifies the disposable construction harness rather than a published GitHub source blob.

Scope: private Xvfb/XTerm only. This proves a harness input route, not semantic-effect handback or general application control.
