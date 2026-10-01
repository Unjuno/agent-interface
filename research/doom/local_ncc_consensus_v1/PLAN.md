# Issue #4163 plan — local NCC spatial consensus

H: a fixed five-band spatial consensus can recover the authored world/background shift when a high-contrast foreground band moves differently and global NCC follows foreground.

T: deterministic 320x140 NumPy fixture; global NCC versus identical NCC per five fixed horizontal bands plus >=3-band consensus within ±2 px. Search ±240, min NCC .20, min best-second margin .02, unchanged 34 px task gate. Ten preregistered cases from Issue #4163. Construction seeds 9909xx are excluded. Formal seeds 416301..416310. Exactly one formal invocation, no rerun.

D: PASS only with >=2 global parallax task errors; candidate <=2 px error on every rigid/parallax case; rigid non-worse; unrelated/flat controls not identified; verifier/source integrity pass. HOLD if no global discriminator. Candidate error or false-control identification is FAIL.

C: foreground is authored as one high-contrast middle band and background occupies four/five bands, favoring spatial consensus; real scenes can violate that support structure.

U: synthetic only; no claim about #747 PNGs, MAP01 yaw/perspective, model/task performance, latency or production. Candidate is a mechanism probe, not a runtime promotion.
