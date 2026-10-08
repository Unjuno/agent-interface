# poll時の優先だけでは、途中で届くcancelを制限できない

Linuxの実pipeで、事前固定した15条件を一度だけ実行しました。dataを読んだ後にcancelを書き、その後もdataを補充する2条件では、EAGAINまで読む方式は16回の診断上限までcancelを受理しませんでした。各pollでcontrolを優先する設定は、比較した3方式すべてで同じです。1回・4回でpollへ戻る既存の単純な方式は、この2条件とも予定した読取り数でcancelを受理しました。

| 条件 | EAGAINまで読む | 1回でpollへ戻る | 4回でpollへ戻る |
|---|---|---|---|
| data読取り1回後にcancel、data補充を継続 | 16回で診断STOP、cancelはcleanupでのみ回収 | 1回でACK、cancel後の追加read0 | 4回でACK、追加read3 |
| data読取り5回後にcancel、data補充を継続 | 16回で診断STOP、cancelはcleanupでのみ回収 | 5回でACK、追加read0 | 8回でACK、追加read3 |
| poll前にdataとcancelがready | 追加data read0でACK | 同左 | 同左 |
| data4 bytes、読取り1回後にcancel、補充なし | 4回でACK | 1回でACK | 4回でACK |
| data4 bytes、cancelなし、補充なし | 4 bytesを回収後EMPTY | 同左 | 同左 |

この範囲では、EAGAINまでのdata drainとpoll入口だけのcontrol優先を、途中で届くcancelの読取り回数制限として棄却します。既存の有限batchで十分に判別でき、新しい機構を要しません。実際のruntimeに該当する内側loopがあるか、そのcallbackの停止やjournal待ちまで有限かは、この実験で確認していません。

補充とcancelの書込みは同一process内で意図的に行い、OSの実FD/read/write/selectorを使いました。したがって、これは自然な到着頻度、並列producerの競合、hard real-time deadline、一般OSへの移植性、GUIのタスク効果や物理入力解放の測定ではありません。時計は同一processのmonotonic_nsで保存しましたが、wall timeの速度差や分布を算出していません。48時間共通締切は未確定のまま、延長していません。

実環境はMac上の専用OrbStack guest、Linux7.0.5-orbstack、arm64、CPython3.12.15、EpollSelectorです。保持済みimage `sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` をpullなしで使用し、networkなし、root/source読取り専用、0.25CPU、128MiB、32PIDsの実設定をcontainer inspectとcgroupで確認しました。選択したPython実行ファイル・selectors.py・native select moduleは事前hashと一致しました。kernelを含む全依存の完全なhash閉包は主張しません。

[事前freeze](https://github.com/Unjuno/agent-interface/issues/17#issuecomment-5967079805)は実行前です。source commit `db77f954355a7c74364de5e02c46712972f773b9`、source tree `25b2baf4b7625618b3d5b1536c1110480c83f2a2`、base `e5270c7bfe50911225afc6c3b5273021331b2bb1`、freeze SHA256 `aecccd3e1f772535807a902ec76e53ef6de1b86632b5d1b2a0bd6e9a3ca14555` が31個の事前入力を固定します。正式allocationは `17-HOT-DRAIN-ORBSTACK-A01-20261003-01a0ff52-70ab`。08:14:08.317471–08:14:12.453261 UTCに一度だけ送信し、producer/auditor各1回・終了code0/0・retry0でした。これは16回の診断STOPを成功したcancelへ変えるものではありません。

初回rawは15行・358イベント、38,054 bytes、SHA256 `242439e8d7a96f2c938668955c5469e40e1ccaeb97a754d1f1295e07f156efa0`。別構造のraw-only byte/FD/因果監査と、作者製の別のイベント切片確認が一致しました。全75個の実FD close検査がEBADFを確認し、guest出力9ファイルのtar復元とguest側hash読戻しも一致しました。保存rawのコピー10種類はすべて拒否されました。これらは非作者committeeのレビューとは別です。source textはすべて `.py.txt` で、自動importやtest discoveryを追加していません。

初回の環境調査はargvのdocker重複で失敗し、実験前に修理しました。実行後のイベント切片helperはcancelなし行でsumに空listを渡すTypeErrorを出し、純粋なraw再解析だけを修理しました。いずれも最初の失敗を保持し、正式producer・正式auditorを再実行していません。後者の初回sourceはtool callからの再構成で、原stderr・開始時刻を独立receiptとして捏造していません。

専用guestは08:17:05.401030 UTCに停止しました。実containerはexited、source・image・raw・終了containerを保持しています。他guestやshared/default daemon、GPU、GUI、model、物理入力を取得していません。

根拠は[PLAN](PLAN.md)、[FREEZE](FREEZE.json)、[初回raw](results/raw.jsonl)、[監査](results/audit.json)、[別のraw切片確認](results/event_slice_reference.json)、[出力保存照合](results/CUSTODY.json)、[実行receipt](results/host_attempt.json)、[資源解放](results/resource_release.json)です。先行#6927はpoll時点で既にco-readyの条件であり、そのallocationや#6915/#6942/#6896を再実行していません。#17/#6501/#59/#57の残る能力・実タスク効果は未完了です。main適用やproduction採用には別の内容合意と現在baseでの結合確認を要します。
