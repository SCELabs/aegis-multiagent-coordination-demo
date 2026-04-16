from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from demo.runner import save_results, summarize
from demo.baseline import run_baseline


def main():
    results = run_baseline()
    summary = summarize(results)
    path = save_results("baseline.json", results)

    print("=" * 60)
    print("BASELINE")
    print("=" * 60)
    for k, v in summary.items():
        print(f"{k}: {v}")
    print(f"\nSaved: {path}")


if __name__ == "__main__":
    main()