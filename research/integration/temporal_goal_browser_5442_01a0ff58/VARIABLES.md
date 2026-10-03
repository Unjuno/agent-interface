# 記号・型・単位（v3・結果取得後の訂正）

| 記号/field | 日本語の意味・定義 | SI単位 | 範囲/前提 | 型 |
|---|---|---|---|---|
| case_id | 独立した文書対の識別子 | 非物理識別子 | C01: C001..C010。C02: C001..C009 と C020。各variant内で一意 | 文字列 |
| namespace | この専用アプリinstanceの対象範囲 | 非物理識別子 | C01: temporal-goal-5442-01a0ff58-C01。C02: temporal-goal-5442-01a0ff58-C02。variant間で代用しない。真正性の証明ではない | 文字列 |
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

これは結果取得後の訂正表です。C02/source/VARIABLES.md は固定時の誤った原表として保持します。
元のC02表にはC01のnamespaceとC001..C010の範囲が残っていました。新表を主試験前の固定記録とは扱いません。
実際の制御・SQL・raw監査は、それぞれの固定cases.jsonのnamespace/識別子/goal_hashを使っています。
mono_nsが等しい記録もあり、因果順序は同一の直列appのevent/request対応で検査します。
観測された目標状態8件/上限終了2件と、元の固定表の整合性HOLDを別に報告します。
