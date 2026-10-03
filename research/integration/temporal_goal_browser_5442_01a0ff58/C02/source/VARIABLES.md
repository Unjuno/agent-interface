# 記号・型・単位

| 記号/field | 日本語の意味・定義 | SI単位 | 範囲/前提 | 型 |
|---|---|---|---|---|
| case_id | 独立した文書対の識別子 | 非物理識別子 | C001..C010、一意 | 文字列 |
| namespace | この専用アプリinstanceの対象範囲 | 非物理識別子 | 固定C01 scope、真正性の証明ではない | 文字列 |
| goal | rich-model workerが作った意図する保存文字列 | 非物理文字列 | 二種類のUnicode、完全一致が今回の目標述語 | 文字列 |
| target | 意図する文書のID | 非物理識別子 | doc:A、doc:Bは変更禁止対照 | 文字列 |
| v | SQLite文書のversion | 1（無次元） | 初期0、実更新ごとに+1、exact int/bool除外 | 整数スカラー |
| expected_version | form読み取り時のv | 1（無次元） | UPDATE時に現在vと一致が必要 | 整数スカラー |
| outcome | 過去の更新結果 | 非物理分類 | APPLIED/CONFLICT/DISTURBED;現在goal状態と分離 | 列挙文字列 |
| goal_current | 新しい観測時点でtarget値がgoalと一致するか | 1（無次元） | 対象binding/型/B保全を別に検査、継続性は未証明 | 真偽値 |
| k | そのcaseで送信済みの新しいrepair数 | 1（無次元の個数） | 0..2、initialと区別 | 整数スカラー |
| utc | 実際の操作/観測のUTC記録 | s（日時表記） | OS時計、因果順序の独立保証ではない | ISO8601文字列 |
| mono_ns | 同一app processのmonotonic時計 | 10^-9 s | 別processの値と比較しない、性能推論に使わない | 整数スカラー |
| opid/nonce | 新しい一回の送信の識別子 | 非物理識別子 | 一意、再送の冪等性を仮定しない | 文字列 |
| goal_hash | namespace/case/target/goalのcanonical SHA256 | 非物理識別子 | bytes binding、正しさ/真正性の証明ではない | 16進文字列 |
| bytes | 保存されたファイルの長さ | B（情報量、SI物理量ではない） | 上限12MiB、実測を別記録 | 整数スカラー |
