#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import subprocess
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_BIN = ROOT / "build" / "facility"
ALLOWED = {"KD", "KU", "MOUSE", "PD", "PM", "PU", "TEXT", "STEP"}


@dataclass
class World:
    proc: subprocess.Popen
    frame_dir: pathlib.Path
    private_report: pathlib.Path
    latest: dict

    @classmethod
    def start(cls, binary: pathlib.Path, seed: int, difficulty: float, sets: list[str], frame_dir: pathlib.Path, report: pathlib.Path):
        cmd = [str(binary), "--stdio", "--seed", str(seed), "--difficulty", str(difficulty)]
        for item in sets:
            cmd += ["--set", item]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        first = json.loads(proc.stdout.readline())
        return cls(proc, frame_dir, report, first)

    def command(self, cmd: str) -> dict:
        assert self.proc.stdin and self.proc.stdout
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("world process exited")
            if line.startswith("{"):
                self.latest = json.loads(line)
                return self.latest

    def snapshot(self, cycle: int) -> pathlib.Path:
        path = self.frame_dir / f"frame-{cycle:06d}.ppm"
        self.command(f"SNAP {path}")
        return path

    def finish(self):
        self.command(f"REPORT {self.private_report}")
        assert self.proc.stdin
        self.proc.stdin.write("QUIT\n")
        self.proc.stdin.flush()
        self.proc.wait(timeout=5)


def validate_command(cmd: str) -> str:
    op = cmd.split(maxsplit=1)[0] if cmd.strip() else ""
    if op not in ALLOWED:
        raise ValueError(f"controller command not allowed: {cmd!r}")
    if op == "STEP":
        parts = cmd.split()
        if len(parts) != 2 or not parts[1].isdigit() or not (1 <= int(parts[1]) <= 12):
            raise ValueError(f"STEP must be 1..12: {cmd!r}")
    return cmd


def start_controller(command: str):
    return subprocess.Popen(shlex.split(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)


def run_arm(binary: pathlib.Path, seed: int, difficulty: float, sets: list[str], controller_cmd: str, root: pathlib.Path, label: str, max_cycles: int) -> dict:
    frame_dir = root / label / "frames"
    frame_dir.mkdir(parents=True)
    report = root / label / "private-report.json"
    world = World.start(binary, seed, difficulty, sets, frame_dir, report)
    ctl = start_controller(controller_cmd)
    try:
        for cycle in range(max_cycles):
            frame = world.snapshot(cycle)
            obs = {
                "schema": "facility-controller-observation-v0",
                "frame": str(frame),
                "tick": world.latest["tick"],
                "done": world.latest["done"],
            }
            assert ctl.stdin and ctl.stdout
            ctl.stdin.write(json.dumps(obs) + "\n")
            ctl.stdin.flush()
            line = ctl.stdout.readline()
            if not line:
                raise RuntimeError(f"controller {label} exited early")
            reply = json.loads(line)
            commands = [validate_command(str(c)) for c in reply.get("commands", [])]
            if not commands and not world.latest["done"]:
                commands = ["STEP 1"]
            stepped = False
            for command in commands:
                world.command(command)
                stepped |= command.startswith("STEP ")
                if world.latest["done"]:
                    break
            if not stepped and not world.latest["done"]:
                world.command("STEP 1")
            if world.latest["done"]:
                break
        world.finish()
        return json.loads(report.read_text())
    finally:
        if ctl.poll() is None:
            ctl.terminate()
        try:
            ctl.wait(timeout=2)
        except subprocess.TimeoutExpired:
            ctl.kill()
        if world.proc.poll() is None:
            world.proc.kill()


def main() -> int:
    p = argparse.ArgumentParser(description="Seed-paired external-controller harness for Procedural Operations Facility v0")
    p.add_argument("--binary", type=pathlib.Path, default=DEFAULT_BIN)
    p.add_argument("--seeds", type=pathlib.Path, default=ROOT / "seeds" / "regression.txt")
    p.add_argument("--difficulty", type=float, default=0.5)
    p.add_argument("--set", action="append", default=[])
    p.add_argument("--left", required=True, help="controller command for B0/left arm")
    p.add_argument("--right", required=True, help="controller command for C1/right arm")
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--max-cycles", type=int, default=10000)
    args = p.parse_args()

    seeds = [int(x) for x in args.seeds.read_text().split() if x.strip()]
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for ordinal, seed in enumerate(seeds):
        pair_dir = args.output / f"pair-{ordinal:04d}"
        pair_dir.mkdir()
        order = [("left", args.left), ("right", args.right)] if ordinal % 2 == 0 else [("right", args.right), ("left", args.left)]
        reports = {}
        for label, cmd in order:
            reports[label] = run_arm(args.binary, seed, args.difficulty, args.set, cmd, pair_dir, label, args.max_cycles)
        if reports["left"].get("seed") != reports["right"].get("seed") or reports["left"].get("spec_hash") != reports["right"].get("spec_hash"):
            raise RuntimeError("paired episode identity mismatch")
        rows.append({
            "ordinal": ordinal,
            "seed": seed,
            "spec_hash": reports["left"]["spec_hash"],
            "left": {
                "success": reports["left"]["success"],
                "failure_reason": reports["left"]["failure_reason"],
                "tick": reports["left"]["tick"],
            },
            "right": {
                "success": reports["right"]["success"],
                "failure_reason": reports["right"]["failure_reason"],
                "tick": reports["right"]["tick"],
            },
        })

    summary = {"schema": "facility-paired-run-v0", "difficulty": args.difficulty, "sets": args.set, "pairs": rows}
    (args.output / "paired-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"pairs": len(rows), "output": str(args.output / "paired-summary.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
