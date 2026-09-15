package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"os"
)

type receipt struct {
	Condition string `json:"condition"`
	Manifest  struct {
		Capabilities map[string]struct {
			State string `json:"state"`
		} `json:"capabilities"`
	} `json:"manifest"`
	Receipt struct {
		Accepted bool   `json:"accepted"`
		Error    string `json:"error"`
		Injected int    `json:"injected_events"`
		Focus    bool   `json:"focus_verified"`
		Key      bool   `json:"key_down_observed"`
		Pointer  bool   `json:"pointer_verified"`
		Changed  bool   `json:"capture_changed"`
		Release  bool   `json:"final_release_verified"`
	} `json:"receipt"`
}

func lines(p string) ([]map[string]any, error) {
	f, e := os.Open(p)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	out := []map[string]any{}
	s := bufio.NewScanner(f)
	for s.Scan() {
		var r map[string]any
		if e = json.Unmarshal(s.Bytes(), &r); e != nil {
			return nil, e
		}
		out = append(out, r)
	}
	return out, s.Err()
}
func load(p string) (receipt, error) {
	var r receipt
	b, e := os.ReadFile(p)
	if e != nil {
		return r, e
	}
	e = json.Unmarshal(b, &r)
	return r, e
}
func main() {
	validL := flag.String("valid-ledger", "", "")
	staleL := flag.String("stale-ledger", "", "")
	expiredL := flag.String("expired-ledger", "", "")
	unsupportedL := flag.String("unsupported-ledger", "", "")
	validR := flag.String("valid-receipt", "", "")
	staleR := flag.String("stale-receipt", "", "")
	expiredR := flag.String("expired-receipt", "", "")
	unsupportedR := flag.String("unsupported-receipt", "", "")
	out := flag.String("out", "", "")
	flag.Parse()
	vl, e := lines(*validL)
	if e != nil {
		panic(e)
	}
	sl, _ := lines(*staleL)
	el, _ := lines(*expiredL)
	ul, _ := lines(*unsupportedL)
	vr, e := load(*validR)
	if e != nil {
		panic(e)
	}
	sr, _ := load(*staleR)
	er, _ := load(*expiredR)
	ur, _ := load(*unsupportedR)
	counts := map[string]int{}
	for _, row := range vl {
		if x, ok := row["event"].(string); ok {
			counts[x]++
		}
	}
	checks := map[string]bool{"valid_admitted": vr.Receipt.Accepted, "focus_verified": vr.Receipt.Focus, "key_down_observed": vr.Receipt.Key, "pointer_verified": vr.Receipt.Pointer, "capture_changed": vr.Receipt.Changed, "release_verified": vr.Receipt.Release, "valid_key_press": counts["key_press"] >= 1, "valid_key_release": counts["key_release"] >= 1, "valid_button_press": counts["button_press"] >= 1, "valid_button_release": counts["button_release"] >= 1, "stale_rejected": !sr.Receipt.Accepted && sr.Receipt.Error == "STALE_OBSERVATION" && sr.Receipt.Injected == 0, "expired_rejected": !er.Receipt.Accepted && er.Receipt.Error == "LEASE_EXPIRED" && er.Receipt.Injected == 0, "unsupported_text_rejected": !ur.Receipt.Accepted && ur.Receipt.Error == "UNSUPPORTED_CAPABILITY" && ur.Receipt.Injected == 0, "stale_private_effects_zero": len(sl) == 0, "expired_private_effects_zero": len(el) == 0, "unsupported_private_effects_zero": len(ul) == 0, "text_explicitly_unsupported": vr.Manifest.Capabilities["input.text"].State == "unsupported", "scroll_explicitly_unsupported": vr.Manifest.Capabilities["input.scroll"].State == "unsupported", "event_feedback_explicitly_unsupported": vr.Manifest.Capabilities["event.feedback"].State == "unsupported"}
	pass := true
	for _, v := range checks {
		pass = pass && v
	}
	f, _ := os.Create(*out)
	defer f.Close()
	json.NewEncoder(f).Encode(map[string]any{"schema": "agent-interface/native-x11-score-v0", "passed": pass, "checks": checks, "valid_private_event_counts": counts, "valid_injected_events": vr.Receipt.Injected, "office_ready": false, "known_blockers": []string{"input.text", "input.scroll", "event.feedback"}})
}
