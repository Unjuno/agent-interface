# Formal-01 result

- Allocation: `issue2499-readiness-successor-3633-formal-01`
- Decision: `STOP_MIXED_APP_READINESS_SUCCESSOR`
- Formal invocations: 1; retries: 0.
- Failure boundary: first Inkscape role readiness returned `STOP_IDENTITY_MISSING`; no app identities were admitted and no transition or input operation ran.
- Calls: input 0, model 0, network 0.
- Cleanup: complete; failed-launch process group and Xvfb/Openbox process groups exited, no remaining PIDs, Xvfb socket removed.
- Independent task effect: not scored. Transition gate: not run.
- Exact source commit: `957cd65ae80180e717c92f1e04f42df5e3c6268c`.
- Frozen image: `sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f` (`linux/arm64`).
- Formal result SHA-256: `ceab4e22649b5e6843a885d856956938a020cb65104a806bed6c27a885b6e902`.
- Construction preflight SHA-256: `5e893d29f2afda8f99201a2e38e3ca462fafc437dcbb0201bf4a16984923d9ff` (`PASS_READINESS_CONSTRUCTION`, distinct IDs for all three applications).
- Formal launcher stopped on the runner's nonzero STOP exit before invoking its success-only audit. The preregistered audit script requires a full PASS transition ledger and cannot certify a legitimate early STOP; therefore no audit receipt is claimed. The raw result preserves event hashes and cleanup evidence.
- Root-cause assessment for successor planning: inspected runner creates an empty Xauthority file and starts Xvfb without `-auth`/cookie setup, unlike the passing construction gate which creates an `xauth` cookie and starts Xvfb with `-auth`. This is a source-based diagnosis, not a separately measured causal experiment.

The formal result is immutable. A successor must use a new allocation/issue and retain this STOP unchanged.
