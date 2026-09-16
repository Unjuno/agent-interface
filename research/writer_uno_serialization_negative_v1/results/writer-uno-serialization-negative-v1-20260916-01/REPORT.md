# Writer UNO serialization negative v1 — retained result

**Result ID:** `writer-uno-serialization-negative-v1-20260916-01`  
**Source/plan freeze:** `749d4253aa9b8e8560919a8d245ef1c8431feeaf`

## Disposition

**RETAIN_UNO_SERIALIZATION_NEGATIVE / REJECT_COMPARE_RECHECK_CONTROLLER_LOCK_AS_ATOMIC_CAS / HOLD_FIX_SELECTION**.

Nine fresh private Xvfb/Openbox/LibreOffice Writer sessions executed once after source freeze: three each for `compare_set`, `recheck_set`, and `controllers_lock_set`. The deterministic external UNO mutator was released strictly after the candidate's compare/final-recheck/controller-lock point and before the candidate write.

| mechanism | sessions | external `book→boox` completed | candidate saw `prewrite=boox` | candidate overwrote to desired |
|---|---:|---:|---:|---:|
| compare then set | 3 | 3/3 | 3/3 | 3/3 |
| final recheck then set | 3 | 3/3 | 3/3 | 3/3 |
| `lockControllers()` + compare/set | 3 | 3/3 | 3/3 | 3/3 |

In the lock arm the external mutator independently observed `hasControllersLocked()==true` in **3/3** sessions and still changed the text. Its measured UNO write calls completed in 5.911 ms median (development/fixture timing only, not a performance bound).

The final document text being `bookkeeperoffice` is **unsafe stale overwrite evidence**, not task success: the candidate had already observed that another process changed the application state to `boox` and nevertheless replaced it under its stale precondition.

## Interpretation

- One client process doing compare then set is not atomic.
- Adding a final read immediately before the write does not close a race that occurs after that read.
- Writer `lockControllers()` is a controller/update presentation lock, not a model-mutation serialization primitive in this measured environment; a second UNO process can mutate `Text.String` while the lock is visible as active.

No additional earlier guard can logically close this demonstrated post-guard gap. A future fix needs a mechanism that serializes the mutation with the condition check, or must refuse/re-observe rather than claim CAS semantics.

## Evidence closure

- 9/9 frozen source blobs matched GitHub before formal execution;
- deterministic static tests: 3/3 PASS;
- formal matrix: 9/9 negative gates PASS;
- formal arm reruns: 0;
- no XTest/input injection, model, provider, or network calls;
- full decision evidence is reconstructible from `formal-evidence.json.gz.b64`.

## Development-only boundary

Before freeze, Python ScriptProvider/macro invocation was explored as a possible single-call application-side mechanism but failed in this environment with LibreOffice `std::bad_alloc`. That plumbing failure is not evidence that all in-process extensions/macros are impossible, and this formal result makes no claim about a custom atomic LibreOffice extension.

## Limits

Private Linux/X11 Writer + UNO only. Deterministic injected concurrency proves possibility, not natural race frequency. This does not evaluate the concurrent X11 server-grab lane, custom LibreOffice extensions, Wayland, Windows/macOS, accessibility APIs, Unicode/IME, model/token effects, or final product architecture.
