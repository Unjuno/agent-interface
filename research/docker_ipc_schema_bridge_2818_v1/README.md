# Docker IPC schema bridge (#2818)

Contract-only adapter for the retained #2807 schema-preflight stop. It binds
request/response IDs, requires a schema payload, preserves usage metadata, and
fails closed on malformed/mismatched/authority-bearing responses. Broker errors
yield without granting authority. It performs no GUI, model, provider, input,
or task operation; this is not a six-task result.
