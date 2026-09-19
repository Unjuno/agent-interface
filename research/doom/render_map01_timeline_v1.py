"""Render a timing-faithful MAP01 observation trace with controller telemetry."""
import argparse
import bisect
import json
from pathlib import Path

import cv2


def host_path(value: str) -> Path:
    if value.startswith("/mnt/c/"):
        return Path("C:/" + value[len("/mnt/c/"):])
    return Path(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--playback-speed", type=float, default=1.0)
    args = parser.parse_args()
    report = json.loads((args.run / "report.json").read_text())
    events = [json.loads(line) for line in
              (args.run / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    assert observations
    captures = [row["capture_ns"] for row in observations]
    start_ns = captures[0]
    end_ns = report["score"]["emit_ns"]
    model_intervals = [(row["controller_model_started_ns"],
                        row["controller_model_ended_ns"], row["iteration"])
                       for row in report["decisions"]
                       if "controller_model_started_ns" in row]
    accepted = {row["id"]: row["accepted_ns"] for row in events
                if row.get("event") == "accepted"}
    programs = [(accepted[row["id"]], row["terminal_ns"], row["id"])
                for row in events if row.get("event") == "terminal"
                and row.get("id") in accepted]
    sample = cv2.imread(str(host_path(observations[0]["image"])))
    assert sample is not None
    geometry = observations[0]["pointer_binding"]["geometry"]
    left, top, width, height = geometry
    canvas_size = (width, height + 80)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(args.output), cv2.VideoWriter_fourcc(*"mp4v"),
                             args.fps, canvas_size)
    assert writer.isOpened()
    duration_s = (end_ns - start_ns) / 1e9
    frame_count = int(duration_s / args.playback_speed * args.fps) + args.fps * 3
    for output_index in range(frame_count):
        source_s = min(output_index / args.fps * args.playback_speed, duration_s)
        now_ns = start_ns + int(source_s * 1e9)
        obs_index = max(0, bisect.bisect_right(captures, now_ns) - 1)
        frame = cv2.imread(str(host_path(observations[obs_index]["image"])))
        crop = frame[top:top + height, left:left + width]
        canvas = cv2.copyMakeBorder(crop, 80, 0, 0, 0, cv2.BORDER_CONSTANT,
                                    value=(12, 12, 12))
        model = next(((iteration, a, b) for a, b, iteration in model_intervals
                      if a <= now_ns <= b), None)
        program = next((identifier for a, b, identifier in programs if a <= now_ns <= b), None)
        phase = "MODEL THINKING + LOCAL COVER" if model else "LOCAL PLAN / FEEDBACK"
        decision = model[0] if model else min(report["iterations"] - 1,
                                               sum(a <= now_ns for a, _, _ in model_intervals) - 1)
        cv2.putText(canvas, f"MAP01 live | {source_s:06.1f}s | decision {max(0, decision)}",
                    (12, 25), cv2.FONT_HERSHEY_SIMPLEX, .62, (245, 245, 245), 1,
                    cv2.LINE_AA)
        cv2.putText(canvas, phase, (12, 51), cv2.FONT_HERSHEY_SIMPLEX, .58,
                    (80, 220, 255) if model else (120, 255, 120), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"ASYNC 35 tic/s | input: {program or 'none'} | playback {args.playback_speed:g}x",
                    (12, 73), cv2.FONT_HERSHEY_SIMPLEX, .45, (210, 210, 210), 1,
                    cv2.LINE_AA)
        if source_s >= duration_s:
            text = ("OUTCOME: MAP01 NOT CLEARED | DEATH 1 | KILL 1"
                    if report["score"]["player_dead"] else "OUTCOME RECORDED")
            cv2.rectangle(canvas, (0, 290), (width, 350), (0, 0, 0), -1)
            cv2.putText(canvas, text, (28, 328), cv2.FONT_HERSHEY_SIMPLEX, .58,
                        (255, 255, 255), 1, cv2.LINE_AA)
        writer.write(canvas)
    writer.release()
    assert args.output.exists() and args.output.stat().st_size > 0
    print(args.output)


if __name__ == "__main__":
    main()
