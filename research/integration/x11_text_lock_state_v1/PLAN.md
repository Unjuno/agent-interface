# X11 text and locked modifier state — Issue #4003

Source/intake: main 03ac3306861c2692b796bb14e2880ba9829d8291.
Preserve closed #3794 and previous #3931/#3955 STOP/HOLD. This is a concrete
text-effect correctness check for #2789, not a general discovery sweep.

## H / T / D / C / U

H: a live key map plus physically released keys does not identify Caps Lock
state. Preflight-only refusal is stale when lock changes before dispatch.
Dispatch-time read-only refusal prevents wrong-case input in the declared
before-dispatch transitions, without modifying locked state as a repair.

T: four serial batches, prepared/dispatch lock states OFF/OFF, ON/ON, OFF/ON,
ON/OFF. Each owns three policies x two repetitions (24 total). Rep0 policy order
EXACT_BACKEND, PREFLIGHT_LOCK_GUARD, DISPATCH_LOCK_GUARD; rep1 reversed.
Fresh ordinary Tk Entry per case, fresh authenticated Xvfb per batch, US map,
text aB2. Existing backend focus/preflight/text/execute/release methods are
unchanged. Native XkbLockModifiers changes the private fixture before the tested
boundary only; XkbGetState and XQueryKeymap independently observe it. Exact app
key/value journals, read-only snapshots and process exits determine effects.
Trailing Euro preflight must refuse before any emission. Per subprocess response
bound 3 s; each batch supervisor bound 15 s plus at most 3 s termination; tool
call uses a 20 s envelope. Four separately observed synchronous supervisor exits
are required. Batch failure stops later batches; no retry/replacement/pooling.

D: all 24 cases, exact schedule, source, raw wire/state, process exits and neutral
physical input required. EXACT_BACKEND: 4 exact/4 wrong-case. PREFLIGHT guard:
2 exact/2 wrong-case/4 refuse, including unnecessary ON/OFF refusal. DISPATCH
guard: 4 exact/4 refuse/0 wrong, all current-locked refusals with zero input and
blank Entry. Every release leaves configured locked state unchanged. All ten
copied-evidence mutations must reject. Missing evidence is HOLD/STOP, complete
semantic disagreement FAIL. A boundary PASS does not erase unsafe policy FAIL.

C: no change after the final check, no other modifier/group, one cooperative US
XKB/Tk stack. Check/use atomicity and multi-key concurrent changes are NOT solved.
Two directed repetitions do not estimate natural error rates. No model/provider,
user desktop/document/clipboard, install, network experiment or shared runtime
mutation. Test effects are confined to disposable private Entry windows.

U: supplied Linux x86_64 container / CPython3.13.5 / Tk8.6 / Python-Xlib0.15,
NOT Docker/OrbStack or image-attested replication. No general layout/IME/input
guard, public CLI/core-admission, model utility, performance or product claim.
Audit independence means another implementation/process, not another researcher.
Categorical exact-byte gates have no calibrated combined measurement uncertainty
or coverage factor. Clock ns are provenance diagnostics, not effect thresholds.

## Implementation and primary reference

source/backend.py is the complete exact upstream blob
9cae101a219348077668c8fc086acf8e13154afe. The AST loader removes ONLY the unused
runtime.core_v1.contract import; it transforms no method/class/constant and
supplies no replacement manifest helper. The unused manifest/artifact paths and
public admission layer are not executed. This is explicitly a backend-method
probe rather than a checkout or end-to-end CLI test.

Native helper build: gcc -std=c11 -O2 -Wall -Wextra lockctl.c -o lockctl -lX11.
X.org XKB Library Specification, chapter 5, Changing Modifiers/Determining State:
https://xorg.freedesktop.org/archive/current/doc/libX11/XKB/xkblib.html
The lock operation only reports request sending; subsequent synchronized native
state queries are the evidence, not the setter's Boolean return alone.

## Variable / unit definitions

| Identifier | Meaning | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| before, after | 準備時・送信時ロック | 1 | 0=OFF, 1=ON | integer scalar |
| mask, locked | X11修飾子ビット | 1 | this fixture 0 or LockMask=2 | integer bitmask |
| ns fields | 同一コンテナ単調時計 | s (stored ns) | nonnegative monotonic readings | integer scalar |
| emissions | backend入力イベント数 | 1 | 0 on refusal, 8 for aB2 | integer scalar |
| payload/value | 要求文字列・実際のEntry内容 | not physical | exact Unicode strings | string |

Unit check: lock masks compare only dimensionless bits; ordering compares only
same-domain ns fields. No timestamp is compared to an event count or bitmask.

## Construction and roadmap

construction-01 STOP: parent Python-Xlib read unrelated XAUTHORITY location.
No task emission, own app terminated, Xvfb exited0/socket removed. Source and raw
retained. Before formal, only parent auth environment mapping was corrected and
restored on close. construction-02 used different payload cD3, exact ordinary
Entry effect/8 events and neutral release, Xvfb exit0. Both excluded. Raw-only
construction audit passes10 mutation checks; additional typed schedule/clock
checks and process-group timeout cleanup added before final source freeze.

Roadmap: intake/source [done] -> excluded construction [done] -> public source
freeze -> four one-shot batches -> raw-only audit -> lossless evidence report/PR
-> verified main readback -> owned dependency-safe cleanup if supported.
The broad repository ROADMAP and #2789 remain open. Local execution incidents
belong to this run log, not new fleet-wide dependencies.
