# Post-run challenge — host-run-02

The route-indexed output and original 10-check `PASS_METHOD_SCOPED` are retained. A later challenge against Issue #6026's explicit maximum/burst-burden reporting requirement found that the output did not preserve or independently reconstruct burst maxima. Reclassified `AUDIT_INCOMPLETE`; no raw file was changed. The successor adds explicit burst IDs and independent maximum-burst reconstruction.
