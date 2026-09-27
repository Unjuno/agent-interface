# Issue #4666 — pixel versus normalized source-coordinate outputs

This isolated successor tests whether coordinate units, rather than visual
presentation, contributed to the out-of-frame localization proposals in
`target_localization_encoding_v1/formal/001/`. Both arms receive byte-identical
RAW images. Only the instruction for interpreting `x,y` differs:

- `PIXEL`: source-image pixel coordinates.
- `NORM01`: normalized source coordinates in `[0,1]`, converted after response
  capture to pixels by multiplying `x` by 639 and `y` by 479.

It remains a static proposal experiment: no GUI input or click is sent. The
prior allocation's raw records and HOLD disposition are unchanged.

See `PROTOCOL.md` for the frozen H/T/D/C/U and gates; `FREEZE.json` for exact
source/model/image/seed identities; and `formal/001/` for raw formal output,
independent audit, and final report after execution.
