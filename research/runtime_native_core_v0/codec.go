package nativecore

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"
)

func boolp(v bool) *bool { return &v }

func quotePythonJSON(s string) (string, error) {
	if !utf8.ValidString(s) {
		return "", fmt.Errorf("text must be valid UTF-8")
	}
	var b strings.Builder
	b.WriteByte('"')
	hex := "0123456789abcdef"
	for _, r := range s {
		switch r {
		case '"':
			b.WriteString("\\\"")
		case '\\':
			b.WriteString("\\\\")
		case '\b':
			b.WriteString("\\b")
		case '\f':
			b.WriteString("\\f")
		case '\n':
			b.WriteString("\\n")
		case '\r':
			b.WriteString("\\r")
		case '\t':
			b.WriteString("\\t")
		default:
			if r < 0x20 {
				b.WriteString("\\u00")
				b.WriteByte(hex[(r>>4)&0xf])
				b.WriteByte(hex[r&0xf])
			} else {
				b.WriteRune(r)
			}
		}
	}
	b.WriteByte('"')
	return b.String(), nil
}

func EncodeC1(p Program) (string, error) {
	if err := ValidateProgram(p); err != nil {
		return "", err
	}
	if !identRE.MatchString(p.ProgramID) || !identRE.MatchString(p.Authority.LeaseID) {
		return "", fmt.Errorf("invalid identifier")
	}
	ops := make([]string, 0, len(p.Ops))
	for _, op := range p.Ops {
		switch op.Op {
		case "focus":
			ops = append(ops, "F:"+op.Target)
		case "key_chord":
			ops = append(ops, "K:"+strings.Join(op.Keys, "+"))
		case "key_state":
			if *op.Down {
				ops = append(ops, "D:"+op.Key)
			} else {
				ops = append(ops, "U:"+op.Key)
			}
		case "text":
			q, err := quotePythonJSON(op.Text)
			if err != nil {
				return "", err
			}
			ops = append(ops, "T:"+q)
		case "pointer_move":
			ops = append(ops, fmt.Sprintf("M:%s,%d,%d", op.Frame, op.X, op.Y))
		case "pointer_button":
			if *op.Down {
				ops = append(ops, "B+:"+op.Button)
			} else {
				ops = append(ops, "B-:"+op.Button)
			}
		case "scroll":
			ops = append(ops, fmt.Sprintf("S:%d,%d", op.DX, op.DY))
		case "observe":
			ops = append(ops, fmt.Sprintf("O:%s,%d,%d,%d,%d", op.Frame, op.X, op.Y, op.W, op.H))
		case "wait_update":
			ops = append(ops, fmt.Sprintf("W:%d", op.TimeoutMS))
		case "verify":
			q, err := quotePythonJSON(op.Predicate)
			if err != nil {
				return "", err
			}
			ops = append(ops, "V:"+q)
		case "release_all":
			ops = append(ops, "R")
		default:
			return "", fmt.Errorf("unsupported op")
		}
	}
	return fmt.Sprintf("A0|%s|%d|%d|%s|%d|%s", p.ProgramID, p.Source.ObservationSeq, p.Source.BindingRevision, p.Authority.LeaseID, p.Authority.ExpiresAtNS, strings.Join(ops, ";")), nil
}

func splitOps(s string) ([]string, error) {
	out := []string{}
	var b strings.Builder
	quoted := false
	escaped := false
	for _, r := range s {
		if escaped {
			b.WriteRune(r)
			escaped = false
			continue
		}
		if quoted && r == '\\' {
			b.WriteRune(r)
			escaped = true
			continue
		}
		if r == '"' {
			quoted = !quoted
			b.WriteRune(r)
			continue
		}
		if r == ';' && !quoted {
			if b.Len() == 0 {
				return nil, fmt.Errorf("empty operation token")
			}
			out = append(out, b.String())
			b.Reset()
			continue
		}
		b.WriteRune(r)
	}
	if quoted {
		return nil, fmt.Errorf("unterminated quoted string")
	}
	if b.Len() > 0 {
		out = append(out, b.String())
	} else if s != "" {
		return nil, fmt.Errorf("trailing operation separator")
	}
	return out, nil
}

func DecodeC1(payload string) (Program, error) {
	parts := strings.SplitN(payload, "|", 7)
	if len(parts) != 7 || parts[0] != "A0" {
		return Program{}, fmt.Errorf("invalid C1 header")
	}
	seq, e1 := strconv.ParseInt(parts[2], 10, 64)
	rev, e2 := strconv.ParseInt(parts[3], 10, 64)
	exp, e3 := strconv.ParseInt(parts[5], 10, 64)
	if e1 != nil || e2 != nil || e3 != nil {
		return Program{}, fmt.Errorf("invalid C1 integer")
	}
	tokens, err := splitOps(parts[6])
	if err != nil {
		return Program{}, err
	}
	ops := []Op{}
	for _, tok := range tokens {
		if tok == "R" {
			ops = append(ops, Op{Op: "release_all"})
			continue
		}
		i := strings.Index(tok, ":")
		if i < 0 {
			return Program{}, fmt.Errorf("operation missing ':'")
		}
		code, p := tok[:i], tok[i+1:]
		switch code {
		case "F":
			ops = append(ops, Op{Op: "focus", Target: p})
		case "K":
			ops = append(ops, Op{Op: "key_chord", Keys: strings.Split(p, "+")})
		case "D":
			ops = append(ops, Op{Op: "key_state", Key: p, Down: boolp(true)})
		case "U":
			ops = append(ops, Op{Op: "key_state", Key: p, Down: boolp(false)})
		case "T":
			var s string
			if json.Unmarshal([]byte(p), &s) != nil {
				return Program{}, fmt.Errorf("invalid quoted string")
			}
			ops = append(ops, Op{Op: "text", Text: s})
		case "M":
			a := strings.Split(p, ",")
			if len(a) != 3 {
				return Program{}, fmt.Errorf("pointer_move arity")
			}
			x, e := strconv.Atoi(a[1])
			if e != nil {
				return Program{}, e
			}
			y, e := strconv.Atoi(a[2])
			if e != nil {
				return Program{}, e
			}
			ops = append(ops, Op{Op: "pointer_move", Frame: a[0], X: x, Y: y})
		case "B+":
			ops = append(ops, Op{Op: "pointer_button", Button: p, Down: boolp(true)})
		case "B-":
			ops = append(ops, Op{Op: "pointer_button", Button: p, Down: boolp(false)})
		case "S":
			a := strings.Split(p, ",")
			if len(a) != 2 {
				return Program{}, fmt.Errorf("scroll arity")
			}
			dx, e := strconv.Atoi(a[0])
			if e != nil {
				return Program{}, e
			}
			dy, e := strconv.Atoi(a[1])
			if e != nil {
				return Program{}, e
			}
			ops = append(ops, Op{Op: "scroll", DX: dx, DY: dy})
		case "O":
			a := strings.Split(p, ",")
			if len(a) != 5 {
				return Program{}, fmt.Errorf("observe arity")
			}
			nums := make([]int, 4)
			for j := 0; j < 4; j++ {
				v, e := strconv.Atoi(a[j+1])
				if e != nil {
					return Program{}, e
				}
				nums[j] = v
			}
			ops = append(ops, Op{Op: "observe", Frame: a[0], X: nums[0], Y: nums[1], W: nums[2], H: nums[3]})
		case "W":
			v, e := strconv.Atoi(p)
			if e != nil {
				return Program{}, e
			}
			ops = append(ops, Op{Op: "wait_update", TimeoutMS: v})
		case "V":
			var s string
			if json.Unmarshal([]byte(p), &s) != nil {
				return Program{}, fmt.Errorf("invalid verify string")
			}
			ops = append(ops, Op{Op: "verify", Predicate: s})
		default:
			return Program{}, fmt.Errorf("unknown opcode %s", code)
		}
	}
	pr := Program{Schema: SchemaProgram, ProgramID: parts[1], Source: Source{seq, rev}, Authority: Authority{parts[4], exp}, Ops: ops, Terminal: Terminal{true}}
	if err := ValidateProgram(pr); err != nil {
		return Program{}, err
	}
	return pr, nil
}
