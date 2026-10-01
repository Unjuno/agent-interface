package nativecore

import "testing"

func b(v bool) *bool { return &v }

func baseProgram() Program {
	return Program{Schema: SchemaProgram, ProgramID: "portable", Source: Source{5, 1}, Authority: Authority{"lease", 1000000}, Ops: []Op{{Op: "focus", Target: "editor"}, {Op: "pointer_move", Frame: "window_client", X: 10, Y: 20}, {Op: "pointer_button", Button: "left", Down: b(true)}, {Op: "pointer_button", Button: "left", Down: b(false)}, {Op: "text", Text: "office"}, {Op: "key_chord", Keys: []string{"CTRL", "S"}}, {Op: "wait_update", TimeoutMS: 500}, {Op: "release_all"}}, Terminal: Terminal{true}}
}
func fullManifest(os, backend string) Manifest {
	m := Manifest{Schema: SchemaBackend, BackendID: "synthetic-" + os, Capabilities: map[string]Capability{}, CoordinateFrames: []string{"screen_physical_px", "screen_logical", "window_client"}}
	m.Platform.OS = os
	m.Platform.Backend = backend
	m.Clock.Unit = "ns"
	m.Clock.Monotonic = true
	for c := range KnownCapabilities {
		m.Capabilities[c] = Capability{"unsupported", ""}
	}
	for _, c := range OfficeFloor {
		m.Capabilities[c] = Capability{"supported", ""}
	}
	return m
}

func TestRepresentativeAdmitsThreeSyntheticOSProfiles(t *testing.T) {
	p := baseProgram()
	for _, x := range [][2]string{{"linux", "x11"}, {"windows", "win32"}, {"macos", "quartz"}} {
		m := fullManifest(x[0], x[1])
		a := Admit(p, m, 1, 5, 1)
		if !a.Accepted {
			t.Fatalf("%s: %#v", x[0], a)
		}
	}
}
func TestStaleAndLeaseErrors(t *testing.T) {
	p := baseProgram()
	m := fullManifest("linux", "x11")
	if a := Admit(p, m, 1, 6, 1); a.Error != "STALE_OBSERVATION" {
		t.Fatal(a)
	}
	if a := Admit(p, m, 1, 5, 2); a.Error != "STALE_BINDING" {
		t.Fatal(a)
	}
	if a := Admit(p, m, 1000001, 5, 1); a.Error != "LEASE_EXPIRED" {
		t.Fatal(a)
	}
}
func TestReleaseAllMustBeExactlyOnceAndFinal(t *testing.T) {
	p := baseProgram()
	p.Ops = []Op{{Op: "release_all"}, {Op: "text", Text: "x"}}
	if ValidateProgram(p) == nil {
		t.Fatal("accepted operation after release_all")
	}
	p = baseProgram()
	p.Ops = append(p.Ops, Op{Op: "release_all"})
	if ValidateProgram(p) == nil {
		t.Fatal("accepted duplicate release_all")
	}
	p = baseProgram()
	p.Ops = p.Ops[:len(p.Ops)-1]
	if ValidateProgram(p) == nil {
		t.Fatal("accepted missing release_all")
	}
}
func TestHeldInputDiscipline(t *testing.T) {
	p := baseProgram()
	p.Ops = []Op{{Op: "key_state", Key: "SHIFT", Down: b(false)}, {Op: "release_all"}}
	if ValidateProgram(p) == nil {
		t.Fatal("accepted release of unheld key")
	}
	p = baseProgram()
	p.Ops = []Op{{Op: "key_state", Key: "SHIFT", Down: b(true)}, {Op: "key_state", Key: "SHIFT", Down: b(false)}, {Op: "release_all"}}
	if err := ValidateProgram(p); err != nil {
		t.Fatal(err)
	}
}
func TestCapabilityAndCoordinateFailures(t *testing.T) {
	p := baseProgram()
	m := fullManifest("linux", "x11")
	m.Capabilities["input.pointer"] = Capability{"permission_required", ""}
	if a := Admit(p, m, 1, 5, 1); a.Error != "PERMISSION_DENIED" {
		t.Fatal(a)
	}
	m = fullManifest("linux", "x11")
	m.Capabilities["input.pointer"] = Capability{"unsupported", ""}
	if a := Admit(p, m, 1, 5, 1); a.Error != "UNSUPPORTED_CAPABILITY" {
		t.Fatal(a)
	}
	m = fullManifest("linux", "x11")
	m.CoordinateFrames = []string{"screen_logical"}
	if a := Admit(p, m, 1, 5, 1); a.Error != "COORDINATE_UNSUPPORTED" {
		t.Fatal(a)
	}
}
