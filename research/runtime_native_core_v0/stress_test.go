package nativecore

import (
	"fmt"
	"math/rand"
	"reflect"
	"testing"
)

func TestDeterministicTenThousandProgramC1Roundtrip(t *testing.T) {
	rng := rand.New(rand.NewSource(20260915))
	texts := []string{"office", "東京", "<&>", "a;\\\"x", "line\nnext", "\u2028", "βeta", "invoice"}
	targets := []string{"editor", "spreadsheet", "browser", "mail"}
	for i := 0; i < 10000; i++ {
		ops := []Op{{Op: "focus", Target: targets[rng.Intn(len(targets))]}}
		switch i % 5 {
		case 0:
			ops = append(ops, Op{Op: "text", Text: fmt.Sprintf("%s-%d", texts[rng.Intn(len(texts))], i)}, Op{Op: "key_chord", Keys: []string{"CTRL", "S"}})
		case 1:
			ops = append(ops, Op{Op: "key_state", Key: "SHIFT", Down: b(true)}, Op{Op: "key_state", Key: "SHIFT", Down: b(false)}, Op{Op: "verify", Predicate: "state_changed"})
		case 2:
			ops = append(ops, Op{Op: "pointer_move", Frame: "screen_physical_px", X: rng.Intn(1920), Y: rng.Intn(1080)}, Op{Op: "pointer_button", Button: "left", Down: b(true)}, Op{Op: "pointer_button", Button: "left", Down: b(false)})
		case 3:
			ops = append(ops, Op{Op: "scroll", DX: 0, DY: []int{-3, -1, 1, 3}[rng.Intn(4)]}, Op{Op: "observe", Frame: "window_client", X: 0, Y: 0, W: 640, H: 480})
		case 4:
			ops = append(ops, Op{Op: "wait_update", TimeoutMS: 250}, Op{Op: "verify", Predicate: "ready;exact"})
		}
		ops = append(ops, Op{Op: "release_all"})
		p := Program{Schema: SchemaProgram, ProgramID: fmt.Sprintf("p%d", i), Source: Source{int64(i), 1}, Authority: Authority{"stress-lease", 999999999999}, Ops: ops, Terminal: Terminal{true}}
		wire, err := EncodeC1(p)
		if err != nil {
			t.Fatalf("encode %d: %v", i, err)
		}
		got, err := DecodeC1(wire)
		if err != nil {
			t.Fatalf("decode %d: %v", i, err)
		}
		if !reflect.DeepEqual(p, got) {
			t.Fatalf("roundtrip %d mismatch", i)
		}
	}
}
