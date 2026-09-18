from __future__ import annotations

from decimal import Decimal, localcontext


def _d(text):
    return Decimal(str(text))


def compute(snapshot):
    with localcontext() as ctx:
        ctx.prec = 60
        boundary = _d(snapshot["t1_max_useful_effect_latency_ms"]) + _d(snapshot["receipt_drain"]["max_ms"])
        metrics = []
        for row in snapshot["rows"]:
            gap = _d(row["stdin_closed_to_exit_ms"])
            metrics.append({
                "tag": row["tag"],
                "git_blob": row["git_blob"],
                "gap_ms": row["stdin_closed_to_exit_ms"],
                "gap_to_boundary_ratio": f"{gap / boundary:.12f}",
                "effective_window_ms": f"{gap - boundary:.6f}",
                "overhead_fraction": f"{boundary / gap:.15f}",
            })
        ratios = [_d(row["stdin_closed_to_exit_ms"]) / boundary for row in snapshot["rows"]]
        overheads = [boundary / _d(row["stdin_closed_to_exit_ms"]) for row in snapshot["rows"]]
        effective = [_d(row["stdin_closed_to_exit_ms"]) - boundary for row in snapshot["rows"]]
        return {
            "boundary_allowance_ms": f"{boundary:.6f}",
            "n": len(metrics),
            "metrics": metrics,
            "min_gap_to_boundary_ratio": f"{min(ratios):.12f}",
            "max_overhead_fraction": f"{max(overheads):.15f}",
            "min_effective_window_ms": f"{min(effective):.6f}",
        }
