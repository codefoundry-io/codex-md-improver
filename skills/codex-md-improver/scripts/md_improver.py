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
        with os.fdopen(descriptor, "w", encoding="utf-8", errors="backslashreplace") as stream:
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
        out.mkdir(exist_ok=False)
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
        (out / (name + ".md")).write_text(rendered, encoding="utf-8", errors="backslashreplace")
        manifest.update(complete=not result.get("partial", False) and result["exit_code"] != 2, phase="finished")
        _write_json(out / "manifest.json", manifest)
        return result["exit_code"]
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        if created:
            manifest.update(complete=False, phase="error", error=str(error))
            _write_json(out / "manifest.json", manifest)
        print(("Audit input/output error: " + str(error)).encode("utf-8", errors="backslashreplace").decode("utf-8"), file=sys.stderr)
        return 2


def _candidate_records(graph, scenarios, content, selected):
    from discovery import canonical, audit_source_boundary
    from lint_candidates import find_candidates
    from references import document_kind, refresh_directory_summaries
    loaded = {source["path"] for c in scenarios for source in [*c.get("sources", []), *c.get("scope_sources", [])]}
    loaded |= {c["global_source"]["path"] for c in scenarios if c.get("global_source", {}).get("path")}
    result = []
    for node in graph["nodes"].values():
        for alias in node["aliases"]:
            path = Path(alias)
            kind = document_kind(path, alias in loaded)
            try:
                boundary = audit_source_boundary(canonical(path), graph.get("_git_storage", []))
                if boundary:
                    graph["partial"], graph["text_read_complete"] = True, False
                    graph["boundaries"].append({"path": alias, "kind": boundary, "phase": "candidates"})
                    for state in graph["states"].values():
                        if state["path"] == alias:
                            state.update(kind=boundary, children=[], identity=None, bytes=None)
                    continue
                data = content.read(path)
                if hashlib.sha256(data).hexdigest() != node["sha256"]:
                    raise OSError("file changed during scan")
                text = data.decode("utf-8")
            except (OSError, UnicodeError) as error:
                failure = "changed_during_read" if "changed during" in str(error) else "blocked_frontier"
                graph["partial"], graph["text_read_complete"] = True, False
                graph["boundaries"].append({"path": alias, "kind": failure, "phase": "candidates"})
                for state in graph["states"].values():
                    if state["path"] == alias:
                        state.update(kind=failure, children=[])
                continue
            for candidate in find_candidates(text, path, kind, selected):
                candidate["source_sha256"] = node["sha256"]
                result.append(candidate)
    refresh_directory_summaries(graph)
    reachable, seen = set(), set()
    pending = [key for roots in graph["roots"].values() for key in roots]
    while pending:
        key = pending.pop()
        if key in seen:
            continue
        seen.add(key)
        state = graph["states"][key]
        if state["kind"] in {"leaf", "cycle"}:
            reachable.add(state["path"])
        pending.extend(edge["state"] for edge in state["children"] if "state" in edge)
    return [candidate for candidate in result if candidate["path"] in reachable]


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
    interrupted = False
    def interrupt_once(signum, frame):
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            _interrupt(signum, frame)
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
        if not isinstance(resolutions, list):
            raise ValueError("Resolutions must be a list")
        home, _ = _home(request)
        out.mkdir(exist_ok=False)
        created = True
        manifest.update(allow_output_in_target=args.allow_output_in_target, phase="inventory")
        _write_json(out / "manifest.json", manifest)
        for sig in (signal.SIGINT, signal.SIGTERM):
            handlers[sig] = signal.signal(sig, interrupt_once)
        content = _Content()
        result = scan(request, content=content, excluded_paths=[out])
        manifest["phase"] = "references"
        _write_json(out / "manifest.json", manifest)
        scenarios = [*result["chains"], *(member for group in result["groups"] for member in group["members"])]
        graph = build_reference_graph(scenarios, settings.get("declared_bases", {}), resolutions,
            context={"codex_home": home, "output": out, "allow_output_in_target": args.allow_output_in_target,
                     "content": content, "git_storage": [f["path"] for f in result["frontiers"]
                                                        if f["kind"] == "git_administration"]})
        result["candidates"] = _candidate_records(graph, scenarios, content, set(_POLICY["detector_ids"]))
        result["graph"] = {k: v for k, v in graph.items() if not k.startswith("_")}
        result["reading_summary"] = summarize_reading_paths(graph)
        result["text_read_complete"] = graph["text_read_complete"]
        result["partial"] |= graph["partial"]
        if result["exit_code"] == 0 and result["candidates"]:
            result["exit_code"] = 1
        manifest["phase"] = "routes"
        _write_json(out / "manifest.json", manifest)
        capped = False
        with (out / "routes.jsonl").open("x", encoding="utf-8", errors="backslashreplace") as stream:
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
        route_label = "Route stream" if capped else "Complete route stream"
        (out / "audit.md").write_text(render_audit(result) + "\n" + route_label + ": routes.jsonl\n", encoding="utf-8", errors="backslashreplace")
        _write_json(out / "manifest.json", manifest)
        return result["exit_code"]
    except (KeyboardInterrupt, ScanInterrupted) as error:
        interrupted = True
        result.update(partial=True, exit_code=3, interruption=type(error).__name__)
        if created:
            _write_json(out / "audit.json", result)
            manifest.update(complete=False, phase="interrupted")
            _write_json(out / "manifest.json", manifest)
        return 3
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        if created:
            result.update(partial=True, exit_code=2, error=str(error))
            _write_json(out / "audit.json", result)
            manifest.update(complete=False, phase="error", error=str(error))
            _write_json(out / "manifest.json", manifest)
        print(("Audit input/output error: " + str(error)).encode("utf-8", errors="backslashreplace").decode("utf-8"), file=sys.stderr)
        return 2
    finally:
        for sig, old in handlers.items():
            signal.signal(sig, old)


if __name__ == "__main__":
    sys.exit(main())
