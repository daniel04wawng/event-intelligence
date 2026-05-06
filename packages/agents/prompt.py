"""One-shot: paste a prompt, get the curated, ranked list.

Reads an event brief from stdin OR a single positional arg, runs the full
pipeline (objective → audience → sourcing → scoring → room balance), and
prints the ranked prospects + a one-line summary.

Usage:
    # argv (one-liner)
    python -m packages.agents.prompt "Plan a 100-person crypto hackathon in SF"

    # stdin (multi-line)
    python -m packages.agents.prompt <<'EOF'
    100-person crypto hackathon next week in SF.
    Builders, founders, ZK researchers, smart contract engineers.
    EOF

    # pipe
    cat my_brief.md | python -m packages.agents.prompt

    # interactive (you type, then Ctrl-D)
    python -m packages.agents.prompt

Flags:
    --top N      print top N rows in the table (default 25)
    --json       emit JSON to stdout instead of a table
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


# ---------- env loading ----------

def _load_dotenv() -> None:
    """Auto-load .env from repo root so ANTHROPIC_API_KEY / DATABASE_URL just work."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


# ---------- main ----------

def _read_brief(args_text: str | None) -> str:
    if args_text:
        return args_text.strip()
    if sys.stdin.isatty():
        print("Paste your event brief — finish with Ctrl-D (Unix) or Ctrl-Z then Enter (Windows):",
              file=sys.stderr)
    return sys.stdin.read().strip()


def _print_table(rows: list[dict], top_n: int) -> None:
    if not rows:
        print("(no prospects sourced — check that ANTHROPIC_API_KEY is set; "
              "without it the curator can't go online)", file=sys.stderr)
        return
    cols = [("#", 3), ("fit", 4), ("priority", 14), ("persona", 28), ("name", 26), ("role", 36)]
    header = "".join(f"{name:<{w}}" for name, w in cols)
    print(header)
    print("-" * sum(w for _, w in cols))
    for i, r in enumerate(rows[:top_n], 1):
        line = (
            f"{i:<3}"
            f"{(str(r.get('fit_score') or '-'))[:3]:<4}"
            f"{(r.get('priority') or '-')[:12]:<14}"
            f"{(r.get('persona') or '-')[:26]:<28}"
            f"{(r.get('name') or '-')[:24]:<26}"
            f"{(r.get('role') or '-')[:34]:<36}"
        )
        print(line)
    if len(rows) > top_n:
        print(f"... ({len(rows) - top_n} more in data/ranked_people.csv)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="packages.agents.prompt", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("brief", nargs="?", default=None,
                        help="Inline brief text. If omitted, reads from stdin.")
    parser.add_argument("--top", type=int, default=25, help="Rows to print (default 25).")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="Emit JSON instead of a table.")
    parser.add_argument("--seed", default=None,
                        help="Optional seed CSV path (skips LLM curation when present).")
    args = parser.parse_args(argv)

    _load_dotenv()

    brief = _read_brief(args.brief)
    if not brief:
        print("error: empty brief", file=sys.stderr)
        return 2

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "warning: ANTHROPIC_API_KEY not set — curator will skip and you'll get 0 prospects. "
            "Add it to .env or `export ANTHROPIC_API_KEY=...` then retry.",
            file=sys.stderr,
        )

    print(f"running pipeline on {len(brief)}-char brief…", file=sys.stderr)

    from packages.agents.run_intelligence import run_pipeline

    code, summary = run_pipeline(
        brief,
        seed_csv_path=args.seed,
        brief_source_label="stdin" if args.brief is None else "argv",
        quiet=True,
    )
    if code != 0:
        print(f"pipeline failed: {summary.get('error', 'unknown')}", file=sys.stderr)
        return code

    # Read the ranked CSV that the pipeline just wrote
    ranked_path = Path(summary.get("ranked_people_csv_path", "data/ranked_people.csv"))
    rows: list[dict] = []
    if ranked_path.exists():
        import csv
        with ranked_path.open() as f:
            rows = list(csv.DictReader(f))

    if args.as_json:
        print(json.dumps({
            "summary": summary,
            "people": rows,
        }, indent=2))
        return 0

    # human table
    print()
    print(f"Sourced {summary.get('ranked_count', 0)} prospects | "
          f"{summary.get('high_priority_count', 0)} high-priority | "
          f"top gap: {summary.get('top_gap_persona', 'n/a')}")
    print(f"Files: {ranked_path}")
    print()
    _print_table(rows, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
