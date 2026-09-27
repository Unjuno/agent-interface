# Caller-owned observation: primary Calc use

The native bridge now uses the public read-only observation facade on its existing
caller-owned session, complementing #4683's dispatch integration. Capture failures
are retained without closing the connection, retrying capture, or clearing input
recovery. Existing before/after binding and artifact identity checks remain.
A returned public capture alone is not an accepted bridge source.

Actual source 42327da2a (full revision in archived source.json), fresh Calc seed
991296. The primary viewed the initial image and both action images through a
real MCP SDK client, entered A1=341/A2=595, saved and confirmed the format dialog.
Saved XLSX independently confirms those values. No extra observation request,
input replay or helper model. Character gap 2 ms and both 250 ms waits unchanged.

Ten successful public observation reports correspond to the ten accepted bridge
observations, including guard/feedback captures. Two public dispatch reports
completed with verified empty input releases. Finish evaluation succeeded and
native_status records owner PID 82904 exit 0; the managed client exited 0 as
observed in terminal. Descendant cleanup remains unverified.

Contract tests separately cover capture failure, invalid regions, recovery-state
preservation, no close/retry/input, and refusal to advance bridge history when
binding changes during capture. The live run does not inject those failures or
independently measure connection identity. No latency, token savings, full MCP
lifecycle convergence or overall acceptance is claimed. Extra retained reports
add storage/write overhead; this integration has not been benchmarked for speed.

Run python3 verify.py here to verify archive hashes, saved cells, public reports,
exact capture correspondence, input releases and owner exit without UI replay.
