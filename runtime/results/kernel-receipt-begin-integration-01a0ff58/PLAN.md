# Receipt-start runtime adoption, ordinary integration

Owner 01a0ff58-480b-7d50-9eee-0bce12250476, parent #5215; dependency #6892 exact d06e636a8c35715d371dc6ba00632aab4b3bad3c.

H: retaining the successful begin timestamp in #6892 permits the runtime to refuse terminal execution receipts whose start precedes that begin. The existing #6878 synthetic matrix established this boundary in an isolated subclass; this work adopts it in the real lifecycle without altering the cancellation repair.
T: add a separate test module first, retain its expected baseline failure, then change only record_execution admission. Run the full kernel discovery normally and with -O. Test valid equality/later starts, refusal nonmutation and later correction, identity mismatches, rejected/duplicate begin preservation, missing begin and cancellation. Use bounded directed source mutations to establish test sensitivity.
D: accepted typed receipt requires successful begin and receipt.started_ns >= execution_started_ns, as well as every original identity/action/release check. Before a refusal, all lifecycle fields must remain identical. Invalid begin must not set or move the successful bound.
C: preserve #6892 four runtime lines/six tests and #6853 duplicate-begin behavior; no new clock state. Do not introduce lease-expiry or end-time deadlines. Ordinary consistency PASS does not assert physical release, clock provenance, public-field immutability, concurrency, GUI/model/backend or task benefit.
U: exact pending dependency may move or fail review. Do not apply against arbitrary main; create/review a fresh fixed runtime proposal after dependency status and exact composition are known. No branch takeover, main write, formal allocation, input/GPU/container or historical producer rerun.

Bounded local output: <1 MiB, stdlib and one short subprocess at a time. Retain first failures and command exits. Immutable #6878 evidence is never edited.
