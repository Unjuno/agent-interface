# Actual replacement of visible pre-existing browser input

The existing browser form fixture starts empty. This new test-only variant
starts its autofocus Value input with old-draft-42 and a visible instruction to
replace the draft. The server stores the submitted request body and has no
expected answer. Ordinary post-controller evaluation still checks the requested
token. Socket v11, runtime v27, admission, image delivery and scoring are unchanged.

The assistant inspected the initial browser image, navigated to the local URL,
and inspected the form image selected by receipt_image.py. The visible input
contained old-draft-42. The assistant then chose Control+a, typed t991029 and
pressed Return. This differs from the earlier empty-form sequence by the
selection step. No DOM, saved-output read or hidden oracle selected the input.
The outcome_client.py CLI received evaluated=true with only value=t991029 saved.

| Metric | Measured |
|---|---:|
| First capture to outcome client return | 52.626 s |
| Form socket return to replacement admission | 14.672 s |
| Navigation / replacement local program | 850.901 / 380.787 ms |
| Outcome client wait | 184.588 ms |
| Terminal to independent evaluation emission | 14.628 ms |

Two programs, one submission, one clock and one outcome read were used; no
fallback status query was necessary. Audit verifies twelve exact frames, saved
request contents, request/program lineage, the full 22-record received prefix,
release after both programs, no rejection or duplicate submission, and the
historical terminal timestamp's bounded confirmation deadline. The process
exited zero after cleanup. Initial/form images were both opened at original
resolution through their received references. Form sequence 9 referenced
005.png; no prior-run index was assumed.

This was an intentionally prepared draft fixture, known to the assistant, not
an unexpected failure or proof of general recovery. It establishes one actual
visual replacement decision and successful end-to-end result. There is no
no-selection control, blind held-out trial or matched speed comparison; do not
claim how often a fixed empty-form policy would fail. The 14.672-second outer
decision interval remains far above the local input duration. Actual model
receipt times, token costs and a comparable human baseline remain unmeasured.

Evidence: results/prefilled-self-use-01 and results/prefilled-self-use-audit.json.
The fixture wrappers, audit, client and transport hashes are recorded separately
from the unchanged runtime source manifest. No default promotion. Next use a
case where the required selection/focus repair is not announced in advance,
and record its visible decision point and correction cost without omitting
failed attempts. Keep this as desktop coverage, not an FPS-oriented benchmark.
