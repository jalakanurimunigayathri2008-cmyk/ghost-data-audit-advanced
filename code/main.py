from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from code.app.pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Evidence-grounded deletion audit agent")
    parser.add_argument("--dataset", default="dataset")
    parser.add_argument("--output", default="output.csv")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = run_pipeline(Path(args.dataset), Path(args.output), args.strict, args.dry_run)
    print(f"Requests: {result['request_count']}; planned output rows: {result['output_count']}")
    for warning in result["warnings"][:30]:
        print("WARNING:", warning)
    if len(result["warnings"]) > 30:
        print(f"... plus {len(result['warnings']) - 30} more warnings")
    if not args.dry_run:
        print("Output:", Path(args.output).resolve())
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
