# 子処理の寿命とbroker交代時の資源排他：c7n4

## 結論

24ケースを完了。判定は **PASS_LOCAL_CHILD_LIFETIME_BOUNDARY**。
ただし本番採用は **HOLD_CHILD_DESCRIPTOR_CONTRACT_UNVALIDATED**。
要求IDの重複抑止は、異なる要求ID同士の資源競合を防ぐ契約ではない。
親だけが持つロックも、親が終了した後に動き続ける子の作業を保護しない。
子にロック記述子を継承させると保持中の重複を防げたが、子が記述子を
閉じる負例では排他が失われた。この負例を合格結果から除外していない。

GitHub Issue投稿・PR作成・main統合は未実施。接続が公開する48操作は
読み取り用で、追加探索でも書き込み操作は見つからなかった。このセッション
の制約であり、GitHub障害・権限拒否・他workerの書き込み不能ではない。

## 現状確認・変えた仮説

開始／終了main:4c701cc51b06296268ad8d9ae3eff1dd6f2d379d。
README、CURRENT_GOALの統治部、ROADMAP、最近のopen/closed Issue・PR、
100 branch名、関連検索をGitHub MCPで確認。全履歴・未push作業の網羅確認
ではない。#4372の前回証拠公開、#3987/#4081、#3924/#3926、#4349は変更なし。

前回r5k1は「子起動前」または「子終了後」にbrokerを停止した。
今回はその除外条件だった「子が実際に稼働中のbroker停止」を追加した。
既存のclaim.py、contract.py、probe.py、collectorは元バイトのまま使った。
要求IDだけのbaselineも前回durable_claim.pyそのもの。追加した資源予約は
試験用slot-a/slot-bに限定し、GUI・実モデル・本番資源には接続していない。

## H/T/D/C/U

H:要求の重複抑止、broker寿命、子の資源占有寿命は別物である。
子が保持するopen-file descriptionに排他を結び付けることは条件付きで有効。

T:3方式、4スケジュール、各2反復、24新規ケース。4つの6ケースバッチを
それぞれ一度だけ実行。ケースごとにold/newという異なる2要求を一度ずつ公開。
正式48要求・48子起動、42broker起動。Linux/CPython標準ライブラリ、実際の
別プロセス・FIFO・/proc・flockを使用。モデル/provider/GUI/OS入力は0。
提供コンテナ上の実行で、Docker/OrbStackのimage-attested追試ではない。

D:24件・全実終了・同一要求再起動0・全新要求回収・旧claim不変・負例の再現・
監査と12改変対照の通過を要求し、通過した。これは境界仮説の限定合格であり、
子のFD保持を未確認の実行先に適用する本番採用はHOLD。

C:同じ保持inode、全起動が同じgateを通ること、信頼された協調child、
保持されたclaim、同一ホストの安定したファイルを前提とする。子のcloseや
LOCK_UN、inode置換、複数ホスト、派生子・孫、外部効果は別契約である。

U:実Codex等のFD保持・自発的close動作、実入力の解除、任意アプリ、電源断、
NFS/SMB、速度/token/費用便益、一般故障率は未測定。同一作者の別実装・
別プロセス監査であり、独立した人の査読ではない。

## 結果（各表セルは2ケースの観測）

| スケジュール | 要求IDのみ | 親だけロック | 子にも継承 |
|---|---|---|---|
| 通常、old終了後にnew | 重複0/2、新結果2/2 | 同左 | 同左 |
| old稼働中にbroker停止、同資源new | 同資源重複2/2 | 同資源重複2/2 | 重複0/2、old終了後にnew進行 |
| old稼働中にbroker停止、別資源new | 別資源進行2/2 | 同左 | 同左 |
| 子が継承FDを閉じてからbroker停止、同資源new | 同資源重複2/2 | 同資源重複2/2 | **同資源重複2/2** |

方式ごとの同資源重複は4/8、4/8、2/8。分母には通常・別資源対照を含むため、
これを自然故障率や性能比較にしてはいけない。子がFDを保持した同資源の
2ケースだけが候補の条件付き排他を示す。記述子closeの2ケースはその限界。
全方式で各8/8の新要求を最終回収し、oldの再実行は0。全48の試験用私有
ファイル効果は完了したが、brokerが失われたold18要求の完了記録は欠けた
ままで、collectorは全18件をPENDINGとした。効果ファイルを後付けの
model結果やtask成功に読み替えていない。

独立した/proc読取りで旧broker終了後も同じ子のPID/start_ticksが生存し、
子は実際にsubreaperへ移ったことを確認。新旧子の同時生存・資源ID・
開始／終了直前記録を照合した。独立lock probeは保持FDのある場合のみ拒否。
保持されない場合には取得できた。新brokerのPID不在や旧pidの死亡を、
資源が空いている証拠にしなかった。

## 実装と条件付き根拠

resource_brokerは、claim前の非待機資源予約、busy時の次周回への繰越、
subprocess.runのpass_fds引数、子終了後の親FD closeだけを追加した。
元の引数・終了/timeout処理はAST比較で、pass_fds以外が等しいことを確認。
親だけロックと継承方式は同じsourceで、渡すFD tupleだけが異なる。
明示的LOCK_UNはしない。子が同じopen-file descriptionを保持している間、
親FDのcloseだけでは最後の参照が消えず、別openの排他取得を拒否する。
詳細な条件付き導出と変数・単位表はPLAN.mdに収録した。

このロックは協調規約であり、sandbox・認証・一般的なexactly-once効果保証
ではない。子がFDを閉じる実行先に使えば、今回の負例のように前提が崩れる。
またoldのPENDINGを解決する仕組みでもなく、効果の成否と排他は別の証拠。

## 検証・保持

- 正式24/24ケース、48/48子起動、各要求の再起動0。
- 4/4外部Popen待機の終了0、24/24ケース終了0。全42brokerは予定した
  SIGTERMで終了−15。これを終了0に変更していない。
- 子の実終了はbrokerのsubprocess.run30件、subreaper.waitpid18件で照合。
- raw-only監査:5471チェック、errors=[]。
- 12/12有効な改変を通常の監査不一致で拒否。無変更・例外落ちをPASSに数えない。
- 8/8単体テスト。固定source20/20一致。正式再実行・置換・事後調整0。
- Freeze SHA256:239fae468a7b8370430dee4e75061aced54eae487fad4aa8eb82e65a43ec455c。
- AUDIT SHA256:59b52475e4764c4253269bd6a6407b974c9ad94fd20846f764a2ae75e9232ae6。
- CONTROLS SHA256:a2a52ea3d71eda322aadca53561df4dbab186ae7d7e8aa239f4b461a33faec10。

構築は合計7ケース。最初の1件のcleanupで、既に終了した子のFIFOへ未記録の
追加R byteを送る処理を発見した。実処理は再実行されていないが、完全な
制御byte会計とは言えないため、source/結果を保持したまま正式前に修正。
次の別ID6ケースを構築し、全チェック後に正式sourceを固定した。構築を正式
分母へ混ぜていない。詳しくはCONSTRUCTION_NOTES.md。

## 前回の保全

前回ZIP ae80575a64ab7f42730291b307b81821d6c04b709b4daba4ab1d87380e978f69
を読み取り専用で復元・検証。727ファイル、17 pins、13テストを確認し、
前回AUDIT/CONTROLS出力が完全一致した。前回20ケースは再実行なし。
新パッケージは前回全ZIPを再内包せず、sourceの必要部分と検証receipt・
ハッシュだけを保存。元ZIPは別の会話添付としてそのまま残っている。
それ以前の48ケースHOLDも変更していない。

## 公開と残件

追加namespace:research/integration/ipc_child_lifetime_c7n4_v1/。
提案branch:research/ipc-child-lifetime-20260926-c7n4（remote未作成）。
GitHub公開、PR、main統合、他branch削除、shared runtime変更は0。
ローカルのdirectory snapshotと追加patchはremote-mainをcloneしたbranchではない。
完全なrepository test/CI、外部review、本番採用、global ROADMAPは未完了。

残る採用判断は、実際の実行先でロック所有者の寿命を保証できるかどうか。
同じ合成ケースを増やして本番のFD保持保証へ代替してはならない。

## 参考一次資料

Linux flock(2):https://man7.org/linux/man-pages/man2/flock.2.html
Python3.13 subprocess:https://docs.python.org/3.13/library/subprocess.html
Linux subreaper:https://man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html
これらはAPI根拠であり、今回の実測値の出典はformal/以下の生記録である。