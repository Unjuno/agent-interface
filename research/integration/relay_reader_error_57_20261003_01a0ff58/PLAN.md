# Ordinary reply-reader repair

H: The public host's child-stdout Readline error can terminate the host before its
existing pending uncertainty/no-replay path observes that request.
T: Exact main source, three reader-error stages (idle, outstanding parsed inert
request, already settled result), plus one-byte writes of Japanese/emoji and EOF.
Preserve first RED, then route Interface error to existing fail(). Run only
existing relay-client/host and necessary caller/exchange/stdio checks.
D: Same outstanding promise rejects uncertainty; no ID advancement, second
request or replay after loss. Idle failure blocks first send. Settled result
remains exact, future sends block. Child transport close exits0. Positive text
and existing refusal/presentation/source custody behavior remain unchanged.
C: Error is deliberately injected by destroying a real Node child stdout
stream; it is not an observed spontaneous OS fault or a real MCP dispatch.
U: Native Windows/Node24.19.0 only, responsive private filesystem and inert
children. No GUI/input/physical-release/backend/model/performance or global
deadline/byte-cap guarantee. Ordinary repairs/checks, not consumed formal work.

| Symbol | 日本語の意味 | 単位 | 定義・範囲 | 型 |
|---|---|---|---|---|
| id | リレー要求番号 | 非物理識別子 | 初回1、応答後2。失敗後の再送は禁止 | 安全整数 |
| attempt | ローカル送信記録の番号 | 非物理識別子 | 0または1の実送信 | 整数 |
| t_child | 不活性子プロセスの自己終了上限 | s | 2。テスト用で物理解放期限ではない | 正の実数 |
| t_probe | テスト呼出しの監督上限 | s | 5。親に対する制限 | 正の実数 |
| n | 新規回帰試験の件数 | 1（個数） | 4、うち失敗注入3・通常応答1 | 整数 |
