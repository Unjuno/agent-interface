# Boolean 応答 ID の数値要求への誤対応

実際の Windows stdio 子プロセス比較では、未変更クライアントが要求整数1に
対する応答Boolean trueを成功結果として受理した。二行のBoolean除外後は、
その応答を受理せず、整数1と数値1.0の正常応答を両方維持した。

| 応答ID | 未変更ソースの呼出し結果 | 修正版の呼出し結果 |
|---|---|---|
| Number 1 | 対応するpayloadを返す | 対応するpayloadを返す |
| Number 1.0 | 対応するpayloadを返す | 対応するpayloadを返す |
| Boolean true | 不正なBoolean-IDのpayloadを返す | EOFでAppServerError |
| Boolean false | EOFでAppServerError | EOFでAppServerError |
| String "1" | EOFでAppServerError | EOFでAppServerError |
| Null | EOFでAppServerError | EOFでAppServerError |

未変更6件は2026-10-03 06:32:18.637398–06:32:19.595436 UTC、
意味的FAIL_BOOLEAN_ID_ALIAS/終了1。修正版6件は06:34:07.408423–
06:34:08.257204 UTC、PASS_BOOLEAN_ID_FILTER/終了0。
それぞれ元のfreeze後に一回だけ実行し、原結果の再実行・失敗行除外はない。
全12件で、実際の送信wire、peerの応答wire、受信journal、呼出し結果、
型を保った残存cache、自然終了0、reader終了、journalと所有パイプの終了が
揃った。source.closeは親pipeを閉じないため、collectorの明示的終了を別記した。

元baselineは3payload/うちBoolean1、修正版は2payload/Boolean0。
独立の保存JSON専用auditorを06:34:09.076786–06:34:09.291291 UTCに
一回実行し終了0。完全な型付き照合と元file/hashを検査し、八つの有効な
コピー改変（literal ID、Boolean受理、float正常結果、sent ID、wire ID、
残存Boolean cache、自然終了、件数欠落）をすべて拒否した。
同じ作者による別実装の検査であり、非作者投票やpeer認証ではない。

追加の公開API回帰は、Boolean true/falseと通知を挟んだ後のNumber1.0応答、
正常IDのサーバーerrorを検査した。通常と-O各2method、終了0。
実際の所有stdio childを各method一つ使い、自然終了とreader/cache/pipeを確認。
合計の不活性protocol childは比較12＋回帰4=16、同時に一つ。
この追加回帰は別の通常実装確認であり、最初の六件比較の反復ではない。
四つの既存PersistentGroundingModel FakeClient試験は読んだだけで実行していない。
全native suite、GUI/model/provider/backend、共有入力、正式allocationは実行しない。

必要な変更はclientの二行、公開API回帰二件、共用SUITES.protocolの一登録。
snapshot/peer/runner/auditor/captureは.py.txtの非自動実行領域に置く。
五つの実在の直接import caller、共用入口と関連workflowをGitから確認した。
native CIはnested archiveをsparse対象から外す。根拠はDEPENDENCIES.json。
別作者の#6944 startup修理と#6945 closed-stderr診断、TS transport、#6882
lineage意味論の原記録・担当は保持する。この修正はその診断の一般timeoutを直さない。

JSON-RPC2.0のIDはString/Number/NullでBooleanを含まないが、このapp-server
研究クライアントの要求はjsonrpc属性を付けない独自JSONL形式である。
[一次仕様](https://www.jsonrpc.org/specification)の型区別を相関述語へ用いた範囲の
修理で、全面的なプロトコル適合性・genuine Codexの障害実測を主張しない。
有効IDを常に出力する本物serverはこの不正peer故障を除外し得る。
pending ID照合、再送・preplay、任意envelope、認証、物理解放・task効果、
待ち時間・呼出し回数・総資源改善は未証明。arm所要時間は効果比較に用いない。

原private byteと公開path置換はPUBLICATION.jsonで個別に識別する。
元freezeと原auditor結果のhashは原byteを指す。公開manifestとreadbackは公開byteを
指す。パス置換を元byteの一致、digestを本人性、監査成功をmain反映と扱わない。
通常setupの最初の失敗と工具出力の上限はSETUP_NOTES.md/DEPENDENCIES.json。
二つの実際の非作者内容票とその後のcurrent base/head/tree結合確認を待つ。
main送信・共有resource/apply lockはゼロ。コンピュータコントロール全体は未解決。
