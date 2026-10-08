import json
import argparse
from pathlib import Path

from candidate import summarize

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(HERE / "fixture.json"))
    parser.add_argument("--output", default=str(HERE / "candidate_result.json"))
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = summarize(fixture["episodes"], fixture["horizons_from_launch"])
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_launched_n": result["all_launched_n"],
                      "first_terminal_counts": result["first_terminal_counts"],
                      "first_terminal_success_fraction": result["first_terminal_success_fraction"],
                      "horizons": result["horizons"]}, sort_keys=True))


if __name__ == "__main__":
    main()
