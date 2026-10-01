# Successor allocation 02 — auditor row-order repair

## H / T / D / C / U

- **H:** The candidate's minimum-feedback result can be independently checked without false failure when semantically identical transcript partitions are serialized in a different order.
- **T:** After the predecessor's candidate/auditor pair each ran once, the raw-only audit failed because partition rows were ordered differently. A new allocation pins the unchanged candidate/input bytes and a separately versioned auditor with canonical partition ordering. The candidate is invoked once to a new output path; the v2 auditor independently enumerates and audits once. Zero retries.
- **D:** `PASS_HOST_CONSTRUCTION_ONLY` requires the v2 raw audit to agree on the exact minimum channel set, decisions, partition content and oracle labels for both positive/null controls. The predecessor FAIL remains immutable. This is not the issue's container T0.
- **C:** This corrects order-only sensitivity in a small authored fixture; it does not validate the task oracle or establish external validity. Candidate/auditor are separate code paths but share frozen cases.
- **U:** No general GUI feedback lower bound, live safety, task effect, model-call bound, or production result is claimed.

The prior allocation's raw output is retained at the parent directory and never reused as this allocation's result. The successor has separate candidate/audit output names and a new allocation ID.
