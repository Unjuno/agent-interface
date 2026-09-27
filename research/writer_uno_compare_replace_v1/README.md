# Writer UNO compare-replace v1

Research-only application-side text mutation discriminator. It compares a stale two-RPC `read -> set` sequence with a single UNO `XReplaceable.replaceAll` exact-regex call under a competing independent UNO append. This is a distinct application-side delivery capability, not OS `input.text`.
