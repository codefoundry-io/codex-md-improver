"""Read-only graph of scenario-bound reference occurrences and physical text."""
import glob
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import unquote
from discovery import _Content, _POLICY


class InvalidOutputLocation(ValueError):
    pass


LIMITED = {"blocked_frontier", "missing_target", "unresolved", "excluded_sensitive",
           "excluded_git", "binary", "undecodable", "special_file", "changed_during_read"}
NON_READ = {"informational", "example", "output"}
CONFIG_NAMES = {".env", ".npmrc", ".pgpass", ".netrc", ".pypirc", ".gitignore",
                ".gitattributes", ".dockerignore", ".editorconfig", ".yarnrc"}


def document_kind(path, guidance=False):
    if guidance:
        return "agents_guidance"
    if path.name in CONFIG_NAMES:
        return "code_config"
    if path.suffix.lower() in {".md", ".markdown"}:
        return "markdown_reference"
    return "linked_instruction" if path.suffix.lower() in {"", ".txt", ".rst"} else "code_config"


def _identity(info):
    return f"{info.st_dev}:{info.st_ino}"


def _classification(line):
    # Link labels/targets and quoted path names are data, not prose directives.
    for start, end, _, _ in reversed(list(_inline_destinations(line))):
        line = line[:start] + " " + line[end:]
    line = re.sub(r"\[[^\]]*\]\[[^\]]*\]", "", line)
    line = re.sub(chr(96) + r"[^" + chr(96) + r"]*" + chr(96), "", line)
    line = re.sub(r"https?://\S+", "", line)
    example = re.search(r"\b(?:example|sample)\b|\be\.g\.(?=\W|$)", line, re.I)
    output = re.search(r"\b(write|output|save|generate|create)\b", line, re.I)
    reading = re.search(r"\b(read|consult|follow|see)\b|읽|참조", line, re.I)
    if reading and (example or output):
        return "mixed"
    if example:
        return "example"
    if output:
        return "output"
    if reading:
        return "read_dependency"
    return "uncertain"


def _inline_destinations(text):
    """Keep balanced destinations and complete optional titles in one span."""
    consumed_until = 0
    for match in re.finditer(r"\[[^\]]*\]\(", text):
        if match.start() < consumed_until:
            continue
        cursor = match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        start = cursor
        if cursor < len(text) and text[cursor] == "<":
            start += 1
            end = text.find(">", start)
            if end < 0 or "\n" in text[start:end]:
                continue
            cursor = end + 1
        else:
            depth = 0
            while cursor < len(text):
                char = text[cursor]
                if char == "\\" and cursor + 1 < len(text):
                    cursor += 2
                    continue
                if char.isspace() or (char == ")" and depth == 0):
                    break
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                cursor += 1
            if depth:
                continue
            end = cursor
        if start == end:
            continue
        after_destination = cursor
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor < len(text) and text[cursor] != ")":
            if cursor == after_destination or text[cursor] not in "\"'(":
                continue
            opener = text[cursor]
            closer = ")" if opener == "(" else opener
            cursor += 1
            depth = 1
            while cursor < len(text) and depth:
                char = text[cursor]
                if char == "\\" and cursor + 1 < len(text):
                    cursor += 2
                    continue
                if char == closer:
                    depth -= 1
                elif opener == "(" and char == "(":
                    depth += 1
                cursor += 1
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
        if cursor < len(text) and text[cursor] == ")":
            consumed_until = cursor + 1
            yield match.start(), cursor + 1, start, end


def _bare_url_target(value):
    value = value.rstrip(".,;!?")
    pairs = {")": "(", "]": "[", "}": "{"}
    while value and value[-1] in pairs and value.count(value[-1]) > value.count(pairs[value[-1]]):
        value = value[:-1].rstrip(".,;!?")
    return value


def _lex(text, path, kind=None):
    """Heuristic candidates only; unmatched prose still needs semantic review."""
    if (kind or document_kind(path)) == "code_config":
        return []
    occurrences, occupied, definitions, fences = [], [], {}, []
    opening, marker_text, offset = None, None, 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            if opening is None and not (marker[1][0] == chr(96) and chr(96) in marker[2]):
                opening, marker_text = offset, marker[1]
            elif (opening is not None and marker[1][0] == marker_text[0]
                  and len(marker[1]) >= len(marker_text) and not marker[2].strip()):
                fences.append((opening, offset + len(line)))
                opening, marker_text = None, None
        offset += len(line)
    if opening is not None:
        fences.append((opening, len(text)))
    for match in re.finditer(r"(?m)^[ \t]*\[([^\]]+)\]:[ \t]*(?:\r?\n[ \t]*)?(\S[^\n]*)", text):
        if any(match.start() < b and match.end() > a for a, b in fences):
            continue
        wrapped = "[definition](" + match[2].strip() + ")"
        destination = next(_inline_destinations(wrapped), None)
        if destination is None or destination[:2] != (0, len(wrapped)):
            continue
        definitions[match[1].casefold()] = wrapped[destination[2]:destination[3]]
        occupied.append(match.span())

    def add(start, end, target, kind, classification=None):
        if any(start < b and end > a for a, b in [*occupied, *fences]):
            return
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        line = text[line_start:line_end if line_end >= 0 else len(text)].strip()
        contextual = _classification(line)
        inferred = "uncertain" if contextual in {*NON_READ, "mixed"} else classification or contextual
        if inferred == "uncertain" and line.startswith("|"):
            column = text[line_start:start].count("|")
            for previous in reversed(text[:line_start].splitlines()):
                if not previous.strip().startswith("|"):
                    break
                cells = previous.split("|")
                if column < len(cells) and re.fullmatch(r"(?:read|files? to read|읽기)", cells[column].strip(), re.I):
                    inferred = "read_dependency"
                    break
        occurrences.append({"span": [start, end], "text": text[start:end], "target_text": target,
                            "classification": inferred,
                            "syntax": kind, "condition": line})
        occupied.append((start, end))

    for opening, closing, start, end in _inline_destinations(text):
        add(start, end, text[start:end], "markdown", "read_dependency")
        occupied.append((opening, closing))
    for match in re.finditer(r"\[([^\]]+)\]\[([^\]]*)\]", text):
        key = (match[2] or match[1]).casefold()
        if key in definitions:
            add(match.start(), match.end(), definitions[key], "markdown", "read_dependency")
    for match in re.finditer(r"(?<!!)\[([^\]^]+)\](?![\[(])", text):
        key = match[1].casefold()
        if key in definitions:
            add(match.start(), match.end(), definitions[key], "markdown", "read_dependency")
    tick = chr(96)
    for match in re.finditer(r"<([A-Za-z][A-Za-z0-9+.-]*:[^<>\s]+)>|"
                             r"([A-Za-z][A-Za-z0-9+.-]*://[^<>\s`]+)", text):
        group = 1 if match[1] is not None else 2
        target = match[group] if group == 1 else _bare_url_target(match[group])
        add(match.start(group), match.start(group) + len(target), target, "url", "read_dependency")
        occupied.append(match.span())
    for match in re.finditer(tick + r"([^" + tick + r"\n]+)" + tick, text):
        target = match[1]
        if "/" in target or re.search(r"\.[A-Za-z0-9]{1,10}(?::\d+)?(?:#.*)?$", target):
            add(match.start(1), match.end(1), target, "plain")
    pattern = r"(?<![\w])(?:~?/|\.{1,2}/)?[\w$.*{}-]+(?:/[\w.*{}$-]+)*(?:\.[\w]+(?::\d+)?(?:#[\w-]+)?|/)"
    for match in re.finditer(pattern, text):
        if re.fullmatch(r"\d+(?:\.\d+)+|e\.g|i\.e", match[0], re.I):
            continue
        add(match.start(), match.end(), match[0], "plain")
    return sorted(occurrences, key=lambda row: row["span"])


def _base_path(base, source, chain):
    if not isinstance(base, dict) or set(base) - {"kind", "path"}:
        raise ValueError("Invalid reference base")
    mapping = {"document_dir": source.parent, "scenario_project_root": Path(chain["scenario_project_root"]),
               "scenario_cwd": Path(chain["cwd"])}
    kind = base.get("kind")
    if kind in mapping and "path" not in base:
        return mapping[kind]
    if kind == "absolute" and isinstance(base.get("path"), str) and Path(base["path"]).is_absolute():
        return Path(base["path"])
    raise ValueError("Unsupported reference base or nonabsolute path")


def _expand_glob(path):
    """Finite component expansion that retains failures hidden by glob.glob."""
    parts = path.parts
    current, frontiers = [Path(parts[0])], []
    for index, part in enumerate(parts[1:], 1):
        following = []
        for parent in current:
            if not glob.has_magic(part):
                child = parent / part
                try:
                    child.lstat()
                    following.append(child)
                except FileNotFoundError:
                    pass
                except OSError:
                    frontiers.append({"path": str(child), "kind": "blocked_frontier"})
                continue
            try:
                with os.scandir(parent) as entries:
                    for entry in entries:
                        if entry.name.startswith(".") and not part.startswith("."):
                            continue
                        if not fnmatch.fnmatchcase(entry.name, part):
                            continue
                        try:
                            if index == len(parts) - 1 or entry.is_dir():
                                following.append(parent / entry.name)
                        except OSError:
                            frontiers.append({"path": str(parent / entry.name), "kind": "blocked_frontier"})
            except (FileNotFoundError, NotADirectoryError):
                pass
            except OSError:
                frontiers.append({"path": str(parent), "kind": "blocked_frontier"})
        current = sorted(set(following))
    return current, list({(row["path"], row["kind"]): row for row in frontiers}.values())


def _nonlocal_status(target):
    if target.startswith("#"):
        return "self_reference"
    filename_line = re.fullmatch(r"[^:/]+\.[^:/]+:\d+(?::\d+)?(?:#.*)?", target)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*:\S*", target) and not filename_line:
        return "url"
    return None


def _absolute_reference(path):
    """Anchor a reference without collapsing filesystem-significant parents."""
    path = Path(path)
    return path if path.is_absolute() else Path.cwd() / path


def _targets(occurrence, source, chain, declared, context):
    target = occurrence["target_text"]
    nonlocal_status = _nonlocal_status(target)
    if nonlocal_status:
        return nonlocal_status, [], [], []
    target = unquote(target.partition("#")[0])
    target = re.sub(r":\d+(?::\d+)?$", "", target)
    has_glob = glob.has_magic(target)
    substitutions = {"HOME": str(context.get("user_home", Path.home())),
                     "CODEX_HOME": str(context.get("codex_home", Path.home() / ".codex")),
                     "PROJECT_ROOT": chain["scenario_project_root"], "CWD": chain["cwd"]}
    unknown = []
    def expand(match):
        name = match[1] or match[2]
        if name not in substitutions:
            unknown.append(name)
        return substitutions.get(name, match[0])
    variable = r"\$\{(\w+)\}|\$(\w+)"
    glob_target = re.sub(variable, lambda match: glob.escape(expand(match)), target)
    target = re.sub(variable, expand, target)
    if unknown or not target or "\0" in target:
        return "unresolved", [], [], []
    if target == "~" or target.startswith("~/"):
        home = str(context.get("user_home", Path.home()))
        glob_target = str(Path(glob.escape(home)) / glob_target[2:])
        target = str(Path(home) / target[2:])
    base = occurrence.get("base") or declared.get(str(source)) or declared.get(source)
    if Path(target).is_absolute():
        alternatives = [Path(target)]
        pattern = glob_target
    else:
        bases = ([_base_path(base, source, chain)] if base else [source.parent]
                 if occurrence["syntax"] == "markdown" else
                 [source.parent, Path(chain["scenario_project_root"]), Path(chain["cwd"])])
        alternatives = [folder / target for folder in bases]
        pattern = str(Path(glob.escape(str(bases[0]))) / glob_target)
    alternatives = list(dict.fromkeys(_absolute_reference(p) for p in alternatives))
    if len(alternatives) != 1:
        return "unresolved", [], [str(p) for p in alternatives], []
    resolved = alternatives[0]
    if has_glob:
        matches, frontiers = _expand_glob(_absolute_reference(pattern))
        return ("resolved", matches, [], frontiers) if matches or frontiers else ("unresolved", [], [str(resolved)], [])
    return "resolved", [resolved], [], []


def _validate_resolutions(resolutions):
    if not isinstance(resolutions, list):
        raise ValueError("Resolutions must be a list")
    seen = set()
    allowed = {"source", "source_sha256", "span", "text", "classification", "base", "target", "scenario_id"}
    for row in resolutions:
        if not isinstance(row, dict) or set(row) - allowed:
            raise ValueError("Invalid resolution fields")
        span = row.get("span")
        if (not isinstance(row.get("source"), str) or not Path(row["source"]).is_absolute()
                or not isinstance(row.get("source_sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", row["source_sha256"])
                or not isinstance(span, list) or len(span) != 2 or any(type(n) is not int for n in span)
                or not 0 <= span[0] < span[1] or not isinstance(row.get("text"), str)
                or row.get("classification") not in {*NON_READ, "read_dependency", "uncertain"}):
            raise ValueError("Resolution needs valid source/hash/span/text/classification")
        if row["classification"] in NON_READ and ("target" in row or "base" in row):
            raise ValueError("Non-read decisions cannot supply a target or base")
        if "target" in row and not isinstance(row["target"], str):
            raise ValueError("Resolution target must be a string")
        key = (row["source"], tuple(span), row.get("scenario_id"))
        if key in seen:
            raise ValueError("Duplicate resolution")
        seen.add(key)


def build_reference_graph(chains, declared_bases=None, resolutions=None, *, context=None):
    declared, context = declared_bases or {}, context or {}
    resolutions = [] if resolutions is None else resolutions
    _validate_resolutions(resolutions)
    if not isinstance(declared, dict):
        raise ValueError("Declared bases must be an object")
    graph = {"nodes": {}, "occurrences": [], "states": {}, "roots": {}, "partial": False,
             "directory_totals": {}, "boundaries": [], "text_read_complete": True,
             "semantic_review_complete": False, "_chains": chains}
    content = context.get("content") or _Content()
    texts, consumed, directories = {}, set(), set()
    home = Path(context.get("user_home", Path.home()))
    codex_home = Path(context.get("codex_home", home / ".codex"))
    sensitive = [home / p for p in _POLICY["known_sensitive_paths"]] + [codex_home / "auth.json"]
    sensitive_ids = set()
    for path in sensitive:
        try:
            sensitive_ids.add(_identity(path.stat()))
        except OSError:
            pass
    sensitive_paths = {p.resolve() for p in sensitive}
    owned = Path(context["output"]).resolve() if context.get("output") else None
    git_storage = [Path(p).resolve() for p in context.get("git_storage", [])]

    def state_key(chain, path):
        return chain["scenario_id"] + "|" + str(path)

    def check_output(path, info, direct):
        if owned is None:
            return False
        real = path.resolve()
        is_owned = real.is_relative_to(owned)
        if not is_owned:
            try:
                is_owned = any(_identity(p.stat()) == _identity(info) for p in [owned, *owned.iterdir()])
            except OSError:
                pass
        if is_owned:
            if direct:
                raise InvalidOutputLocation("Direct input aliases this run's output: " + str(path))
            graph["boundaries"].append({"path": str(path), "kind": "owned_output"})
            return True
        if stat.S_ISDIR(info.st_mode) and owned.is_relative_to(real) and not context.get("allow_output_in_target"):
            raise InvalidOutputLocation("Linked input directory contains this run's output: " + str(path))
        return False

    def terminal(chain, path, kind, info=None, identity=None):
        key = state_key(chain, path)
        graph["states"][key] = {"path": str(path), "kind": kind, "identity": identity,
                               "bytes": info.st_size if info and stat.S_ISREG(info.st_mode) else None, "children": []}
        if kind in LIMITED:
            graph["partial"], graph["text_read_complete"] = True, False
        return key

    def visit(path, chain, ancestors, direct=True):
        path = _absolute_reference(path)
        key = state_key(chain, path)
        try:
            info = path.stat()
        except FileNotFoundError:
            return terminal(chain, path, "missing_target")
        except OSError:
            return terminal(chain, path, "blocked_frontier")
        if stat.S_ISDIR(info.st_mode):
            directories.add(key)
        if check_output(path, info, direct):
            return None
        identity, real = _identity(info), path.resolve()
        if identity in sensitive_ids or real in sensitive_paths:
            return terminal(chain, path, "excluded_sensitive", info, identity)
        if ".git" in path.parts or ".git" in real.parts or any(real.is_relative_to(p) for p in git_storage):
            if not direct:
                graph["boundaries"].append({"path": str(path), "kind": "git_administration"})
                return None
            return terminal(chain, path, "excluded_git", info, identity)
        if path.name == "SKILL.md" or real.name == "SKILL.md":
            return terminal(chain, path, "excluded_skill", info, identity)
        if identity in ancestors:
            if key not in graph["states"]:
                terminal(chain, path, "cycle", info, identity)
            return key
        if key in graph["states"] and graph["states"][key]["kind"] != "cycle":
            # A cached node's descendants may have first been reached under a
            # different ancestor set. Revisit those edges in this route context;
            # physical content and occurrence records remain shared.
            existing = graph["states"][key]
            for edge in list(existing["children"]):
                if "state" in edge:
                    child = graph["states"][edge["state"]]
                    visit(Path(child["path"]), chain, ancestors | {identity},
                          direct=existing["kind"] != "directory")
            return key
        if stat.S_ISDIR(info.st_mode):
            try:
                if (path / "SKILL.md").is_file():
                    return terminal(chain, path, "excluded_skill", info, identity)
                entries = sorted(path.iterdir())
            except OSError:
                return terminal(chain, path, "blocked_frontier")
            terminal(chain, path, "directory", info, identity)
            for entry in entries:
                if entry.name == ".git":
                    graph["boundaries"].append({"path": str(entry), "kind": "git_administration"})
                    continue
                child = visit(entry, chain, ancestors | {identity}, direct=False)
                if child:
                    graph["states"][key]["children"].append({"state": child, "condition": "directory read"})
            if not graph["states"][key]["children"]:
                graph["states"][key]["kind"] = "empty_directory"
            return key
        if not stat.S_ISREG(info.st_mode):
            return terminal(chain, path, "special_file", info, identity)
        if identity not in graph["nodes"]:
            try:
                data = content.read(path)
            except OSError as error:
                kind = "changed_during_read" if "changed during" in str(error) else "blocked_frontier"
                return terminal(chain, path, kind, info, identity)
            if b"\0" in data:
                return terminal(chain, path, "binary", info, identity)
            try:
                text = data.decode("utf-8")
            except UnicodeError:
                return terminal(chain, path, "undecodable", info, identity)
            graph["nodes"][identity] = {"identity": identity, "aliases": [], "bytes": len(data),
                                       "sha256": hashlib.sha256(data).hexdigest(), "content_status": "read"}
            texts[identity] = text
        node = graph["nodes"][identity]
        if str(path) not in node["aliases"]:
            node["aliases"].append(str(path))
        text = texts[identity]
        terminal(chain, path, "leaf", info, identity)
        guidance = {s["path"] for s in [chain.get("global_source", {}), *chain["sources"], *chain.get("scope_sources", [])] if s.get("path")}
        candidates = _lex(text, path, document_kind(path, str(path) in guidance))
        for index, resolution in enumerate(resolutions):
            if resolution["source"] != str(path) or resolution.get("scenario_id", chain["scenario_id"]) != chain["scenario_id"]:
                continue
            a, b = resolution["span"]
            if resolution["source_sha256"] != node["sha256"] or text[a:b] != resolution["text"] or b > len(text):
                raise ValueError("Stale resolution source/hash/span: " + str(path))
            consumed.add(index)
            candidate = next((c for c in candidates if c["span"] == resolution["span"]), None)
            if candidate is None:
                candidate = {"span": resolution["span"], "text": resolution["text"], "syntax": "semantic",
                             "target_text": resolution.get("target", resolution["text"]), "condition": "supplied semantic resolution"}
                candidates.append(candidate)
            candidate["classification"] = resolution["classification"]
            if "target" in resolution:
                candidate["target_text"] = resolution["target"]
            if "base" in resolution:
                candidate["base"] = resolution["base"]
        for candidate in sorted(candidates, key=lambda c: c["span"]):
            occurrence = {**candidate, "source": str(path), "source_sha256": node["sha256"],
                          "scenario_id": chain["scenario_id"], "cwd": chain["cwd"],
                          "scenario_project_root": chain["scenario_project_root"]}
            occurrence["id"] = hashlib.sha256(json.dumps([str(path), candidate["span"], chain["scenario_id"]]).encode()).hexdigest()[:20]
            classification = candidate["classification"]
            nonlocal_status = _nonlocal_status(candidate["target_text"])
            if nonlocal_status:
                status, targets, alternatives, frontiers = nonlocal_status, [], [], []
            elif classification in NON_READ:
                status, targets, alternatives, frontiers = "non_read", [], [], []
            elif classification == "uncertain":
                status, targets, alternatives, frontiers = "unresolved", [], [], []
            else:
                status, targets, alternatives, frontiers = _targets(candidate, path, chain, declared, context)
            occurrence.update(status=status, targets=[str(p) for p in targets], alternatives=alternatives)
            if frontiers:
                occurrence["expansion_frontiers"] = frontiers
            graph["occurrences"].append(occurrence)
            if status == "unresolved":
                graph["partial"], graph["text_read_complete"] = True, False
                graph["states"][key]["children"].append({"kind": "unresolved", "condition": candidate["condition"],
                                                        "occurrence_id": occurrence["id"]})
            for frontier in frontiers:
                child = terminal(chain, Path(frontier["path"]), frontier["kind"])
                graph["states"][key]["children"].append({"state": child, "condition": candidate["condition"],
                                                        "occurrence_id": occurrence["id"]})
            for target in targets:
                child = visit(target, chain, ancestors | {identity})
                if child:
                    graph["states"][key]["children"].append({"state": child, "condition": candidate["condition"],
                                                            "occurrence_id": occurrence["id"]})
        return key

    for chain in chains:
        sources = [s["path"] for s in [chain.get("global_source", {}), *chain["sources"], *chain.get("scope_sources", [])] if s.get("path")]
        graph["roots"][chain["scenario_id"]] = []
        for source in dict.fromkeys(sources):
            key = visit(Path(source), chain, set())
            if key:
                graph["roots"][chain["scenario_id"]].append(key)
    if consumed != set(range(len(resolutions))):
        raise ValueError("A resolution did not match an accessible selected source/scenario")

    def record(rows, value):
        rows[json.dumps(value, sort_keys=True)] = value

    def condition(source, edge, scenario):
        target = graph["states"].get(edge.get("state"), {})
        return {"scenario_id": scenario, "source": source["path"],
                "occurrence_id": edge.get("occurrence_id"), "condition": edge["condition"],
                "target_path": target.get("path")}

    incoming = {}
    for key, state in graph["states"].items():
        scenario = key[:-(len(state["path"]) + 1)]
        for edge in state["children"]:
            if "state" in edge:
                record(incoming.setdefault(edge["state"], {}), condition(state, edge, scenario))

    def descendants(key, scenario):
        ids, conditions, frontiers, seen, pending = set(), dict(incoming.get(key, {})), {}, set(), [key]
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            row = graph["states"][current]
            if row["identity"] in graph["nodes"]:
                ids.add(row["identity"])
            if row["kind"] in LIMITED or row["kind"] == "excluded_skill":
                record(frontiers, {"scenario_id": scenario, "path": row["path"], "kind": row["kind"]})
            for edge in row["children"]:
                evidence = condition(row, edge, scenario)
                record(conditions, evidence)
                if "state" in edge:
                    pending.append(edge["state"])
                else:
                    record(frontiers, {**evidence, "kind": edge["kind"]})
        return ids, conditions, frontiers

    def summary(ids, conditions, frontiers):
        counts = {}
        for row in frontiers.values():
            counts[row["kind"]] = counts.get(row["kind"], 0) + 1
        return {"unique_text_bytes": sum(graph["nodes"][i]["bytes"] for i in ids),
                "physical_text_files": len(ids), "read_conditions": list(conditions.values()),
                "frontiers": list(frontiers.values()), "frontier_counts": counts,
                "lower_bound": bool(frontiers)}

    combined = {}
    graph["directory_totals_by_scenario"], graph["directory_summaries_by_scenario"] = {}, {}
    for key, state in graph["states"].items():
        if key in directories:
            scenario = key[:-(len(state["path"]) + 1)]
            ids, conditions, frontiers = descendants(key, scenario)
            row = summary(ids, conditions, frontiers)
            graph["directory_summaries_by_scenario"].setdefault(scenario, {})[state["path"]] = row
            graph["directory_totals_by_scenario"].setdefault(scenario, {})[state["path"]] = row["unique_text_bytes"]
            all_ids, all_conditions, all_frontiers = combined.setdefault(state["path"], (set(), {}, {}))
            all_ids.update(ids)
            all_conditions.update(conditions)
            all_frontiers.update(frontiers)
    graph["directory_summaries"] = {path: summary(*values) for path, values in combined.items()}
    graph["directory_totals"] = {path: row["unique_text_bytes"] for path, row in graph["directory_summaries"].items()}
    return graph


def iter_terminal_paths(graph, chain):
    """Expand routes lazily, with route-local cycle and unique-byte accounting."""
    loaded = [s["path"] for s in [chain.get("global_source", {}), *chain["sources"]] if s.get("path")]
    initial_ids = set()
    prefix_incomplete = False
    for source in loaded:
        row = graph["states"].get(chain["scenario_id"] + "|" + source)
        if row and row["identity"] in graph["nodes"]:
            initial_ids.add(row["identity"])
        else:
            prefix_incomplete = True
    initial_total = sum(graph["nodes"][i]["bytes"] for i in initial_ids)

    def result(node, route, conditions, total, kind, origin):
        return {"scenario_id": chain["scenario_id"], "cwd": chain["cwd"],
                "environment_group_id": chain.get("environment_group_id"),
                "scenario_project_root": chain["scenario_project_root"], "loader_sources": loaded,
                "originating_instruction_file": origin, "route": route, "conditions": conditions,
                "terminal_path": node["path"], "terminal_kind": kind, "terminal_bytes": node["bytes"],
                "route_original_bytes": total,
                "lower_bound": prefix_incomplete or kind in LIMITED or kind == "excluded_skill",
                "content_status": "read" if node["identity"] in graph["nodes"] else "metadata_only",
                "global_original_bytes": chain.get("global_source", {}).get("original_bytes"),
                "project_original_bytes": chain["project_original_bytes"],
                "project_included_bytes": chain["project_included_bytes"], "reference_original_bytes": total - initial_total}

    def walk(key, route, conditions, ancestors, counted, total, origin):
        node = graph["states"][key]
        identity = node["identity"]
        current = [*route, node["path"]]
        if identity in graph["nodes"] and identity not in counted:
            total += graph["nodes"][identity]["bytes"]
            counted = counted | {identity}
        cycle = identity is not None and identity in ancestors
        children = [] if cycle else node["children"]
        if not children:
            yield result(node, current, conditions, total, "cycle" if cycle else node["kind"], origin)
        for edge in children:
            if "state" not in edge:
                unknown = {"path": None, "bytes": None, "identity": None}
                yield result(unknown, current, [*conditions, edge["condition"]], total, "unresolved", origin)
            else:
                yield from walk(edge["state"], current, [*conditions, edge["condition"]],
                                ancestors | {identity}, counted, total, origin)
    for root in graph["roots"].get(chain["scenario_id"], []):
        yield from walk(root, [], [], set(), initial_ids, initial_total, graph["states"][root]["path"])


def summarize_reading_paths(graph):
    return {"unique_text_bytes": sum(n["bytes"] for n in graph["nodes"].values()),
            "physical_text_files": len(graph["nodes"]), "occurrences": len(graph["occurrences"]),
            "text_read_complete": graph["text_read_complete"], "partial": graph["partial"],
            "semantic_review_complete": False, "directory_totals": graph["directory_totals"],
            "directory_totals_by_scenario": graph["directory_totals_by_scenario"],
            "directory_summaries": graph["directory_summaries"],
            "directory_summaries_by_scenario": graph["directory_summaries_by_scenario"]}
