# Issue #7728 Windows-host counter cross-check A01

## Scope

This is a host-specific follow-up to the merged macOS sensor HOLD in #7728. It asks whether the Windows host exposes a documented cumulative CPU-package energy counter whose raw value agrees with the Windows Energy Metering Interface (EMI). It does not repeat or overturn the macOS result.

The run is read-only: enumerate EMI devices, read their metadata and absolute-energy samples, and read the `Energy Meter(RAPL_Package0_PKG)\Energy` performance counter between two EMI samples. Do not launch an application task, GUI, model, route, CPU load, or formal T1 pilot. Do not elevate privileges.

## H / T / D / C / U

**H.** This Windows host exposes an unprivileged cumulative package-energy measurement whose unit/domain metadata can be tied to a Windows EMI device and whose performance-counter raw value is bracketed by that device's absolute-energy readings.

**T.** Freeze the exact probe/auditor/EMI header hashes and base commit. Read all present EMI v1/v2 devices once, query the exact RAPL package performance counter once, then read all EMI devices once more. An independent parser checks unit, metered-domain/channel name, monotonicity, status, counter type and bracketing. It also rejects synthetic unit, missing-channel and out-of-bracket mutations. No task or workload is launched.

**D.** `PASS_COUNTER_ORACLE_MATCH` only if the EMI metadata declares picowatt-hours, identifies `RAPL_Package0_PKG`, both direct readings are monotonic, the Performance Counter has valid status and a 64-bit raw-count type, and its raw value lies between the direct EMI readings for the same channel. Otherwise retain `HOLD_COUNTER_IDENTITY_OR_UNIT_UNVERIFIED` or the observed failure. This result alone does not authorize T1.

**C.** A coincidentally similar counter can be misidentified; bracket checks plus the direct API metadata reduce this risk. Package-level energy includes the host's total package activity and is not process attribution.

**U.** This does not validate idle-baseline subtraction, task-boundary repeatability, a GUI effect oracle, per-process attribution, energy per safe effect, or non-inferiority. The prior host snapshot showed high total CPU use, so no idle/load or route measurement is attempted in this run. No counter wrap or reset is observed in a short read-only interval; any later decrease must be treated as reset/invalid, with no guessed wrap correction.

## Stop rule

Do not run any route/task pilot from this package. A later step requires a quiet, controlled host baseline and a separately frozen route protocol with independent effect scoring.
