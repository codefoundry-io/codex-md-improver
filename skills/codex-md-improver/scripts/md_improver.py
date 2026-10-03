"""Portable command entrypoint. Audit targets are always read-only."""
import argparse
import json
from pathlib import Path
import sys


def main(argv=None):
    if sys.version_info < (3, 11):
        print("Python 3.11 or newer is required.", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description="Read-only instruction audit; exit 0 is not prompt-quality certification.")
    parser.add_argument("command", choices=["scan"])
    parser.add_argument("--project", action="append", required=True)
    parser.add_argument("--cwd")
    parser.add_argument("--codex-home")
    parser.add_argument("--settings")
    parser.add_argument("--out", required=True)
    parser.add_argument("--allow-output-in-target", action="store_true")
    args = parser.parse_args(argv)
    from discovery import ScopeRequest, scan
    try:
        projects = [Path(p) for p in args.project]
        out = Path(args.out)
        if not out.is_absolute() or out.exists() or out.is_symlink():
            raise ValueError("Output must be a new absolute directory")
        inside = any(out.resolve().is_relative_to(p.resolve()) for p in projects)
        if inside and not args.allow_output_in_target:
            raise ValueError("Output inside an input requires --allow-output-in-target")
        settings = json.loads(Path(args.settings).read_text()) if args.settings else {}
        request = ScopeRequest(projects, Path(args.codex_home) if args.codex_home else None,
                               Path(args.cwd) if args.cwd else None, settings)
        # Task 1 performs bounded loader inventory; the graph task adds streamed lifecycle.
        result = scan(request)
        out.mkdir(parents=True, exist_ok=False)
        (out / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / "manifest.json").write_text(json.dumps({"complete": True, "owned": ["audit.json", "manifest.json"],
                                                     "allow_output_in_target": args.allow_output_in_target}) + "\n")
        return result["exit_code"]
    except (OSError, ValueError, TypeError) as error:
        print("Audit input/output error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
