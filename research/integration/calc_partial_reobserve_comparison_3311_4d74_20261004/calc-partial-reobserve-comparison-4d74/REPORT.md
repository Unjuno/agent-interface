# G17 ordinary image reobservation versus text-only recheck

Disposition: PASS_SCOPED_USER_IMAGE_REOBSERVATION; HOLD_LIVE_ADOPTION.
Four fresh contexts ABBA text/image/image/text, two model turns each. First
tool interaction identical: explicit partial text, successFalse, same actual
retained G14 screenshots. Second prompt identical; only image arm also supplies
the exact final PNG via ordinary localImage user input. No fresh GUI/input.

First answers: cases0/2/3 falsely report unexecuted row3=31/43/1333; case1
accurately reports first row and unexecuted second inputs. Preserve all failures.
Second answers: image cases1/2 accurately report headers,23/41/943 and blank
row3 onward (case2 repairs its first false report). Text cases0/3 incorrectly
say row2 onward blank. Correct final reports: text0/2, image2/2. This is small,
known-scene evidence, not broad efficacy, proof of internal ingestion or live
adoption. It supports a prospective ordinary-image fallback test; do not silently
regrade G14/G15/G16 or discard first answers. Original live allocation not replayed.

Independent WSLc saved-transcript auditor checks first tool reply/image digest,
two turn requests/completions, second input presence and exact PNG hash, final
usage custody; AUDIT_V2.json errors[]. First audit failed FileNotFoundError
because pathlib.Path treated retained Windows path as Linux filename. Preserve
audit.py and FIRST_AUDIT_FAILURE.txt; distinct audit_v2.py uses PureWindowsPath
on saved data only. No model/native rerun. Primary semantic scoring separate,
not blinded external assessment. Image delivery is not internal attention proof.

Two-turn cumulative model totals: input162323/cached118016(subset)/output1361/
reasoning769(subset)/total163684. Individual usage and host wall in SUMMARY.json.
Both arms incur an additional model turn; no causal cost ranking. Image case1
input80368 versus case2 28118 despite same offered PNG remains unexplained.
Primary construction context cost unknown. Original CLI/source hashes frozen.

Existing host authenticated endpoint; no credentials copied. Audit WSLc image
86edd8e13599b0e4e035b5865e4fee340740d349308a2a24a1304aa1cb41dde2,
networknone/requestedCPU1/memory512MiB/user65534:65534, swap-limit warning observed.
No effective cgroup readback captured, so enforcement uncertified. The first
observer/script failure is retained separately from model reporting outcomes.

Also retain POSTRUN notification-order diagnosis of G15/G16: all eight last
usage totals precede turn/completed and match reported totals; tool completion
retains inputText/inputImage in every case. This excludes missing final usage
in those retained traces, not every possible model delivery fault. First ephemeral
inspection TypeError from null started contentItems is disclosed. No model replay.

Next: use ordinary current-image handoff as a prospective fallback in new live
partial execution, test final report and saved effects, and measure all extra
model boundaries before any integrated efficiency claim. Full ROADMAP remains open.
