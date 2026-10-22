# Owner stop overlap A01

## Question and hypothesis

When `stop_requested` arrives after the owner thread dequeues an explicit
`release` but before that operation executes, does shutdown create a second
`owner_release` record even though the admitted key receives only one XTEST
KeyRelease?

**H:** the explicit release will empty the admitted key once; the next loop
iteration will then append an empty `stop_requested` cleanup record. Its
`valid_until_ns: null` should distinguish that shutdown record from the
lease-bound release record.

## H/T/D/C/U

- **H:** The exact current-main InputOwner v10 state machine separates the
  explicit release operation from the persistent stop signal. Stop arriving
  during the dequeued operation may therefore produce an additional empty
  owner record without a second input event.
- **T:** Run the hash-pinned owner source twice with deterministic fake Xlib:
  a baseline explicit release and a dequeue-gated stop-overlap case. In the
  latter, pause after `Queue.get()` returns `release`, set `stop_requested`,
  then resume. Compare emitted fake XTEST events and owner records.
- **D:** PASS if each case produces one KeyPress and one KeyRelease, no fake
  key remains down, all captured owner records verify empty state, and the
  stop-overlap case's extra record has `reason=stop_requested` and
  `valid_until_ns=null`. FAIL if an input event is duplicated, a key remains
  down, verification fails, or the expected record distinction is absent.
- **C:** The extra shutdown record may be an intentional final cleanup barrier.
  A fake server cannot establish real X-server or physical-key behavior.
- **U:** This isolates only owner queue/record semantics. It does not test
  physical input, GUI delivery, useful feedback, model timing, recovery
  efficacy, threat control, or MAP01 task effect.

## Frozen identities

- Base `main`: `8094af4631fc7bc5d92990e5151d5e89477ee39f`.
- Candidate source: `dependencies/input_owner_v10.py`, copied byte-for-byte
  from that base and identified in `FREEZE.json`.
- No formal/live allocation: construction-only fake-Xlib probe.
- Candidate commands: `python3 -B run.py`; independent audit:
  `python3 -B audit.py`.
