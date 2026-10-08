# Supplemental auditor identity

This auditor was added after the first T2 audit to independently verify the
configured observation delay, marker freshness/fault controls, active-lease
suppression boundary, and an early-observation mutation. It reads the exact same
immutable formal raw; it does not invoke the simulator.

- `audit_v2.py` SHA-256: `a17ec9fb9f0b78bef390efb23f13b04556af3825921b78bcbff5524ab8401680`
- `AUDIT_V2.json` retains the one supplemental audit's stdout result.
- Input raw SHA-256: `1093ab8d5750fe305e22413b470b909badea2e670a57a2d68faaabbe052ac3b4`
- Supplemental auditor completed with PASS, zero errors, and rejected the
  early-observation mutation. The first auditor output remains unchanged.
