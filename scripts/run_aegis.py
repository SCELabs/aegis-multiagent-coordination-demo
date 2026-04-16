from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from demo.runner import save_results, summarize
from demo.aegis_run import run_aegis


def main():
    results = run_aegis()
    summary = summarize(results)
    path = save_results("aegis.json", results)

    print("=" * 60)
    print("AEGIS")
    print("=" * 60)
    for k, v in summary.items():
        print(f"{k}: {v}")

    print("\nCASE NOTES")
    print("=" * 60)
    for item in results:
        print(item["case_id"])
        for note in getattr(item["state"], "event_log", [])[:0]:
            pass
        notes = getattr(item["metrics"], "notes", None)
        if notes:
            for note in notes:
                print(" -", note)

    print(f"\nSaved: {path}")


if __name__ == "__main__":
    main()
