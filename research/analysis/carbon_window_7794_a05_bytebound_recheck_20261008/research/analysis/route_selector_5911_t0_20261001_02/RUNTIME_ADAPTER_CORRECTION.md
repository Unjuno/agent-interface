# Adapter correction before candidate (append-only)

The prior adapter note incorrectly said the module text starts with `export`. Readback shows the first line is `const argmin` and the exported declaration occurs later. The failed `new Function` parse occurred before invocation/output, so candidate count remains 0. Correct one-shot binding: apply exactly `source.replace("export function evaluate(", "function evaluate(")` to remove the export token at its actual declaration, then evaluate/call once. No algorithm text changes.
