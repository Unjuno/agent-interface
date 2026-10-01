package nativecore

import (
	"reflect"
	"testing"
)

func TestC1RoundtripRepresentative(t *testing.T) {
	p := baseProgram()
	s, e := EncodeC1(p)
	if e != nil {
		t.Fatal(e)
	}
	q, e := DecodeC1(s)
	if e != nil {
		t.Fatal(e)
	}
	if !reflect.DeepEqual(p, q) {
		t.Fatalf("roundtrip mismatch\n%#v\n%#v", p, q)
	}
}
func TestC1RoundtripTextEscapes(t *testing.T) {
	p := baseProgram()
	p.Ops = []Op{{Op: "text", Text: "a;\\\"東京"}, {Op: "verify", Predicate: "x;y"}, {Op: "release_all"}}
	s, e := EncodeC1(p)
	if e != nil {
		t.Fatal(e)
	}
	q, e := DecodeC1(s)
	if e != nil {
		t.Fatal(e)
	}
	if !reflect.DeepEqual(p, q) {
		t.Fatal("mismatch")
	}
}
func TestC1RejectsUnknownOpcode(t *testing.T) {
	if _, e := DecodeC1("A0|p|1|1|l|9|Z:x;R"); e == nil {
		t.Fatal("accepted unknown opcode")
	}
}
func TestC1RejectsReleaseThenInput(t *testing.T) {
	if _, e := DecodeC1("A0|p|1|1|l|9|R;T:\"x\""); e == nil {
		t.Fatal("accepted op after release")
	}
}

func TestC1PythonCompatibleStringEscapes(t *testing.T) {
	cases := []struct{ in, want string }{
		{"<&>", `"<&>"`},
		{"東京", `"東京"`},
		{"a;\\\"x", `"a;\\\"x"`},
		{"\u2028", "\"" + string(rune(0x2028)) + "\""},
		{"\u2029", "\"" + string(rune(0x2029)) + "\""},
		{"\x01\n", `"\u0001\n"`},
	}
	for _, tc := range cases {
		got, err := quotePythonJSON(tc.in)
		if err != nil {
			t.Fatal(err)
		}
		if got != tc.want {
			t.Fatalf("%q: got %q want %q", tc.in, got, tc.want)
		}
	}
}

func TestC1GoldenWireVector(t *testing.T) {
	p := baseProgram()
	p.ProgramID = "golden"
	p.Ops = []Op{{Op: "text", Text: "<&>;東京\u2028"}, {Op: "verify", Predicate: "x;y"}, {Op: "release_all"}}
	got, err := EncodeC1(p)
	if err != nil {
		t.Fatal(err)
	}
	want := "A0|golden|5|1|lease|1000000|T:\"<&>;東京" + string(rune(0x2028)) + "\";V:\"x;y\";R"
	if got != want {
		t.Fatalf("wire mismatch\ngot:  %s\nwant: %s", got, want)
	}
	q, err := DecodeC1(got)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(p, q) {
		t.Fatal("golden roundtrip mismatch")
	}
}
