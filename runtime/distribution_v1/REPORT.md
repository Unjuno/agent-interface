# Standalone cross-platform doctor artifact v1

Task `RUNTIME-STANDALONE-DOCTOR-V1-20260917-001`, Issue #600.  
Integration base `5970859ba4bf9f4109b45f63ee0981386349de46`.

Decision: **PASS_LOCAL_DETERMINISTIC_STANDALONE_DOCTOR** pending the exact
Ubuntu/Windows/macOS matrix.

The builder copies a closed enumerated set from promoted `runtime/core_v1` and
`runtime/interface_v1`, adds only deterministic bootstrap files, and writes a
ZIP_STORED Python zipapp with fixed 1980 timestamps and fixed Unix file mode.
No research tree, native backend dependency or generated cache is included.

Local construction result:

- two consecutive builds are byte-identical;
- artifact bytes: **28,913**;
- artifact SHA-256: `5fc7b440553f96d77b757e1b1ad5ded8961af7ab742b528c27d91b51085a9e05`;
- exact 12-entry archive closure verified;
- every copied source byte matches the repository input;
- `python agent-interface-doctor.pyz` executes successfully;
- emitted doctor keeps `support_claim=false`, `ready_for_side_effects=false`,
  `input_authority=none`, `capture_authority=none`.

This artifact is a bootstrap/diagnostic distribution, not the Golden Desktop
Research Preview and not a native automation support claim. Native effect
backends remain separately promoted.
