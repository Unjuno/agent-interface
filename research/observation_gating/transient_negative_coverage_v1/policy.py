"""Non-authoritative historical cue evidence; no access to fixture/oracle labels."""

def classify(trace: dict) -> dict:
    answer = {"status": "UNKNOWN_BINDING", "max_gap_ns": None, "grants_input_authority": False}
    try:
        if trace["clock"] != "CLOCK_MONOTONIC" or not isinstance(trace["surface"], str) or not trace["surface"]:
            return answer
        start, end = trace["start_ns"], trace["end_ns"]
        if type(start) is not int or type(end) is not int or not 0 <= start <= end:
            return answer
        samples = trace["samples"]
        if not isinstance(samples, list) or not samples:
            return answer
        last_end = start
        for s in samples:
            if s["surface"] != trace["surface"] or s["clock"] != trace["clock"]:
                return answer
            if any(type(s[k]) is not int for k in ("a", "b", "count")):
                return answer
            if not last_end <= s["a"] <= s["b"] <= end or not 0 <= s["count"] <= 1024:
                return answer
            last_end = s["b"]
        gaps = [samples[0]["b"]-start, end-samples[-1]["a"]]
        gaps += [q["b"]-p["a"] for p, q in zip(samples, samples[1:])]
        answer["max_gap_ns"] = max(gaps)
        if any(s["count"] >= 512 for s in samples):
            answer["status"] = "SEEN"
        elif type(trace.get("min_duration_ns")) is not int or trace["min_duration_ns"] <= 0:
            answer["status"] = "UNKNOWN_DURATION"
        elif max(gaps) < trace["min_duration_ns"]:
            answer["status"] = "ABSENT_MIN_DURATION"
        else:
            answer["status"] = "UNKNOWN_COVERAGE"
        return answer
    except (KeyError, TypeError, ValueError, IndexError):
        return answer
