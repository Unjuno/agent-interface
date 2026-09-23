package nativecore

import (
	"fmt"
	"regexp"
	"sort"
)

const (
	SchemaBackend = "agent-interface/backend-v0"
	SchemaProgram = "agent-interface/program-v0"
)

var KnownCapabilities = map[string]bool{
	"capture.frame": true, "input.keyboard": true, "input.text": true,
	"input.pointer": true, "input.scroll": true, "input.release_all": true,
	"window.focus": true, "display.geometry": true, "clock.monotonic": true,
	"event.feedback": true, "clipboard.read": true, "clipboard.write": true,
	"window.enumerate": true, "accessibility.query": true,
}

var OfficeFloor = []string{
	"capture.frame", "input.keyboard", "input.text", "input.pointer", "input.scroll",
	"input.release_all", "window.focus", "display.geometry", "clock.monotonic", "event.feedback",
}

var identRE = regexp.MustCompile(`^[A-Za-z0-9._-]{1,64}$`)
var keyRE = regexp.MustCompile(`^[A-Za-z0-9._+-]{1,32}$`)

var coordinateFrames = map[string]bool{"screen_physical_px": true, "screen_logical": true, "window_client": true}
var buttons = map[string]bool{"left": true, "middle": true, "right": true, "x1": true, "x2": true}
var capStates = map[string]bool{"supported": true, "unsupported": true, "unknown": true, "permission_required": true}

// Manifest mirrors the language-neutral backend capability document.
type Manifest struct {
	Schema    string `json:"schema"`
	BackendID string `json:"backend_id"`
	Platform  struct {
		OS      string `json:"os"`
		Backend string `json:"backend"`
	} `json:"platform"`
	Capabilities     map[string]Capability `json:"capabilities"`
	CoordinateFrames []string              `json:"coordinate_frames"`
	Clock            struct {
		Unit      string `json:"unit"`
		Monotonic bool   `json:"monotonic"`
	} `json:"clock"`
	Permissions []string `json:"permissions"`
}

type Capability struct {
	State  string `json:"state"`
	Detail string `json:"detail"`
}

type Program struct {
	Schema    string    `json:"schema"`
	ProgramID string    `json:"program_id"`
	Source    Source    `json:"source"`
	Authority Authority `json:"authority"`
	Ops       []Op      `json:"ops"`
	Terminal  Terminal  `json:"terminal"`
}

type Source struct {
	ObservationSeq  int64 `json:"observation_seq"`
	BindingRevision int64 `json:"binding_revision"`
}
type Authority struct {
	LeaseID     string `json:"lease_id"`
	ExpiresAtNS int64  `json:"expires_at_ns"`
}
type Terminal struct {
	ReleaseAllRequired bool `json:"release_all_required"`
}

type Op struct {
	Op        string   `json:"op"`
	Target    string   `json:"target,omitempty"`
	Keys      []string `json:"keys,omitempty"`
	Key       string   `json:"key,omitempty"`
	Down      *bool    `json:"down,omitempty"`
	Text      string   `json:"text,omitempty"`
	Frame     string   `json:"frame,omitempty"`
	X         int      `json:"x,omitempty"`
	Y         int      `json:"y,omitempty"`
	W         int      `json:"w,omitempty"`
	H         int      `json:"h,omitempty"`
	Button    string   `json:"button,omitempty"`
	DX        int      `json:"dx,omitempty"`
	DY        int      `json:"dy,omitempty"`
	TimeoutMS int      `json:"timeout_ms,omitempty"`
	Predicate string   `json:"predicate,omitempty"`
}

type Admission struct {
	Accepted             bool     `json:"accepted"`
	Error                string   `json:"error,omitempty"`
	RequiredCapabilities []string `json:"required_capabilities"`
}

func ValidateManifest(m Manifest) error {
	if m.Schema != SchemaBackend {
		return fmt.Errorf("backend schema mismatch")
	}
	if !identRE.MatchString(m.BackendID) {
		return fmt.Errorf("invalid backend_id")
	}
	if m.Platform.OS != "linux" && m.Platform.OS != "windows" && m.Platform.OS != "macos" {
		return fmt.Errorf("unsupported os name")
	}
	if len(m.Platform.Backend) < 1 || len(m.Platform.Backend) > 48 {
		return fmt.Errorf("invalid platform backend")
	}
	for cap, row := range m.Capabilities {
		if !KnownCapabilities[cap] {
			return fmt.Errorf("unknown capability %s", cap)
		}
		if !capStates[row.State] {
			return fmt.Errorf("invalid state for %s", cap)
		}
		if len(row.Detail) > 256 {
			return fmt.Errorf("invalid detail for %s", cap)
		}
	}
	if len(m.CoordinateFrames) == 0 {
		return fmt.Errorf("coordinate_frames must be non-empty")
	}
	seen := map[string]bool{}
	for _, f := range m.CoordinateFrames {
		if !coordinateFrames[f] {
			return fmt.Errorf("unknown coordinate frame")
		}
		if seen[f] {
			return fmt.Errorf("duplicate coordinate frame")
		}
		seen[f] = true
	}
	if m.Clock.Unit != "ns" {
		return fmt.Errorf("clock unit must be ns")
	}
	return nil
}

func ValidateProgram(p Program) error {
	if p.Schema != SchemaProgram {
		return fmt.Errorf("program schema mismatch")
	}
	if !identRE.MatchString(p.ProgramID) {
		return fmt.Errorf("invalid program_id")
	}
	if p.Source.ObservationSeq < 0 || p.Source.BindingRevision < 0 {
		return fmt.Errorf("negative source version")
	}
	if !identRE.MatchString(p.Authority.LeaseID) {
		return fmt.Errorf("invalid lease_id")
	}
	if p.Authority.ExpiresAtNS < 1 {
		return fmt.Errorf("invalid expires_at_ns")
	}
	if !p.Terminal.ReleaseAllRequired {
		return fmt.Errorf("release_all_required must be true")
	}
	if len(p.Ops) < 1 || len(p.Ops) > 128 {
		return fmt.Errorf("ops length out of range")
	}

	heldKeys := map[string]bool{}
	heldButtons := map[string]bool{}
	releaseCount := 0
	for i, op := range p.Ops {
		switch op.Op {
		case "focus":
			if !identRE.MatchString(op.Target) {
				return fmt.Errorf("invalid focus target")
			}
		case "key_chord":
			if len(op.Keys) < 1 || len(op.Keys) > 5 {
				return fmt.Errorf("invalid chord keys")
			}
			seen := map[string]bool{}
			for _, k := range op.Keys {
				if !keyRE.MatchString(k) || seen[k] {
					return fmt.Errorf("invalid chord key")
				}
				seen[k] = true
			}
		case "key_state":
			if !keyRE.MatchString(op.Key) || op.Down == nil {
				return fmt.Errorf("invalid key_state")
			}
			if *op.Down {
				if heldKeys[op.Key] {
					return fmt.Errorf("key already held")
				}
				heldKeys[op.Key] = true
			} else {
				if !heldKeys[op.Key] {
					return fmt.Errorf("key released while not held")
				}
				delete(heldKeys, op.Key)
			}
		case "text":
			if len([]rune(op.Text)) > 16384 {
				return fmt.Errorf("invalid text")
			}
		case "pointer_move":
			if !coordinateFrames[op.Frame] || op.X < -1000000 || op.X > 1000000 || op.Y < -1000000 || op.Y > 1000000 {
				return fmt.Errorf("invalid pointer_move")
			}
		case "pointer_button":
			if !buttons[op.Button] || op.Down == nil {
				return fmt.Errorf("invalid pointer_button")
			}
			if *op.Down {
				if heldButtons[op.Button] {
					return fmt.Errorf("button already held")
				}
				heldButtons[op.Button] = true
			} else {
				if !heldButtons[op.Button] {
					return fmt.Errorf("button released while not held")
				}
				delete(heldButtons, op.Button)
			}
		case "scroll":
			if op.DX < -100000 || op.DX > 100000 || op.DY < -100000 || op.DY > 100000 {
				return fmt.Errorf("invalid scroll")
			}
		case "observe":
			if !coordinateFrames[op.Frame] || op.W < 1 || op.H < 1 || op.W > 1000000 || op.H > 1000000 {
				return fmt.Errorf("invalid observe")
			}
		case "wait_update":
			if op.TimeoutMS < 0 || op.TimeoutMS > 60000 {
				return fmt.Errorf("invalid wait_update")
			}
		case "verify":
			if len(op.Predicate) < 1 || len(op.Predicate) > 512 {
				return fmt.Errorf("invalid verify")
			}
		case "release_all":
			releaseCount++
			if i != len(p.Ops)-1 {
				return fmt.Errorf("release_all must be final operation")
			}
			heldKeys = map[string]bool{}
			heldButtons = map[string]bool{}
		default:
			return fmt.Errorf("unsupported op %s", op.Op)
		}
	}
	if releaseCount != 1 {
		return fmt.Errorf("release_all must appear exactly once")
	}
	if len(heldKeys) != 0 || len(heldButtons) != 0 {
		return fmt.Errorf("program terminates with held input")
	}
	return nil
}

func requiredForOp(op Op) []string {
	switch op.Op {
	case "key_chord", "key_state":
		return []string{"input.keyboard"}
	case "text":
		return []string{"input.text"}
	case "pointer_move", "pointer_button":
		return []string{"input.pointer", "display.geometry"}
	case "scroll":
		return []string{"input.scroll"}
	case "focus":
		return []string{"window.focus"}
	case "observe":
		return []string{"capture.frame", "display.geometry"}
	case "wait_update":
		return []string{"event.feedback", "clock.monotonic"}
	case "verify":
		return []string{"event.feedback"}
	case "release_all":
		return []string{"input.release_all"}
	}
	return nil
}

func RequiredCapabilities(p Program) ([]string, error) {
	if err := ValidateProgram(p); err != nil {
		return nil, err
	}
	set := map[string]bool{"input.release_all": true}
	for _, op := range p.Ops {
		for _, c := range requiredForOp(op) {
			set[c] = true
		}
	}
	out := make([]string, 0, len(set))
	for c := range set {
		out = append(out, c)
	}
	sort.Strings(out)
	return out, nil
}

func Admit(p Program, m Manifest, nowNS, currentSeq, currentRev int64) Admission {
	if err := ValidateProgram(p); err != nil {
		return Admission{false, "INVALID_PROGRAM", []string{}}
	}
	if err := ValidateManifest(m); err != nil {
		return Admission{false, "INVALID_PROGRAM", []string{}}
	}
	req, _ := RequiredCapabilities(p)
	if nowNS > p.Authority.ExpiresAtNS {
		return Admission{false, "LEASE_EXPIRED", req}
	}
	if p.Source.ObservationSeq != currentSeq {
		return Admission{false, "STALE_OBSERVATION", req}
	}
	if p.Source.BindingRevision != currentRev {
		return Admission{false, "STALE_BINDING", req}
	}
	for _, c := range req {
		state := "unknown"
		if row, ok := m.Capabilities[c]; ok {
			state = row.State
		}
		if state == "permission_required" {
			return Admission{false, "PERMISSION_DENIED", req}
		}
		if state != "supported" {
			return Admission{false, "UNSUPPORTED_CAPABILITY", req}
		}
	}
	frames := map[string]bool{}
	for _, f := range m.CoordinateFrames {
		frames[f] = true
	}
	for _, op := range p.Ops {
		if (op.Op == "pointer_move" || op.Op == "observe") && !frames[op.Frame] {
			return Admission{false, "COORDINATE_UNSUPPORTED", req}
		}
	}
	return Admission{true, "", req}
}

func OfficeReadiness(m Manifest) (bool, []string) {
	if ValidateManifest(m) != nil {
		return false, []string{"INVALID_MANIFEST"}
	}
	blocking := []string{}
	for _, c := range OfficeFloor {
		if row, ok := m.Capabilities[c]; !ok || row.State != "supported" {
			blocking = append(blocking, c)
		}
	}
	sort.Strings(blocking)
	return len(blocking) == 0, blocking
}
