# Issue #2624 live-smoke plan

Allocation: `mindustry-materialized-live-smoke-2624-20260922-01`.

## H
With the exact preverified Mindustry v160.2 JAR, canonical save, and retained
setup-only mod mounted in the provided disposable Linux execution container, one
fresh private Xvfb/Openbox/Java21 session reaches the retained paused setup
projection and exits cleanly under SIGTERM without any controller/task input or
model/provider call.

## T
One formal session only; timeout 60 s; no retry/replacement/tuning. Fresh HOME,
XDG and Mindustry data directory. Install exact retained mod, copy exact save to
`input.msav`, set software-render/null-audio environment, start `java -Xmx768m
-Duser.home=<fresh-home> -jar <exact-jar>`, and wait for retained `ready.txt`.
Construction is asset hashing plus private Xvfb/Openbox lifecycle only; it never
launches Mindustry.

Expected identities:
- Mindustry.jar: 87,022,576 bytes; SHA256 7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539
- canonical.msav: SHA256 8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed; Git blob 7663b25633d853a257fbb407723fe85579120111
- mod.json: SHA256 4b8e413ab0c4561c82edd8e422c517b631f1baee79a0b008adb42e9624965e05; Git blob 137ae8036b7864af744565bbc1c2af566290ea92
- scripts/main.js: SHA256 7b5bd06bc34db9655e3946a9c202948cdaa0a4b233e0eec1fe063aa8358c220f; Git blob 84e9a0c291d5b7f454d6092f2c100728a9a16da2

## D
PASS_MINDUSTRY_MATERIALIZED_LIVE_SMOKE_SCOPED iff all identities pass before
launch; Xvfb/Openbox start; Java remains live through readiness; ready.txt and
valid oracle.json arrive <=60 s; oracle has width=300,height=250, 250 rows x 300
tiles, paused=true, core_present=true,copper=200; wmctrl reports a Mindustry
window; task/controller/model/provider call counters remain zero; Mindustry,
Openbox, and Xvfb all terminate after SIGTERM without SIGKILL and are reaped; and
independent audit/source/corruption gates pass.

Exact assets but no readiness/window -> FAIL_LIVE_FIXTURE_STARTUP. Readiness with
oracle mismatch -> FAIL_ORACLE_MISMATCH. Missing source/process/evidence -> STOP/HOLD.

## C
Setup-only cooperative mod and oracle; software-rendered private Xvfb fixture.
No gameplay/controller/model behavior. Process SIGTERM is not crash/power-loss.

## U
One session cannot establish repeated reset reliability, task correctness,
model/token economics, human tempo, production support, or #57 second-domain
economics. PASS only removes the live-start gate required by #1679/#2068/#57.
