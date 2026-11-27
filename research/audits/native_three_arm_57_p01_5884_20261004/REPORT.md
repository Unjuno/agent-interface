# #57 P01 実モデル・実GUI三方式比較

判定：HOLD_INTEGRATION_QUALIFICATION_WITH_MEASURED_SCOPED_BENEFIT。18課題すべての正しい単一POST効果と記録上のverified releaseを独立監査で確認。persistentはtask4でMISSINGを検出し、旧参照pointer0のまま1回修復し、task5–6へ再利用した。全統合安全資格は未取得のため本番採用や広いGUI解決とは扱わない。

| 方式 | input | output | cache input（input内数） | reasoning（output内数） | generation（preflight込） | 画像 | ready→独立oracle 秒 |
|---|---:|---:|---:|---:|---:|---:|---:|
| plain | 108811 | 562 | 66688 | 118 | 7 | 6 | 36.631 |
| ephemeral | 110293 | 933 | 74752 | 132 | 7 | 6 | 46.550 |
| persistent | 38874 | 455 | 12032 | 112 | 3 | 2 | 27.712 |

persistentのinput+outputは39329。plainの109373に対して64.04%減、ephemeralの111226に対して64.64%減。fresh preflightを各方式へ加算した累積tokenのbreak-evenはplainに対してtask2、ephemeralに対してtask1、task4修復後も優位が続いた。readyから最終独立oracleまでの時間はplainより24.35%短かった。この区間はbackend startupとschema preflightを含まず、全体速度の因果保証ではない。

| task | plain累積token | ephemeral累積token | persistent累積token | persistent route |
|---|---:|---:|---:|---|
| 1 | 24542 | 24843 | 24825 | cold |
| 2 | 38813 | 39319 | 24825 | reuse |
| 3 | 54418 | 55189 | 24825 | reuse |
| 4 | 71394 | 72482 | 39329 | repair |
| 5 | 89712 | 91161 | 39329 | reuse |
| 6 | 109373 | 111226 | 39329 | reuse |

| persistent phase | task秒 | モデルgeneration | input+output |
|---|---:|---:|---:|
| task-1 / cold | 7.644 | 1 | 13060 |
| task-2 / reuse | 1.531 | 0 | 0 |
| task-3 / reuse | 1.951 | 0 | 0 |
| task-4 / repair | 8.031 | 1 | 14504 |
| task-5 / reuse | 3.624 | 0 | 0 |
| task-6 / reuse | 4.747 | 0 | 0 |

実行ID 57-native-three-arm-P01-20261004-5884、同じseed57041008、順序plain→ephemeral→persistent、各6課題A/A/A/B/B/B、各方式1sample。native Codex0.146.1、gpt-5.6-luna/low、全方式ともarm内のmodel会話を保持。plainは座標契約と共有一回限りruntime guardを使い6操作batchを保持する。ephemeral/persistentは既存compiled契約・run_task/caller。歴史的E01の141sourceを固定した研究bundleで、current-main認定ではない。

全体producerは18:05:12–18:07:25 UTC、終了0、約133.641秒。VM起動・転送・source検証・preflight・全arm・回収・終了処理を含む。3方式を直列に実行した合計なので一方式のtask速度とはしない。task elapsedとmodel waitの原値はsummary JSONに保存し、異なるhost/guest時計の絶対時刻を引き算しない。startup/schema/回収の共有時間を各armへ恣意的に割り振らない。

fresh preflight3件＋grounding6/6/2で実呼出し17、モデル画像14。全actual input257978/output1950、cached input153472、reasoning output362、cache write0。cache/reasoningを総数へ二重加算しない。N01の別allocation input34867/output318と失敗原記録も保持し、P01の費用と合算してbenefitを作らない。金額・価格は未取得。

単一の開発既知fixture、固定順序、cloud cache、共有host負荷とモデル応答のばらつきが交絡。分布・confidence interval・人間速度・第二domain・本番互換性を推定しない。semantic abstention、全runtime negative、内部startup deadlineは未資格。cgroup1CPU/768MiB/256tasks/300秒は設定したがP01実行中の実効値は取得していない。host出力上限は100ms監視で有限overshootを許す。token capはarm間観測の停止でhard課金上限ではない。

独立監査は固定source/auditor hash、provider request/actual response/usage/image、元POSTとaccepted token-entry、terminal/release、完了時刻、eligible target resolutionを照合。18原効果・重複0・予期しないPOST0・旧参照入力0。全journalはclose前に保持し、archive内journal hashを確認した。VM停止を終了後に読み戻した。source/runtime変更は自分の隔離候補だけ、main変更0。原archiveは方式ごとにoutputsへ保全。

次は実結果とfreeze/source/rawを既存PR/#57へ保全し、非作者reviewを通す。第二domainと未取得安全資格は別の必要作業であり、この小さい比較から全goal完了を宣言しない。

| 方式 | local observations | durable calls | local program壁時計 秒 | task内model wait 秒（host時計） | schema model wait 秒 |
|---|---:|---:|---:|---:|---:|
| plain | 153 | 84 | 9.576 | 22.546 | 4.734 |
| ephemeral | 151 | 96 | 10.214 | 29.991 | 5.672 |
| persistent | 161 | 114 | 11.738 | 10.262 | 5.088 |

local program時間はguestのprogram submit/終了区間の和で、local観測・IPC・guard・入力・settleを含み、純CPU時間ではない。hostのmodel wait時計をguestの絶対時刻へ合わせていない。これらを恣意的に足し引きして厳密なlocal overheadを作らない。

追加の保存raw導出では、persistentのMISSING通知からfresh mintまでの区間にpointer/input admissionが0件であることを再計算した。この導出はpost-run分析であり、frozen producerと最初の固定監査は変更していない。
