# Standalone cross-platform doctor artifact v1

Task `RUNTIME-STANDALONE-DOCTOR-V1-20260917-001`, Issue #600.  
Integration base `5970859ba4bf9f4109b45f63ee0981386349de46`.

Decision: **`PASS_CROSS_PLATFORM_DETERMINISTIC_STANDALONE_DOCTOR`**.

The builder copies a closed enumerated set from promoted `runtime/core_v1` and
`runtime/interface_v1`, adds only deterministic bootstrap files, and writes a
ZIP_STORED Python zipapp with fixed 1980 timestamps and fixed Unix file mode.
No research tree, native backend dependency or generated cache is included.

## Local construction

- two consecutive builds are byte-identical;
- artifact bytes: **28,913**;
- artifact SHA-256: `5fc7b440553f96d77b757e1b1ad5ded8961af7ab742b528c27d91b51085a9e05`;
- exact 12-entry archive closure verified;
- `python agent-interface-doctor.pyz` executes successfully;
- emitted doctor keeps `support_claim=false`, `ready_for_side_effects=false`,
  `input_authority=none`, `capture_authority=none`.

## Cross-platform integration finding and repair

The first Ubuntu/Windows/macOS Actions matrix retained one integration failure:
Ubuntu and macOS produced the frozen artifact, while Windows built a different
29,640-byte artifact because worktree newline conversion changed Python source
bytes before packaging.

The repair changes only distribution provenance:
- in a Git checkout, the builder reads each packaged source from exact
  `HEAD:<path>` Git blob bytes;
- the verifier compares the archive to the same committed-byte definition;
- non-Git test fixtures retain filesystem fallback;
- a regression commits LF source, rewrites only the worktree copy to CRLF, and
  requires `_source_bytes()` to return the committed LF bytes.

No `runtime/core_v1` or `runtime/interface_v1` source or semantics changed.

Final Actions run `35124442335` at head
`df96b8e6ca0745370387e4bae383a85063bef98c` passes on
**ubuntu-latest, windows-latest and macos-latest**. Every job passes compile,
distribution tests, artifact build, exact verification and standalone execution.
The Ubuntu upload artifact is `10458089252`; its Actions ZIP digest is
`3cac35bef04b362ef8bb2007bdc2307bcec14347c57d33bae52698214501697f`.

An independent disposable-container readback of that uploaded artifact verifies
`SHA256SUMS`, executes the `.pyz`, and again observes no capture/input authority.

This artifact is a bootstrap/diagnostic distribution, not the Golden Desktop
Research Preview and not a native automation support claim. Native effect
backends remain separately promoted under Issue #564.
