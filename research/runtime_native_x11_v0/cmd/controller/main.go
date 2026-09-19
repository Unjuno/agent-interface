package main

import (
	core "agentinterface/nativecore"
	x11 "agentinterface/nativex11"
	"encoding/json"
	"flag"
	"os"
	"time"
)

func b(v bool) *bool { return &v }
func main() {
	condition := flag.String("condition", "valid", "")
	ready := flag.String("ready", "", "")
	out := flag.String("out", "", "")
	flag.Parse()
	raw, e := os.ReadFile(*ready)
	if e != nil {
		panic(e)
	}
	xid, e := x11.ParseXID(string(raw))
	if e != nil {
		panic(e)
	}
	backend, e := x11.Open("")
	if e != nil {
		panic(e)
	}
	defer backend.Close()
	backend.RegisterTarget("fixture", xid)
	seq := int64(5)
	exp := backend.NowNS() + int64(5*time.Second)
	if *condition == "stale" {
		seq = 4
	}
	if *condition == "expired" {
		exp = 1
		time.Sleep(time.Millisecond)
	}
	ops := []core.Op{{Op: "focus", Target: "fixture"}, {Op: "key_state", Key: "A", Down: b(true)}, {Op: "pointer_move", Frame: "window_client", X: 100, Y: 100}, {Op: "pointer_button", Button: "left", Down: b(true)}, {Op: "pointer_button", Button: "left", Down: b(false)}, {Op: "release_all"}}
	if *condition == "unsupported_text" {
		ops = []core.Op{{Op: "focus", Target: "fixture"}, {Op: "text", Text: "office"}, {Op: "release_all"}}
	}
	p := core.Program{Schema: core.SchemaProgram, ProgramID: "x11-" + *condition, Source: core.Source{ObservationSeq: seq, BindingRevision: 1}, Authority: core.Authority{LeaseID: "x11-lease", ExpiresAtNS: exp}, Ops: ops, Terminal: core.Terminal{ReleaseAllRequired: true}}
	r := backend.Execute(p, 5, 1)
	f, e := os.Create(*out)
	if e != nil {
		panic(e)
	}
	defer f.Close()
	json.NewEncoder(f).Encode(map[string]any{"condition": *condition, "manifest": backend.Manifest(), "receipt": r})
}
