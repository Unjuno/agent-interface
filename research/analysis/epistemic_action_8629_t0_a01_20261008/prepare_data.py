def build_dataset(seeds):
    if __package__:
        from .generator import generate_cases
    else:
        from generator import generate_cases

    fixture_cases = []
    oracle_cases = {}
    for seed in seeds:
        for generated in generate_cases(seed):
            case_id = generated["case_id"]
            fixture_cases.append(
                {
                    "case_id": case_id,
                    "input": generated["input"],
                    "prescription": generated["truth"]["epistemic_action"],
                }
            )
            oracle_cases[case_id] = generated["truth"]
    if len(oracle_cases) != len(fixture_cases):
        raise ValueError("duplicate case id across held-out seeds")
    return (
        {"schema": "epistemic-action-8629-fixture-v1", "seeds": list(seeds), "cases": fixture_cases},
        {"schema": "epistemic-action-8629-oracle-v1", "cases": oracle_cases},
    )


def main():
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--oracle", required=True)
    args = parser.parse_args()
    fixture, oracle = build_dataset((17, 29, 41, 53))
    Path(args.fixture).write_text(json.dumps(fixture, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    Path(args.oracle).write_text(json.dumps(oracle, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
