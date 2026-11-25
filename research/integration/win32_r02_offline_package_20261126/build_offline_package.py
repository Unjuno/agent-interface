"""Build the R02 review package and exercise its entrypoint with inert stdio."""
from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from offline_taskserver import REQUIRED_TOOLS

HERE = Path(__file__).resolve().parent
R02 = HERE / "inputs/r02_candidate"
R44 = HERE / "inputs/frozen_parent"
PIN_FILE = HERE / "input_pins.json"
MANIFEST = "SHA256SUMS.txt"
STATIC_REFUSAL = "Static R44 candidate only; review, refreeze and explicitly authorize before live use."
COPY_TO_RUNNER_PATH = ("source/scorer.py", "source/foreground_probe.py", "task_oracle_server.py")
FROZEN_REFERENCE = {
    "conditions.json": "frozen_parent/conditions.json",
    "run_cohort.py": "frozen_parent/run_cohort.py.txt",
    "source/fixture_app.py": "frozen_parent/fixture_app.py.txt",
}
ID_FIELDS = ("trial_id", "program_id", "lease_id", "followup_program_id", "followup_lease_id")
GEOMETRY_FIELDS = (
    "ordinal", "source_window_position", "followup_window_position", "capture_frame",
    "capture_region", "authority_lease_ms", "horizon_ms", "effect_delay_ms",
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def pinned_input(root, name):
    # Frozen Python is stored as data so the originals cannot be imported by filename.
    return root / (name + ".txt" if name.endswith(".py") else name)


def load_pinned_inputs():
    pins = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    inputs = {}
    for label, source in (("frozen_parent", R44), ("r02_candidate", R02)):
        entries = inputs[label] = {}
        for name, expected in pins[label].items():
            data = pinned_input(source, name).read_bytes()
            if sha256(data) != expected:
                raise RuntimeError(f"{label} SHA-256 mismatch for {name}")
            entries[name] = data
    return inputs


def write_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)


def write_json(path, value):
    write_file(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def prospective_conditions(parent):
    if parent["trial"] != parent["trials"][0] or parent["order"] != [1, 2, 3, 4, 5]:
        raise RuntimeError("frozen R44 template shape changed")
    common = {
        "source_main": parent["source_main"],
        "order": parent["order"],
        "execution_authorized": False,
        "allocation": {
            "fixture_launches": 0, "dispatches": 0, "observations": 0,
            "recoveries": 0, "task_verifications": 0,
        },
    }
    templates = []
    trials = []
    used_parent_ids = {old[field] for old in parent["trials"] for field in ID_FIELDS}
    for trial, ordinal in zip(parent["trials"], parent["order"], strict=True):
        if trial["ordinal"] != ordinal:
            raise RuntimeError("frozen R44 trial order changed")
        template = {key: trial[key] for key in GEOMETRY_FIELDS}
        template["window_title"] = f"Agent Interface R02 prospective trial {ordinal} source"
        template["followup_window_title"] = f"Agent Interface R02 prospective trial {ordinal} successor"
        templates.append({**template, **dict.fromkeys(ID_FIELDS)})
        synthetic_ids = {key: uuid.uuid5(uuid.NAMESPACE_OID,
            f"r02-offline-preflight-20261126:{ordinal}:{key}").hex for key in ID_FIELDS}
        if used_parent_ids.intersection(synthetic_ids.values()):
            raise RuntimeError("prospective IDs intersect historical R44 IDs")
        trials.append({**template, **synthetic_ids})
    return (
        {**common, "schema": "agent-interface/r02-conditions-template-v1",
         "trial": templates[0], "trials": templates},
        {**common, "schema": "agent-interface/r02-offline-prospective-conditions-v1",
         "identifier_scope": "deterministic offline examples", "trial": trials[0], "trials": trials},
    )


def packet_root(packet):
    if packet.parent.name != "integration" or packet.parent.parent.name != "research":
        raise ValueError("Package output must be <root>/research/integration/<packet>.")
    return packet.parents[2]


def verify_resolvers(inputs, output):
    expected = packet_root(output)
    for name in ("run_cohort_candidate.py", "task_oracle_server.py"):
        path = inputs / name
        tree = ast.parse(path.read_bytes(), filename=str(path))
        binding, = [
            node for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "ROOT" for target in node.targets)
        ]
        scope = {"Path": Path, "__file__": str(output / name)}
        exec(compile(ast.Module(body=[binding], type_ignores=[]), str(path), "exec"), scope)
        if scope["ROOT"] != expected:
            raise RuntimeError(f"published {name} root differs from expected checkout root")


def lock_runner(source):
    text = source.decode("utf-8")
    tree = ast.parse(text, filename="run_cohort_candidate.py")
    entrypoints = {"main", "run_trial"}
    bodies = [
        node.body[0] for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name in entrypoints
    ]
    if len(bodies) != len(entrypoints):
        raise RuntimeError("pinned candidate entrypoints changed")
    lines = text.splitlines(keepends=True)
    for statement in sorted(bodies, key=lambda node: node.lineno, reverse=True):
        lines.insert(statement.lineno - 1,
                     " " * statement.col_offset + f"raise SystemExit({STATIC_REFUSAL!r})\n")
    return "".join(lines).encode("utf-8")


def candidate_parameters(packet, folder, fresh, cfg):
    runner = packet / "run_cohort_candidate.py"
    tree = ast.parse(runner.read_bytes(), filename=str(runner))
    bindings = {"SCORER_PATH", "FIXTURE_PATH", "FG_PATH"}
    assignments = [
        node for node in tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id in bindings for target in node.targets)
    ]
    scope = {"PACKET": packet}
    verify_resolvers(packet, packet)
    exec(compile(ast.Module(body=assignments, type_ignores=[]), str(runner), "exec"), scope)
    expected = {
        "SCORER_PATH": packet / "source/scorer.py",
        "FIXTURE_PATH": packet / "fixture_app_candidate.py",
        "FG_PATH": packet / "source/foreground_probe.py",
    }
    for name, path in expected.items():
        if scope.get(name) != path or not path.is_file():
            raise RuntimeError(f"missing packaged runner dependency {name}")
        ast.parse(path.read_bytes(), filename=str(path))
    cfg_keys = {
        sub.slice.value for sub in ast.walk(tree)
        if isinstance(sub, ast.Subscript) and isinstance(sub.value, ast.Name)
        and sub.value.id == "cfg" and isinstance(sub.slice, ast.Constant)
    }
    if not cfg_keys.issubset(cfg):
        raise RuntimeError(f"missing prospective trial keys {cfg_keys - cfg.keys()}")

    task_params, = [node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and node.name == "task_params"]
    exec(compile(ast.Module(body=[task_params], type_ignores=[]), str(runner), "exec"), {
        "PACKET": packet, "ROOT": packet.parents[2], "folder": folder,
        "targets": folder / "targets.json", "fresh": SimpleNamespace(folder=fresh), "sys": sys,
        "StdioServerParameters": StdioServerParameters,
    }, scope)
    return scope["task_params"]


async def probe_mode(packet, *, optimized):
    with tempfile.TemporaryDirectory(prefix="r02-package-check-") as temporary:
        root = Path(temporary)
        staged = root / "research/integration/r02-prospective"
        shutil.copytree(packet, staged)
        appdata = root / "fake-localappdata"
        switches = ["-B", "-O"] if optimized else ["-B"]
        mode = "optimized" if optimized else "normal"
        exit_result = subprocess.run(
            [sys.executable, *switches, str(staged / "run_cohort_candidate.py")],
            cwd=staged, env={**os.environ, "LOCALAPPDATA": str(appdata), "PYTHONOPTIMIZE": ""},
            capture_output=True, text=True, timeout=10,
        )
        if (exit_result.returncode, exit_result.stdout, exit_result.stderr.strip()) != (1, "", STATIC_REFUSAL):
            raise RuntimeError(f"{mode} static runner did not refuse before its imports")
        callable_probe = r"""
import asyncio
import runpy
import sys

runner = runpy.run_path(sys.argv[1], run_name="offline_programmatic_probe")

class Forbidden:
    def __getattr__(self, name):
        raise AssertionError(f"unexpected fixture, ledger or fence access: {name}")
    def __truediv__(self, component):
        raise AssertionError(f"unexpected fixture, ledger or fence access: {component}")

for name, args in (("main", ()), ("run_trial", (runner["COND"]["trial"],))):
    invoke = runner[name]
    invoke.__globals__.update(RAW=Forbidden(), FENCE=Forbidden(), subprocess=Forbidden())
    try:
        asyncio.run(invoke(*args))
    except SystemExit as exc:
        if str(exc) != sys.argv[2]:
            raise
    else:
        raise RuntimeError(f"{name} did not refuse programmatic execution")
"""
        callable_result = subprocess.run(
            [sys.executable, *switches, "-c", callable_probe,
             str(staged / "run_cohort_candidate.py"), STATIC_REFUSAL],
            cwd=staged, env={**os.environ, "LOCALAPPDATA": str(appdata), "PYTHONOPTIMIZE": ""},
            capture_output=True, text=True, timeout=10,
        )
        if callable_result.returncode != 0:
            raise RuntimeError(f"{mode} programmatic refusal failed: {callable_result.stderr}")

        conditions = json.loads((staged / "conditions.json").read_text(encoding="utf-8"))
        cfg = conditions["trial"]
        folder = staged / "raw" / f'trial-{cfg["ordinal"]:02d}'
        fresh = folder / "fresh-task-target"
        make_task_params = candidate_parameters(staged, folder, fresh, cfg)
        write_json(folder / "targets.json", {"fresh": 1})
        write_json(fresh / "fixture-state.json", {"text": ""})
        write_file(fresh / "events.jsonl", b"")
        results = {}
        for label in ("task-mcp", "followup-recovery-mcp"):
            task = make_task_params(label)
            native_entry = staged / "task_oracle_server.py"
            expected = [str(path) for path in (
                native_entry, folder / "targets.json", folder / label,
                fresh / "fixture-state.json", fresh / "events.jsonl",
            )]
            if list(task.args) != expected or Path(task.cwd) != root:
                raise RuntimeError(f"{mode} {label} paths differ from package layout")
            ast.parse(native_entry.read_bytes(), filename=str(native_entry))
            parameters = StdioServerParameters(
                command=task.command,
                args=[*switches, str(staged / "offline_taskserver.py"), *task.args],
                cwd=task.cwd, env={"LOCALAPPDATA": str(appdata), "PYTHONOPTIMIZE": ""},
            )
            async with stdio_client(parameters) as (reader, writer):
                async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=10)) as client:
                    await client.initialize()
                    tools = await client.list_tools()
            names = sorted(tool.name for tool in tools.tools)
            if names != list(REQUIRED_TOOLS):
                raise RuntimeError(f"{mode} {label} unexpected offline tool registry")
            evidence_path = folder / label / "registration.json"
            if set((folder / label).iterdir()) != {evidence_path}:
                raise RuntimeError(f"{mode} {label} unexpected tool call or output")
            registration = json.loads(evidence_path.read_text(encoding="utf-8"))
            if registration["optimization"] != int(optimized) or registration["backend"] != "inert-fastmcp":
                raise RuntimeError(f"{mode} {label} did not use the requested fake backend")
            results[label] = {
                "entrypoint_arguments": [Path(arg).relative_to(staged).as_posix() for arg in task.args],
                "registered_fake_tools": names, "registration": registration,
            }
        if appdata.exists() or (root / "runtime").exists():
            raise RuntimeError("offline stdio wrote to a runtime or custody directory")
    return {
        "mode": mode, "direct_execution_refused": True,
        "programmatic_execution_refused": True, "paths": results,
    }


def package_hashes(output):
    return {
        path.relative_to(output).as_posix(): sha256(path.read_bytes())
        for path in sorted(output.rglob("*"))
        if path.is_file() and path != output / MANIFEST
    }


def verify_package(output):
    lines = (output / MANIFEST).read_text(encoding="utf-8").splitlines()
    recorded = {}
    for line in lines:
        digest, name = line.split("  ", maxsplit=1)
        if name in recorded:
            raise RuntimeError(f"duplicate package manifest entry {name}")
        recorded[name] = digest
    if recorded != package_hashes(output):
        raise RuntimeError("package manifest does not match all payload bytes")
    return recorded


async def build(output):
    output = output.resolve()
    packet_root(output)
    if output.exists():
        raise FileExistsError(output)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".r02-build-") as temporary:
        staged = Path(temporary) / "package"
        entries = await populate(staged, output)
        staged.rename(output)
    return entries


async def populate(output, published_path):
    inputs = load_pinned_inputs()
    parent = inputs["frozen_parent"]
    template, conditions = prospective_conditions(json.loads(parent["conditions.json"]))
    output.mkdir()
    for name, data in inputs["r02_candidate"].items():
        write_file(output / name, lock_runner(data) if name == "run_cohort_candidate.py" else data)
    for name in COPY_TO_RUNNER_PATH:
        write_file(output / name, parent[name])
    for name, packaged in FROZEN_REFERENCE.items():
        write_file(output / packaged, parent[name])
    write_file(output / "input_pins.json", PIN_FILE.read_bytes())
    write_file(output / "offline_taskserver.py", (HERE / "offline_taskserver.py").read_bytes())
    write_json(output / "conditions.template.json", template)
    write_json(output / "conditions.json", conditions)
    write_json(output / "raw/cohort-progress.json", {
        "schema": "agent-interface/r44-progress-v1", "completed_trials": 0, "trials": [],
    })
    verify_resolvers(output, published_path)
    results = [await probe_mode(output, optimized=optimized) for optimized in (False, True)]
    write_json(output / "preflight.json", {
        "outcome": "PASS_OFFLINE_PACKAGE_PREFLIGHT",
        "scope": "pinned task-server entrypoint with injected inert MCP constructor",
        "published_layout": "<root>/research/integration/<packet>",
        "published_root_resolvers_verified": True,
        "modes": results, "fixture_launches": 0, "tool_calls": 0,
        "host_custody_accesses": 0, "native_runtime_startups": 0,
    })
    manifest = "".join(f"{digest}  {name}\n" for name, digest in sorted(package_hashes(output).items()))
    write_file(output / MANIFEST, manifest.encode("utf-8"))
    return verify_package(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="New package directory at <root>/research/integration/<packet>")
    args = parser.parse_args()
    output = args.output.resolve()
    entries = asyncio.run(build(output))
    print(json.dumps({
        "outcome": "PASS_OFFLINE_PACKAGE_PREFLIGHT", "package": str(output),
        "manifest_entries": len(entries), "manifest_sha256": sha256((output / MANIFEST).read_bytes()),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
