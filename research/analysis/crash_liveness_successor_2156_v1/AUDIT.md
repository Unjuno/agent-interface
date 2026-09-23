# Independent audit

Recompute all six decisions from persistence, delivery, effect status, and idempotency. Require replay only for visible durable receipts, query/reconcile for ambiguity, abort after known effect, and new identity only when no durable record exists. All effect and authority counters remain zero.
