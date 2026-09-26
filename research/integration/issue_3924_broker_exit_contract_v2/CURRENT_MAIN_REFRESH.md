# Current-main refresh before formal freeze

- Successor Issue #4485 intake main: `a718da028d33c9608433789676ddd7204d8c5d14`.
- Refreshed current main immediately before formal freeze:
  `67f1aedace0039d2ab8e4550becfaea78c50653c`.
- The research branch was rebased to this exact current-main commit.
- `runtime/host_model_ipc_broker_v1.py` remains Git blob
  `f307daafdfd36d1ab4faf39bb36c36350e6e67e4` and SHA-256
  `034b2e72a28fc3defb1b48195a2a8d3450e850895a4b3b7b7919dca44e198775`.
- `runtime/test_host_model_ipc_broker_v1.py` remains Git blob
  `e645ae575cd6fdae02556df9facc9919739584f3` and SHA-256
  `a28b59232e55956a11bd87a35812b7d77df16febe5510c68fb80eda03a3ede1c`.
- No formal case or broker/fake invocation has started for allocation v2.
- H/T/D/C/U and the seven-case matrix are unchanged from Issue #4485.
