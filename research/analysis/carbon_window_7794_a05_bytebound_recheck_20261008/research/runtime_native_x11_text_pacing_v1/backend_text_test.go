package nativetextpacing

import (
	core "agentinterface/nativecore"
	"testing"
)

func TestTextSubset(t *testing.T) {
	good := core.Program{Ops: []core.Op{{Op: "text", Text: "coffee"}}}
	if !textSubsetOK(good) {
		t.Fatal("lowercase text rejected")
	}
	for _, s := range []string{"Office", "a b", "café", "1"} {
		p := core.Program{Ops: []core.Op{{Op: "text", Text: s}}}
		if textSubsetOK(p) {
			t.Fatalf("unsupported subset accepted: %q", s)
		}
	}
}
