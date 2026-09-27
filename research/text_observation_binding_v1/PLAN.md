# Text observation binding v1

H: an exact-prefix string alone is insufficient authority for suffix recovery; freshness + binding + target + focus must remain valid.

T: private authenticated Xvfb/Openbox, two real Tk entry targets, intended `bookkeeperoffice`, stops 3/5/8/12/15, six observation conditions, two policies = 60 trials. Conditions: fresh same-target, stale sequence after mutation, stale binding after mutation, wrong-target observation, expired observation after mutation, and focus-changed after observation. `content_only_prefix` checks only text prefix. `bound_prefix` additionally requires exact sequence/revision/target identity, age <= 100ms, and current focus == expected target. Refusals emit zero recovery input.

D: bound policy must recover all 5 fresh cases exactly and refuse all 25 fault cases with zero recovery key events. Content-only negative outcomes are retained as measured and are not task success. Keymap unchanged; physical input empty.

C/U: fixture IPC is an exact research oracle and supplies authoritative metadata for the experiment. Real Office/AX/OCR/DOM observation freshness/identity remains unproven; no rollback, Unicode/IME, 3OS, model/token claim.
