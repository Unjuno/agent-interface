# PUBLIC construction path-display projection

保持したconstruction v1–v4原本92 membersをUTF8として読み、指定のworkspace absolute prefixだけを <WORKSPACE> に置換したpublic表示用archive。PUBLIC_MANIFEST.jsonは各memberのoriginal/public bytes・SHA・変換有無とprivate original archive identityを結ぶ。元archive/memberは前後とも不変、public decodeは指定置換後のbyte/hashと全92件一致。

古いsource/receiptの投影pathは表示証拠であり、投影されたsourceの実行認証ではない。receipt内に保持したsource/hashはprivate execution originalを指す。現portable v4 audit/controls sourcesおよびv4 RESULTS.jsonのbyteは完全に同じであり、54 controls normal/-Oの結果の意味は変えていない。初回のLinux/macOS errno failureと修正履歴も表示上保持した。

PRIVATE construction-v1-v4-originals.tar.gzは公開・pushしない。このPUBLIC archiveだけを公開packageへ使用する。これはartifact包装支援でcommittee vote/原本認証ではない。今回collector/auditor/regression/target-code/Git/network/VMを実行していない。
