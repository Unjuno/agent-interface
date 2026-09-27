package main

import (
	core "agentinterface/nativecore"
	tp "agentinterface/nativetextpacing"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"sort"
	"time"
)

var corpus = []string{"office", "coffee", "bookkeeper", "committee", "parallel", "address", "success", "letterpress", "mississippi", "assessment", "committee", "bookkeeping", "ffffffffff", "aaaaaaaaaa", "tttttttttt", "ssssssssss"}

func down(v bool) *bool { return &v }
func program(id string, seq, rev, expires int64, ops []core.Op) core.Program {
	return core.Program{Schema: core.SchemaProgram, ProgramID: id, Source: core.Source{ObservationSeq: seq, BindingRevision: rev}, Authority: core.Authority{LeaseID: "native-text-pacing-v1", ExpiresAtNS: expires}, Ops: ops, Terminal: core.Terminal{ReleaseAllRequired: true}}
}
func median(v []int64) int64 {
	if len(v) == 0 {
		return 0
	}
	x := append([]int64(nil), v...)
	sort.Slice(x, func(i, j int) bool { return x[i] < x[j] })
	n := len(x)
	if n%2 == 1 {
		return x[n/2]
	}
	return (x[n/2-1] + x[n/2]) / 2
}

func main() {
	display := flag.String("display", "", "X display")
	xidText := flag.String("window-id", "", "target XID")
	pacingMS := flag.Float64("pacing-ms", 1, "pacing ms")
	out := flag.String("out", "", "output JSON")
	flag.Parse()
	xid, err := tp.ParseXID(*xidText)
	if err != nil {
		panic(err)
	}
	b, err := tp.Open(*display, time.Duration(*pacingMS*float64(time.Millisecond)))
	if err != nil {
		panic(err)
	}
	defer b.Close()
	b.RegisterTarget("calc", xid)
	now := b.NowNS()
	expires := now + 60_000_000_000
	stale := program("native-tight-stale", 4, 1, expires, []core.Op{{Op: "focus", Target: "calc"}, {Op: "text", Text: "x"}, {Op: "release_all"}})
	sr := b.Execute(stale, 5, 1)
	ops := []core.Op{{Op: "focus", Target: "calc"}, {Op: "pointer_move", Frame: "window_client", X: 80, Y: 180}, {Op: "pointer_button", Button: "left", Down: down(true)}, {Op: "pointer_button", Button: "left", Down: down(false)}, {Op: "key_chord", Keys: []string{"CTRL", "Home"}}}
	for _, s := range corpus {
		ops = append(ops, core.Op{Op: "text", Text: s}, core.Op{Op: "key_chord", Keys: []string{"ENTER"}})
	}
	ops = append(ops, core.Op{Op: "key_chord", Keys: []string{"CTRL", "S"}}, core.Op{Op: "release_all"})
	task := program(fmt.Sprintf("native-tight-%dus", int(*pacingMS*1000)), 5, 1, expires, ops)
	t0 := time.Now()
	tr := b.Execute(task, 5, 1)
	editNS := time.Since(t0).Nanoseconds()
	time.Sleep(400 * time.Millisecond)
	confirm := program("native-tight-confirm", 5, 1, expires, []core.Op{{Op: "key_chord", Keys: []string{"ENTER"}}, {Op: "release_all"}})
	cr := b.Execute(confirm, 5, 1)
	time.Sleep(1200 * time.Millisecond)
	result := map[string]any{"schema": "agent-interface/native-x11-tight-text-pacing-execution-v1", "pacing_ms": *pacingMS, "corpus": corpus, "stale": sr, "task": tr, "confirm": cr, "edit_elapsed_ns": editNS, "median_char_call_ns": median(tr.TextCharDurationsNS), "median_char_start_interval_ns": median(tr.TextCharStartIntervalsNS), "manifest": b.Manifest()}
	passed := !sr.Accepted && sr.Error == "STALE_OBSERVATION" && sr.InjectedEvents == 0 && tr.Accepted && tr.Error == "" && tr.FinalReleaseVerified && cr.Accepted && cr.Error == "" && cr.FinalReleaseVerified
	result["passed_transport"] = passed
	data, _ := json.MarshalIndent(result, "", "  ")
	data = append(data, '\n')
	if *out != "" {
		if err := os.WriteFile(*out, data, 0644); err != nil {
			panic(err)
		}
	}
	os.Stdout.Write(data)
	if !passed {
		os.Exit(1)
	}
}
