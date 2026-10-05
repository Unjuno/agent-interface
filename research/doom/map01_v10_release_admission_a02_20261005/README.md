# V10 failed-release admission boundary A02

## H / T / D / C / U

- **H:** After an input owner's terminal release remains physically unverified, its retained lease identity prevents a later lease from injecting another key.
- **T:** Run the same four-case fake-X suite once against current-main V10 and once against PR #7962's retry candidate, under Python 3.12 in normal and optimized modes. The added case holds key A, suppresses every KeyRelease, requires terminal release to raise, then attempts key B under a different lease. Preserve the first output for each source/mode; no retries.
- **D:** The safety case passes only if the second lease is rejected before key B appears in fake physical state; persistent release remains unverified. Candidate retry cases must also pass. Baseline differences in the pre-existing retry tests remain visible.
- **C:** One CPU, 512 MiB configured, network disabled, Python image pinned by digest. The fake X display does not establish real X server behavior, physical state, application consumption, or game effect.
- **U:** This is a control-boundary construction check, not a V39 live threat exposure, independently useful feedback, recovery efficacy, MAP01 progress, or proof of safe real input. The #59 live-game lane remains unassigned.

## Result

The one-shot WSLc matrix completed without retry. On the current-main V10 source, the new persistent-failure admission case passed in both modes: after release verification failed, a different lease was rejected before key B entered fake physical state. The two earlier repair cases retained their expected baseline error/failure (dropped explicit key-up remained down; an untracked wheel-button release remained down). This baseline result is `1 failure, 1 error` across four tests.

On PR #7962's V10 candidate, all four cases passed in normal and optimized Python. The newly added case confirms the failed old lease remains active and blocks the new lease's key-down; it does not establish a physical X server guarantee. `audit.py` checks both pinned source copies, identical test bytes, and all four raw records.

The candidate is bounded component evidence for a fake-X owner. It does not establish V39 runtime integration, real X11/physical key state, app consumption, useful feedback, recovery efficacy, a threat response, MAP01 progress, or the #59 live gate. No live allocation was used.
