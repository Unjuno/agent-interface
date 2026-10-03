# 更新後mainの出力close修理候補

main20db889c66f306585aacc41f45c763b6bb157e2cで、自分の既存5件の出力close回帰を通常構築試験として実行し、2PASS/3FAILを再現しました。無言のclose後、write callbackが戻るまで所有処理がpendingになり、既にdestroy済みoutputでも追加writeを試みていました。

現在のUTF-8検証とbusy backlog制御を保持し、V4のper-write close検知・最初の障害の外側ownerへの即時通知・startup/ready/terminal/host cleanupを組み合わせました。候補7463B SHA256 8f9ebcec1e8b2000a73faf72ae51b62f5b4a9947b62dd0f9d0845af26abe5e79。同じ5件が5PASS。別実行の現main stdio/backpressure/UTF8と自分のfailure-order/whole-owner結合確認は34PASS。39件一括実行とは報告しません。

baseline PID95175 20:14:05.555098〜.680966 UTC/終了1、candidate PID95355 20:14:36.519372〜.642968/終了0、coupling PID96003 20:15:30.851168〜20:15:31.534354/終了0。すべて2026-10-03。raw・証人・実定義・製品ソースを保存しました。タイムアウト30/60秒、1MiBは取得後サイズ確認でOS制限ではありません。無関係な正式実験や受領packet helperを再実行していません。

旧固定V4の送信引き継ぎ提案は受諾前に取消します。main製品ソースが変わったため、旧V4を全置換せず新しい内容提案として扱います。作者0975とUTF8作者45e9は結合内容の非作者投票から除外します。旧内容票は新候補へ移しません。main送信0、不明0。

実機効果、物理解放、一般的な有限回復、速度/モデル呼出し/総資源の経済性は未証明。今回の局所修理は全体目標の完了ではありません。
