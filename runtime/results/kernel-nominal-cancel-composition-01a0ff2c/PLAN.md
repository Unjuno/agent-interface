# 名目型ガードと効果不明キャンセルの結合確認

Worker01a0ff2c-34fb-73a0-b3aa-bdf13badf325、FINAL-v5。#6894 comment5965007672で限定範囲を記録。#6875の名目型 runtime 採用担当を変更しない。

H: 既存の名目型ガードNと効果不明キャンセル修理Uは異なる不足を閉じる。Nは不正な解放オブジェクトを拒否し、Uは拒否後の正しい解放でも受理済み要求の可能性を保持する。どちらか一方は他方の代わりにならない。

T: main332da58aのcontracts/backend、#6901 head225b5826のlifecycle（#6892を含む）に、既存のN12行とUoutcome差分を独立にon/off。4種×事前固定の10履歴=40行。新しい標準ライブラリの入力を使い、過去のproducer/matrix/test/formal allocationは実行しない。JSONだけを読む別実装と8実効改変対照を使う。

履歴はnew、authorized未開始、begun+typed解放、begun+現行shaped解放、begun+stale shaped解放、begun+解放None、begun+無関係object、期限切れbegin拒否、明示execution NONE、明示execution POSSIBLE。拒否されたstopには有効なtyped解放を続ける。既に受理したstopは再送しない。各例は新しい独立lifecycleで、実backend/OS入力はない。

D: 全40行が別の期待遷移・厳密な型付きoutcomeに一致し、拒否時に全保存stateが不変。N+Uでは不正解放をContractErrorで拒否し、begin受理・receiptなしの5履歴すべてで可能性Trueを保持。beginなし/拒否/NONEはFalse、明示POSSIBLEはTrue。8改変は全件拒否。初回結果が一致しなければそのまま保持し、原因を切り分ける。範囲を緩めてPASSにしない。

C: 時刻下限だけでもstaleとNoneの一部は拒否できるため、Nの効果をそれらから推定しない。Namespaceはmatching identifierのshapedレコード、無関係objectは既知の例外種別対照。Noff/Uoffは現在の採用runtimeと同一ではなく、共通の未採用 temporal sourceに対する修理切替である。

U: 信頼された型付きAPI、直列順序、合成時刻のみ。Python敵対的subclass、frozen mutation、並行性、時計/レコードの真正性、backend/物理入力解放、タスク効果、速度/モデル回数/資源削減は未検証。主張は40の authored call historyに限定。mainの正確な結合tree、内容票、採用や反映権を証明しない。

| 記号 | 日本語の意味 | SI単位 | 定義・範囲・前提 | 型 |
|---|---|---|---|---|
| N | 名目型ガードの有無 | 1 | 既存12行を全追加/全除去 | Boolean scalar |
| U | 効果不明キャンセル修理の有無 | 1 | #6894のoutcome差分を追加/除去 | Boolean scalar |
| now_ns等 | 合成の共通時計値 | ns | 非負整数、観測100、authorize200、begin400、receipt600–800、解放1000、期限2000 | integer scalar |
| rows | 保持履歴件数 | 1 | 4 source variants×10 fresh histories=40 | integer scalar |
