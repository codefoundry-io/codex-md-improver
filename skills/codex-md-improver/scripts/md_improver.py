"""Portable command entrypoint. Audit targets are always read-only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys


class ScanInterrupted(BaseException):
    pass


def _interrupt(signum, frame):
    raise ScanInterrupted("signal " + str(signum))


def _write_json(path, value):
    # The previous valid receipt survives interruption before atomic replacement.
    temporary = path.with_name("." + path.name + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _assessment_command(args):
    from reporting import enrich_audit, compare_reports, render_audit, _report_shape
    out = None
    created = False
    manifest = {"complete": False, "phase": "starting", "owned": ["manifest.json"]}
    try:
        def read(path):
            if not path:
                raise ValueError("Missing report input argument")
            data = Path(path).read_bytes()
            value = json.loads(data)
            if not isinstance(value, dict):
                raise ValueError("Report inputs must be objects")
            return value, hashlib.sha256(data).hexdigest()
        if args.command == "report":
            audit, digest = read(args.audit)
            assessment, _ = read(args.assessment)
            inputs = [audit]
        else:
            before, digest = read(args.before)
            after, _ = read(args.after)
            inputs = [before, after]
        for value in inputs:
            _report_shape(value)
        out = Path(args.out)
        if not out.is_absolute() or out.exists() or out.is_symlink():
            raise ValueError("Output must be a new absolute directory")
        roots = [Path(p) for value in inputs for p in value.get("scope", {}).get("projects", [])]
        roots += [Path(s["path"]) for value in inputs for s in value.get("graph", {}).get("states", {}).values()
                  if s.get("kind") in {"directory", "empty_directory"}]
        if any(out.resolve().is_relative_to(p.resolve()) for p in roots) and not args.allow_output_in_target:
            raise ValueError("Output inside an input requires --allow-output-in-target")
        out.mkdir(parents=True, exist_ok=False)
        created = True
        _write_json(out / "manifest.json", manifest)
        if args.command == "report":
            result = enrich_audit(audit, assessment, input_sha256=digest)
            name, rendered = "audit", render_audit(result)
        else:
            result = compare_reports(before, after, before_sha256=digest)
            name = "delta"
            rendered = "# Audit comparison\n\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        manifest.update(owned=["manifest.json", name + ".json", name + ".md"],
                        temporary_paths=[".manifest.json.tmp", "." + name + ".json.tmp"],
                        allow_output_in_target=args.allow_output_in_target)
        _write_json(out / (name + ".json"), result)
        (out / (name + ".md")).write_text(rendered, encoding="utf-8")
        manifest.update(complete=not result.get("partial", False) and result["exit_code"] != 2, phase="finished")
        _write_json(out / "manifest.json", manifest)
        return result["exit_code"]
    except (OSError, ValueError, TypeError, KeyError) as error:
        if created:
            manifest.update(complete=False, phase="error", error=str(error))
            _write_json(out / "manifest.json", manifest)
        print("Audit input/output error: " + str(error), file=sys.stderr)
        return 2


def _candidate_records(graph, scenarios, content, selected):
    from lint_candidates import find_candidates
    loaded = {source["path"] for c in scenarios for source in [*c.get("sources", []), *c.get("scope_sources", [])]}
    loaded |= {c["global_source"]["path"] for c in scenarios if c.get("global_source", {}).get("path")}
    result = []
    for node in graph["nodes"].values():
        for alias in node["aliases"]:
            path = Path(alias)
            kind = "agents_guidance" if alias in loaded else "markdown_reference" if path.suffix.lower() == ".md" else "linked_instruction" if path.suffix.lower() in {"", ".txt", ".rst"} else "code_config"
            text = content.read(path).decode("utf-8")
            for candidate in find_candidates(text, path, kind, selected):
                candidate["source_sha256"] = node["sha256"]
                result.append(candidate)
    return result


def main(argv=None):
    if sys.version_info < (3, 11):
        print("Python 3.11 or newer is required.", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description="Read-only instruction audit; exit 0 is not prompt-quality certification.")
    parser.add_argument("command", choices=["scan", "report", "compare"])
    parser.add_argument("--project", action="append")
    parser.add_argument("--audit")
    parser.add_argument("--assessment")
    parser.add_argument("--before")
    parser.add_argument("--after")
    parser.add_argument("--cwd")
    parser.add_argument("--codex-home")
    parser.add_argument("--settings")
    parser.add_argument("--resolutions")
    parser.add_argument("--max-routes", type=int)
    parser.add_argument("--out", required=True)
    parser.add_argument("--allow-output-in-target", action="store_true")
    args = parser.parse_args(argv)
    if args.command != "scan":
        return _assessment_command(args)
    from discovery import ScopeRequest, scan, validate_request, _home, _Content, _POLICY
    from references import build_reference_graph, iter_terminal_paths, summarize_reading_paths
    from reporting import render_audit
    out = None
    created = False
    manifest = {"complete": False, "owned": ["audit.json", "audit.md", "routes.jsonl", "manifest.json"],
                "temporary_paths": [".audit.json.tmp", ".manifest.json.tmp"],
                "route_count": 0, "phase": "starting"}
    result = {"schema_version": 1, "chains": [], "partial": True, "exit_code": 3,
              "inventory_complete": False, "text_read_complete": False, "semantic_review_complete": False,
              "assessment": "unassessed"}
    handlers = {}
    try:
        if not args.project:
            raise ValueError("scan requires --project")
        projects = [Path(p) for p in args.project]
        out = Path(args.out)
        if not out.is_absolute() or out.exists() or out.is_symlink():
            raise ValueError("Output must be a new absolute directory")
        inside = any(out.resolve().is_relative_to(p.resolve()) for p in projects)
        if inside and not args.allow_output_in_target:
            raise ValueError("Output inside an input requires --allow-output-in-target")
        if args.max_routes is not None and args.max_routes <= 0:
            raise ValueError("--max-routes must be positive")
        settings = json.loads(Path(args.settings).read_text()) if args.settings else {}
        request = ScopeRequest(projects, Path(args.codex_home) if args.codex_home else None,
                               Path(args.cwd) if args.cwd else None, settings)
        validate_request(request)
        resolutions = json.loads(Path(args.resolutions).read_text()) if args.resolutions else []
        home, _ = _home(request)
        out.mkdir(parents=True, exist_ok=False)
        created = True
        manifest.update(allow_output_in_target=args.allow_output_in_target, phase="inventory")
        _write_json(out / "manifest.json", manifest)
        for sig in (signal.SIGINT, signal.SIGTERM):
            handlers[sig] = signal.signal(sig, _interrupt)
        content = _Content()
        content.deny([Path.home() / p for p in _POLICY["known_sensitive_paths"]] + [home / "auth.json"])
        result = scan(request, content=content, excluded_paths=[out])
        manifest["phase"] = "references"
        _write_json(out / "manifest.json", manifest)
        scenarios = [*result["chains"], *(member for group in result["groups"] for member in group["members"])]
        graph = build_reference_graph(scenarios, settings.get("declared_bases", {}), resolutions,
            context={"codex_home": home, "output": out, "allow_output_in_target": args.allow_output_in_target,
                     "content": content, "git_storage": [f["path"] for f in result["frontiers"]
                                                        if f["kind"] == "git_administration"]})
        result["graph"] = {k: v for k, v in graph.items() if not k.startswith("_")}
        result["reading_summary"] = summarize_reading_paths(graph)
        result["text_read_complete"] = graph["text_read_complete"]
        result["partial"] |= graph["partial"]
        result["candidates"] = _candidate_records(graph, scenarios, content, set(_POLICY["detector_ids"]))
        if result["exit_code"] == 0 and result["candidates"]:
            result["exit_code"] = 1
        manifest["phase"] = "routes"
        _write_json(out / "manifest.json", manifest)
        capped = False
        with (out / "routes.jsonl").open("x", encoding="utf-8") as stream:
            for chain in scenarios:
                for row in iter_terminal_paths(graph, chain):
                    if args.max_routes is not None and manifest["route_count"] >= args.max_routes:
                        capped = True
                        break
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    stream.flush()
                    manifest["route_count"] += 1
                    _write_json(out / "manifest.json", manifest)
                if capped:
                    break
        result["partial"] |= capped
        result["route_limit_reached"] = capped
        if result["exit_code"] != 2 and result["partial"]:
            result["exit_code"] = 3
        manifest.update(phase="finished", complete=not result["partial"] and result["exit_code"] != 2)
        _write_json(out / "audit.json", result)
        (out / "audit.md").write_text(render_audit(result) + "\nComplete route stream: routes.jsonl\n", encoding="utf-8")
        _write_json(out / "manifest.json", manifest)
        return result["exit_code"]
    except (KeyboardInterrupt, ScanInterrupted) as error:
        result.update(partial=True, exit_code=3, interruption=type(error).__name__)
        if created:
            _write_json(out / "audit.json", result)
            manifest.update(complete=False, phase="interrupted")
            _write_json(out / "manifest.json", manifest)
        return 3
    except (OSError, ValueError, TypeError) as error:
        if created:
            result.update(partial=True, exit_code=2, error=str(error))
            _write_json(out / "audit.json", result)
            manifest.update(complete=False, phase="error", error=str(error))
            _write_json(out / "manifest.json", manifest)
        print("Audit input/output error: " + str(error), file=sys.stderr)
        return 2
    finally:
        for sig, old in handlers.items():
            signal.signal(sig, old)


if __name__ == "__main__":
    sys.exit(main())
