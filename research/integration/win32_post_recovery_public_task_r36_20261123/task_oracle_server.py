from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from runtime.cli_v1.mcp_server import create_server

def main(argv=None):
    import hashlib, json, time
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 4:
        raise SystemExit("expected targets, output directory, state path, and events path")
    targets_path, output, state_path, events_path = map(Path, argv)
    def oracle(action):
        op=action.get("operation_id"); gen=action.get("target_generation"); cid=action.get("call_id")
        execution=((action.get("result") or {}).get("execution") or {})
        start=execution.get("started_ns"); end=execution.get("ended_ns")
        rows=[]
        if events_path.exists():
            for line in events_path.read_text(encoding="utf-8").splitlines():
                try: rows.append(json.loads(line))
                except json.JSONDecodeError: pass
        matching=[r for r in rows if r.get("kind")=="char" and r.get("code")==98 and type(r.get("monotonic_ns")) is int and type(start) is int and type(end) is int and start <= r["monotonic_ns"] <= end]
        state=json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        success=(isinstance(cid,str) and isinstance(op,str) and isinstance(gen,str) and len(matching)==1 and state.get("text")=="b")
        observed=matching[0]["monotonic_ns"] if matching else time.monotonic_ns()
        digest=hashlib.sha256(events_path.read_bytes()).hexdigest() if events_path.exists() else "0"*64
        return {"call_id":cid,"operation_id":op,"target_generation":gen,"oracle_id":"r36b0000000000000000000000000001","outcome":"success" if success else "failure","observed_monotonic_ns":observed,"evidence_ref":"fixture-oracle:r36:events-sha256:"+digest}
    create_server(json.loads(targets_path.read_text(encoding="utf-8")), output,
        session_mode="supervised-win32",
        supervised_win32_late_input_horizon_ns=2_000_000_000,
        supervised_win32_task_oracle=oracle).run(transport="stdio")

if __name__ == "__main__":
    main()
