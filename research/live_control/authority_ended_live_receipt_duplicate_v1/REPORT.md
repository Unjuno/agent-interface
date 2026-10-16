# Live `authority_ended` duplicate-receipt ledger v1

Status: **PASS_LIVE_RECEIPT_LEDGER** for one fresh model-free ViZDoom/X11 session. This closes the in-process duplicate-terminal remint failure at caller level; restart durability remains unproved.

## Question

Offline replay of an exact retained live `authority_ended` terminal showed a correctness gap: token objects were one-use, but replaying the same terminal receipt could mint a fresh token. The candidate binds token issuance to the runtime-owned `interruption.intent_token` (`authority_end_id`) in a session-scoped issued-ID ledger.

This live block changes one thing only: use that ledger in the existing two-dispatch caller and inject the **exact same first terminal receipt** once before token consumption and once after token consumption / second physical action.

## Frozen runtime

- immutable runtime source base `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`;
- ViZDoom 1.3.0 / Freedoom MAP01 / `map01-threat-contact-v2`, skill 1, ASYNC_SPECTATOR 35 Hz;
- CPython 3.13.5 / Linux 6.18.44 / shared Intel Xeon Platinum 8573C, frequency unpinned;
- private Xvfb/Openbox;
- construction smoke seed 994299 excluded;
- formal seed **994300**, one session, zero formal retries, zero model calls.

## First formal outcome

| Gate | Outcome |
|---|---|
| first terminal | `authority_ended` |
| runtime `authority_end_id` | `c2b93e1a1d884ded8dbd572b3fb0cfcb` |
| duplicate before consume | **REJECT** `authority_end_id already issued` |
| input after duplicate-before | **0** |
| post sequence → current sequence | 2 → 3 |
| revalidation | `revalidated` |
| input before second submit | **0** |
| intended second physical input | **1** |
| second terminal | `completed` |
| second release | verified empty |
| duplicate after consume/second terminal | **REJECT** `authority_end_id already issued` |
| input after duplicate-after before finish | **0** |
| total post-first-release input admissions | **1** (the intended second action only) |
| `third` ID events | **0** |
| independent five-field final scorer agreement | PASS |

The ledger's issued set contains exactly the first runtime authority-end identity and is not extended by either duplicate delivery.

### Timing observations

- first deadline → verified empty: **0.928 ms**;
- first verified empty → intended second physical input: **115.999 ms**;
- second input admission → second verified empty: **131.849 ms**.

These are one shared-host session, not distributions or hard-real-time guarantees.

## Independent audit / evidence

`audit_live_receipt_duplicate_v1.py` replays the formal result and raw event/scorer files. It verifies the first runtime identity, zero input before the intended second admission, exactly one post-first-release input admission, no third-ID events, verified second release and final scorer agreement. Local audit: **PASS**.

`compact-evidence.json` retains the exact first/second terminal receipts, every post-first-release input admission, the empty `third` event set, terminal score/direct-final independent scorer sample, formal result, and SHA-256 identities of the original raw text files. The full raw text files remain in the disposable container and are not claimed retained on GitHub. PNG/AIT visual binaries are likewise local-only and are not needed for these receipt/release/admission/scorer claims.

## H / T / D / C / U

**H.** Receipt-level issuance keyed by a runtime-owned authority-end identity prevents duplicate/delayed first-terminal delivery from reminting a second replan token without blocking the one legitimate later fresh-evidence dispatch.

**T.** One fresh real ViZDoom/X11 formal session. Inject the exact first terminal receipt before consume and after the one legitimate second action. No model calls; zero formal retries.

**D.** **PASS_LIVE_RECEIPT_LEDGER** because both duplicates are rejected, neither creates input, exactly one intended second action is admitted, and release/scorer gates pass.

**C.** The ledger is process-memory state. A caller restart loses `issued_ids`; a replay after restart can still remint unless issuance state is restored durably. Mark-on-issue can also reduce liveness if token state is lost while the issued ID survives.

**U.** n=1, one fixture/key/host, no model or useful gameplay effect. Transport duplication itself is simulated at the caller boundary; network retry stacks are not exercised.

## Next smallest experiment

Do **not** add a model yet. Test the known restart counterexample directly: issue/consume the first receipt identity, instantiate a fresh empty ledger (simulated caller restart), and replay the exact same retained receipt. The current candidate is expected to fail. Then add the smallest durable/rehydratable issued-ID journal and rerun only that restart matrix before any live restart or model-in-loop allocation.
