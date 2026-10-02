# Auditor path-fix record

The first offline STOP-evidence audit invocation failed before reading evidence because its local root expression resolved to the `evidence/` directory rather than the experiment root. It performed no data generation, model load, Docker call, or experiment. The auditor path was corrected to use the experiment root (`parents[2]`); the failed first audit attempt is retained here as an engineering record.

