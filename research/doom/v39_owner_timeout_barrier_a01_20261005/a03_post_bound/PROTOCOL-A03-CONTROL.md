# A03 post-bound delayed-release control supplement

## Purpose and relation

A03 v3's candidate arm followed the frozen schedule and is retained at `results/a03_v3/RESULT.json`. Its baseline arm reached the finalizer before the 1.75 s timer opened the gate; the finalizer's unconditional emergency gate-open made the recorded baseline schedule differ. This supplement executes **baseline only**, with the same 1.75 s timer and a 3 s post-terminal owner-stop observation so its final owner record can be captured. It reuses (does not rerun) the already executed A03 v3 candidate arm when printing the assembled pair.

## H / T / D / C / U

**H:** Under a shared 1.75 s post-timeout fake-gate delay, baseline emits no release row and retains F8, while the already observed candidate expires its 1.5 s wait before the gate opens, then completes physical cleanup without draining the late row; both preserve a failed/unverified terminal.

**T:** Run the baseline arm once using the A03 v3 runner with only the post-terminal observation extended from 1.5 s to 3 s. Read the immutable candidate result from `results/a03_v3/RESULT.json`; do not call its runner. Retain the baseline output separately and an assembled pair for audit.

**D:** Candidate limitation is supported if gate-open follows timeout by 1.70–1.90 s, candidate wait expires before gate-open, owner later stops with verified physical up, no candidate up row exists, bridge retains F8, and terminal remains failed/unverified. Baseline schedule is adequate only if its gate opens in the same 1.70–1.90 s window and owner stops before capture; retain exact timing and receipts.

**C:** Separate executions can have scheduler variance; compare each gate-open relative to its own timeout, and do not infer rates from one schedule. Emergency finalization still opens a gate if the owner has not stopped by capture.

**U:** Native Windows fake-display only. No real X11/OS input, game, task effect, useful feedback, recovery efficacy, safety, or MAP01 result.
