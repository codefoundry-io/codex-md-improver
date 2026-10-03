"""Read-only, explicitly hypothetical instruction loader and scope inventory."""
from dataclasses import asdict, dataclass, field
import ctypes
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tomllib
from typing import TypedDict


@dataclass
class ScopeRequest:
    projects: list[Path]
    codex_home: Path | None = None
    cwd: Path | None = None
    settings: dict = field(default_factory=dict)


@dataclass
class LoaderSettings:
    limit: int | None = None
    fallback_names: list[str] | None = None
    root_markers: list[str] | None = None
    trust: str = "unknown"
    trust_key: str | None = None
    client: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    unresolved: list[str] = field(default_factory=list)


class ChainReport(TypedDict, total=False):
    scenario_id: str
    cwd: str
    scenario_project_root: str
    inventory_root: str
    settings: dict
    sources: list[dict]
    global_source: dict
    project_original_bytes: int | None
    project_included_bytes: int | None
    project_retained_raw_bytes: int | None
    warning: bool | None
    raw_volume_exceeds_budget: bool | None
    loader_outcome: str
    partial: bool


WHITE_SPACE = "\t\n\v\f\r \u0085\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
CONFIG_FIELDS = {"project_doc_max_bytes": "limit", "project_doc_fallback_filenames": "fallback_names",
                 "project_root_markers": "root_markers"}
_POLICY = json.loads((Path(__file__).resolve().parents[1] / "assets/defaults.json").read_text(encoding="utf-8"))
DEFAULTS = _POLICY["loader"]


def canonical(path: Path) -> Path:
    """Match native Unix canonical spelling; Python preserves case aliases on macOS."""
    if sys.platform != "darwin":
        return path.resolve(strict=True)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.realpath.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
    libc.realpath.restype = ctypes.c_void_p
    libc.free.argtypes = [ctypes.c_void_p]
    pointer = libc.realpath(os.fsencode(path), None)
    if not pointer:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(path))
    try:
        return Path(os.fsdecode(ctypes.string_at(pointer)))
    finally:
        libc.free(pointer)


def _home(request):
    env = os.environ.get("CODEX_HOME", "")
    origin = "explicit" if request.codex_home is not None else "environment" if env else "default"
    path = request.codex_home if origin == "explicit" else Path(env) if env else Path.home() / ".codex"
    if origin != "default":
        if not path.is_absolute() or not path.is_dir():
            raise ValueError("Codex home must be an existing absolute directory")
        path = canonical(path)
    return path, origin


def _mapping(value, allowed, label):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError("Invalid " + label + " fields")


def _fields(value):
    _mapping(value, DEFAULTS, "loader settings")
    for key, item in value.items():
        if item is None:
            continue
        if key == "limit":
            if type(item) is not int or item < 0:
                raise ValueError("limit must be a nonnegative integer or null")
        elif not isinstance(item, list) or any(not isinstance(x, str) for x in item):
            raise ValueError(key + " must be an ordered string list or null")


def validate_request(request):
    if not request.projects or any(not p.is_absolute() or ".." in p.parts or not p.is_dir() for p in request.projects):
        raise ValueError("Select existing absolute project directories")
    if request.cwd and (len(request.projects) != 1 or not request.cwd.is_absolute() or ".." in request.cwd.parts
                        or not request.cwd.is_dir() or not request.cwd.is_relative_to(request.projects[0])):
        raise ValueError("--cwd requires one containing project")
    obj = request.settings
    _mapping(obj, {"schema_version", "client", "non_project", "trust", "session_overrides",
                   "environment_groups", "declared_bases"}, "settings")
    if "schema_version" in obj and (type(obj["schema_version"]) is not int or obj["schema_version"] != 1):
        raise ValueError("Unsupported settings version")
    for key in ("non_project", "session_overrides"):
        _fields(obj.get(key, {}))
    trust = obj.get("trust", {})
    if not isinstance(trust, dict) or any(not isinstance(k, str) or not Path(k).is_absolute()
            or v not in ("trusted", "untrusted", "unset", "unknown") for k, v in trust.items()):
        raise ValueError("trust requires absolute lookup keys and valid levels")
    if "client" in obj:
        _mapping(obj["client"], {"name", "version"}, "client")
        if any(not isinstance(v, str) for v in obj["client"].values()):
            raise ValueError("client values must be strings")
    if not isinstance(obj.get("declared_bases", {}), dict):
        raise ValueError("declared_bases must be an object")
    groups = obj.get("environment_groups", [])
    if not isinstance(groups, list):
        raise ValueError("environment_groups must be a list")
    seen_cwds, seen_ids = set(), set()
    for group in groups:
        _mapping(group, {"id", "cwds", "effective_loader_settings"}, "environment group")
        name, cwds = group.get("id"), group.get("cwds")
        if not isinstance(name, str) or not name or name in seen_ids or not isinstance(cwds, list) or not cwds:
            raise ValueError("Groups need unique IDs and ordered cwds")
        seen_ids.add(name)
        for cwd in cwds:
            if (not isinstance(cwd, str) or not Path(cwd).is_absolute() or ".." in Path(cwd).parts or not Path(cwd).is_dir()
                    or not any(Path(cwd).is_relative_to(root) for root in request.projects)
                    or cwd in seen_cwds or request.cwd and Path(cwd) != request.cwd):
                raise ValueError("Group cwd must be uniquely selected")
            seen_cwds.add(cwd)
        effective = group.get("effective_loader_settings", {})
        _mapping(effective, {*DEFAULTS, "trust", "provenance"}, "effective group settings")
        _fields({k: v for k, v in effective.items() if k in DEFAULTS})
        if effective.get("trust", "unknown") not in ("trusted", "untrusted", "unset", "unknown"):
            raise ValueError("Invalid group trust")
        if not isinstance(effective.get("provenance", {}), dict):
            raise ValueError("Invalid group provenance")


def _config(path, content):
    try:
        return tomllib.loads(content.read(path).decode("utf-8")), None
    except FileNotFoundError:
        return {}, None
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        return {}, type(error).__name__


def _ancestors(path):
    return [path, *path.parents]


def _marker_root(cwd, markers):
    for folder in _ancestors(cwd):
        for marker in markers:
            try:
                (folder / marker).stat()
                return folder
            except OSError:
                continue  # Pinned FindUpErrorPolicy::Ignore.
    return cwd


def _metadata_text(path, content):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
        return None
    return content.read(path).decode("utf-8").strip(" \t\r\n\v\f")


def _git_pointer(path, content):
    text = _metadata_text(path, content)
    if text is None or not text.startswith("gitdir:"):
        return None
    target = text[7:].strip(" \t\r\n\v\f")
    return Path(os.path.abspath(path.parent / target)) if target else None


def _git_fallback(cwd, content):
    """(validated key, inaccessible-fact reason); None/None is definite absence."""
    try:
        repo = None
        for folder in _ancestors(cwd):
            entry = folder / ".git"
            try:
                info = entry.stat()
            except FileNotFoundError:
                continue
            if stat.S_ISDIR(info.st_mode):
                try:
                    (entry / "HEAD").stat()
                except FileNotFoundError:
                    continue
            repo = folder
            break
        if repo is None:
            return None, None
        entry = repo / ".git"
        if entry.is_dir():
            return repo, None
        gitdir = _git_pointer(entry, content)
        if gitdir is None or gitdir.is_symlink() or not gitdir.is_dir():
            return None, None
        resolved = canonical(gitdir)
        if resolved.parent.name != "worktrees":
            return None, None
        common = resolved.parent.parent
        backlink = _metadata_text(resolved / "gitdir", content)
        commonlink = _metadata_text(resolved / "commondir", content)
        if not backlink or not commonlink:
            return None, None
        registration = resolved / backlink
        if (registration.name != ".git" or canonical(registration.parent) != canonical(repo)
                or canonical(resolved / commonlink) != common):
            return None, None
        main = gitdir.parent.parent.parent
        main_entry = main / ".git"
        main_storage = main_entry if main_entry.is_dir() else _git_pointer(main_entry, content)
        if main_storage is None or canonical(main_storage) != common:
            return None, None
        return main, None
    except FileNotFoundError:
        return None, None
    except (OSError, UnicodeError) as error:
        return None, type(error).__name__


def _trust(cwd, observed, supplied, base_error, content):
    facts = dict(observed)
    facts.update(supplied)
    try:
        for key in dict.fromkeys([str(canonical(cwd)), str(cwd)]):
            if key in facts:
                return facts[key], key, None
            if base_error:
                # A hidden higher-priority cwd entry can block every fallback.
                return "unknown", None, base_error
        root, problem = _git_fallback(cwd, content)
        if problem:
            return "unknown", None, problem
        if root:
            for key in dict.fromkeys([str(canonical(root)), str(root)]):
                if key in facts:
                    return facts[key], key, base_error
    except OSError as error:
        return "unknown", None, type(error).__name__
    return ("unknown" if base_error else "unset"), None, base_error


def _fallback_names(values, ignored=None):
    if values is None:
        return None
    seen = {"AGENTS.override.md", "AGENTS.md"}
    names = []
    for value in values:
        reason = ("invalid_filename" if not value or value in (".", "..") or "/" in value or "\0" in value
                  else "duplicate" if value in seen else None)
        if reason:
            if ignored is not None:
                ignored.append({"value": value, "reason": reason})
            continue
        seen.add(value)
        names.append(value)
    return names


def resolve_settings(request: ScopeRequest, cwd: Path, *, content=None) -> LoaderSettings:
    home, _ = _home(request)
    content = _protected_content(request, content)
    config, error = _config(home / "config.toml", content)
    values = dict(DEFAULTS) if not error else {key: None for key in DEFAULTS}
    origins = {key: "unresolved_user_config" if error else "pinned_default" for key in DEFAULTS}
    problems = ["user_config:" + error] if error else []
    observed = {}
    project_entries = config.get("projects", {})
    trust_table_error = error
    if isinstance(project_entries, dict):
        for key, value in project_entries.items():
            if isinstance(value, dict):
                level = value.get("trust_level", "unset")
                observed[key] = level if level in ("trusted", "untrusted", "unset") else "unknown"
            else:
                observed[key] = "unknown"
    else:
        trust_table_error = "invalid_projects_table"
    def apply(table, origin, project=False):
        picked = {field: table[key] for key, field in CONFIG_FIELDS.items()
                  if key in table and not (project and field == "root_markers")}
        try:
            _fields(picked)
            values.update(picked)
            origins.update({key: origin for key in picked})
        except ValueError:
            problems.append("invalid_relevant_config")
            for key in picked:
                values[key] = None
                origins[key] = "unresolved:" + origin
    apply(config, "observed_user_config")
    values.update(request.settings.get("non_project", {}))
    origins.update({key: "supplied_non_project" for key in request.settings.get("non_project", {})})
    trust, trust_key, trust_error = _trust(cwd, observed, request.settings.get("trust", {}), trust_table_error, content)
    if trust_error or trust == "unknown":
        problems.append("trust:" + (trust_error or "explicit_unknown"))
    overrides = request.settings.get("session_overrides", {})
    # Project layers cannot set this field, including the ancestry used to read them.
    markers = overrides.get("root_markers", values["root_markers"])
    root = _marker_root(cwd, markers) if markers is not None else cwd
    before_project, before_origins = dict(values), dict(origins)
    if trust in {"trusted", "unknown"}:
        for folder in reversed(_ancestors(cwd)[:_ancestors(cwd).index(root) + 1]):
            path = folder / ".codex/config.toml"
            local, failure = _config(path, content)
            if failure:
                problems.append("project_config:" + failure)
                values["limit"], values["fallback_names"] = None, None
                origins.update({key: "unresolved_project_config:" + str(path) for key in ("limit", "fallback_names")})
            else:
                apply(local, "trusted_project:" + str(path), project=True)
        if trust == "unknown":
            for key in ("limit", "fallback_names"):
                if values[key] != before_project[key]:
                    values[key] = None
                    origins[key] = "unresolved_project_eligibility"
                else:
                    origins[key] = before_origins[key]
    values.update(overrides)
    origins.update({key: "supplied_session_override" for key in overrides})
    ignored = []
    values["fallback_names"] = _fallback_names(values["fallback_names"], ignored)
    for key, value in values.items():
        if value is None:
            problems.append("unknown:" + key)
    return LoaderSettings(**values, trust=trust, trust_key=trust_key, client=dict(request.settings.get("client", {})),
                          provenance={"scenario": "observed_plus_defaults", "unattested_live_layers": ["system", "profile", "cloud", "session"],
                                      "trust_source": "supplied" if trust_key in request.settings.get("trust", {}) else "observed",
                                      "ignored_fallback_names": ignored,
                                      "fields": origins, "client_source": "supplied" if "client" in request.settings else "unattested",
                                      "live_runtime_attested": False}, unresolved=sorted(set(problems)))


class _Content:
    def __init__(self):
        self.cache = {}
        self.denied_identities = set()
        self.denied_paths = set()

    def deny(self, paths):
        for path in paths:
            self.denied_paths.add(path.resolve())
            try:
                self.denied_identities.add(tuple(self.identity(path)))
            except OSError:
                pass

    def identity(self, path):
        info = path.stat()
        return [info.st_dev, info.st_ino]

    def read(self, path):
        before = path.stat()
        identity = (before.st_dev, before.st_ino)
        if identity in self.denied_identities or path.resolve() in self.denied_paths:
            raise PermissionError("known sensitive source excluded")
        if not stat.S_ISREG(before.st_mode):
            raise OSError("nonregular source excluded")
        signature = (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        if identity in self.cache:
            old_signature, data = self.cache[identity]
            if old_signature != signature:
                raise OSError("file changed during scan")
            return data
        data = path.read_bytes()
        after = path.stat()
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (*identity, *signature):
            raise OSError("file changed during read")
        self.cache[identity] = signature, data
        return data


def _protected_content(request, content=None):
    content = content or _Content()
    home, _ = _home(request)
    content.deny([Path.home() / p for p in _POLICY["known_sensitive_paths"]] + [home / "auth.json"])
    return content


def _global(request, content):
    home, origin = _home(request)
    warnings = []
    for name in ("AGENTS.override.md", "AGENTS.md"):
        path = home / name
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                continue
            data = content.read(path)
            decoded = data.decode("utf-8", errors="replace").strip(WHITE_SPACE)
            if decoded:
                return {"path": str(path), "original_bytes": len(data), "included_bytes": len(decoded.encode()),
                        "sha256": hashlib.sha256(data).hexdigest(), "physical_identity": content.identity(path),
                        "state": "selected", "warnings": warnings, "home_origin": origin}
        except FileNotFoundError:
            continue
        except OSError as error:
            warnings.append({"path": str(path), "error": type(error).__name__})
    return {"path": None, "original_bytes": None if warnings else 0, "included_bytes": None if warnings else 0,
            "state": "cache_unknown" if warnings else "absent", "warnings": warnings, "home_origin": origin}


def _selected(cwd, settings):
    if settings.root_markers is None or settings.fallback_names is None:
        return cwd, [], "unknown_discovery_settings"
    root = _marker_root(cwd, settings.root_markers)
    folders = list(reversed(_ancestors(cwd)[:_ancestors(cwd).index(root) + 1]))
    paths = []
    try:
        for folder in folders:
            for name in ["AGENTS.override.md", "AGENTS.md", *settings.fallback_names]:
                path = folder / name
                try:
                    if stat.S_ISREG(path.stat().st_mode):
                        paths.append(path)
                        break
                except FileNotFoundError:
                    continue
    except OSError as error:
        return root, paths, type(error).__name__
    return root, paths, None


_INDEPENDENT_BUDGET = object()


def _volume_flags(original, limit):
    ratio = _POLICY["original_volume_warning"]
    warning = ratio["denominator"] * original >= ratio["numerator"] * limit if original is not None and limit is not None and limit > 0 else None
    excess = original > limit if original is not None and limit is not None else None
    return warning, excess


def _chain(cwd, inventory_root, settings, global_source, content, remaining=_INDEPENDENT_BUDGET):
    budget = settings.limit if remaining is _INDEPENDENT_BUDGET else remaining
    root, paths, discovery_error = _selected(cwd, settings)
    sources, volume = [], 0
    for path in paths:
        record = {"path": str(path), "original_bytes": None, "sha256": None, "read_error": None,
                  "raw_retained_bytes": 0, "included_bytes": 0, "omission": None}
        try:
            record["original_bytes"] = path.stat().st_size
            volume += record["original_bytes"]
            data = content.read(path)
            record["sha256"] = hashlib.sha256(data).hexdigest()
            record["physical_identity"] = content.identity(path)
        except OSError as error:
            record["read_error"] = type(error).__name__
        sources.append(record)
    gate = settings.trust == "untrusted" or settings.limit == 0
    exhausted = not gate and budget == 0
    unresolved = settings.trust == "unknown" or budget is None or discovery_error
    included, charged, outcome = 0, 0, "omitted_by_gate" if gate else "assembled"
    if exhausted:
        outcome = "budget_exhausted"
        for source in sources:
            source["omission"] = "budget_exhausted"
    elif not gate and unresolved:
        included = charged = None
        outcome = "unresolved"
    elif not gate:
        available = budget
        for source in sources:
            if available == 0:
                source["omission"] = "budget_exhausted"
                continue
            if source["read_error"]:
                included = charged = None
                outcome = "environment_read_error"
                break
            try:
                data = content.read(Path(source["path"]))[:available]
            except OSError as error:
                source["read_error"] = type(error).__name__
                included = charged = None
                outcome = "environment_read_error"
                break
            text = data.decode("utf-8", errors="replace")
            if not text.strip(WHITE_SPACE):
                source["omission"] = "empty_or_whitespace"
                continue
            raw, decoded = len(data), len(text.encode())
            source.update(raw_retained_bytes=raw, included_bytes=decoded,
                          omission="clipped" if raw < source["original_bytes"] else None)
            available -= raw
            charged += raw
            included += decoded
    original = None if discovery_error or any(s["original_bytes"] is None for s in sources) else volume
    warning, excess = _volume_flags(original, settings.limit)
    scope_sources = []
    for name in ["AGENTS.override.md", "AGENTS.md", *(settings.fallback_names or [])]:
        path = cwd / name
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                continue
            data = content.read(path)
            scope_sources.append({"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                                  "physical_identity": content.identity(path),
                                  "original_bytes": len(data), "selected": path in paths})
        except FileNotFoundError:
            continue
        except OSError as error:
            scope_sources.append({"path": str(path), "sha256": None, "error": type(error).__name__})
    record = {"scenario_id": hashlib.sha256(json.dumps([str(inventory_root), str(cwd)]).encode()).hexdigest()[:16], "cwd": str(cwd),
              "scenario_project_root": str(root), "inventory_root": str(inventory_root), "settings": asdict(settings),
              "sources": sources, "scope_sources": scope_sources, "global_source": global_source, "project_original_bytes": original,
              "project_included_bytes": included, "project_retained_raw_bytes": charged,
              "warning": warning, "raw_volume_exceeds_budget": excess, "loader_outcome": outcome,
              "modeled_loader_error": None if gate or exhausted or discovery_error == "unknown_discovery_settings" else discovery_error or
                  ("read_error" if outcome == "environment_read_error" else None),
              "delivery": "conditional_on_runtime_permissions", "partial": bool(discovery_error or included is None or
                  global_source["warnings"] or any(s["read_error"] for s in sources) or
                  any(s.get("error") for s in scope_sources)),
              "discovery_error": discovery_error}
    region = {"paths": [s["path"] for s in sources], "settings": record["settings"], "error": discovery_error}
    record["region_id"] = hashlib.sha256(json.dumps(region, sort_keys=True).encode()).hexdigest()[:16]
    return record


def _inventory(request, content, excluded_paths=()):
    roots = [p.resolve() for p in request.projects]
    rows, frontiers = [], []
    storage = set()
    def identify_storage(path):
        marker = path / ".git"
        try:
            if marker.is_dir():
                storage.add(canonical(marker))
            elif marker.is_file():
                target = _git_pointer(marker, content)
                if target is not None and target.is_dir():
                    storage.add(canonical(target))
        except (OSError, UnicodeError) as error:
            frontiers.append({"path": str(marker), "kind": "blocked", "error": type(error).__name__})

    def walk(path, owner, ancestors):
        try:
            identity = (path.stat().st_dev, path.stat().st_ino)
            if any(path.resolve().is_relative_to(p.resolve()) for p in excluded_paths):
                frontiers.append({"path": str(path), "kind": "owned_output"})
                return
            if identity in ancestors:
                frontiers.append({"path": str(path), "kind": "cycle"})
                return
            if path.is_symlink() and not any(path.resolve().is_relative_to(root) for root in roots):
                frontiers.append({"path": str(path), "kind": "outside_scope"})
                return
            rows.append((path, owner))
            identify_storage(path)
            for entry in sorted(path.iterdir()):
                try:
                    if entry.name == ".git":
                        frontiers.append({"path": str(entry), "kind": "git_administration"})
                    elif entry.is_dir():
                        walk(entry, owner, ancestors | {identity})
                except OSError as error:
                    frontiers.append({"path": str(entry), "kind": "blocked", "error": type(error).__name__})
        except OSError as error:
            frontiers.append({"path": str(path), "kind": "blocked", "error": type(error).__name__})
    if request.cwd:
        for folder in _ancestors(request.cwd):
            identify_storage(folder)
        rows.append((request.cwd, request.projects[0]))
    else:
        for root in request.projects:
            walk(root, root, set())
    # A pointer can identify an earlier sibling. Filter provisional metadata-only
    # rows before any instruction content is read or cwd scenario is constructed.
    def in_storage(path):
        try:
            physical = canonical(path)
        except OSError:
            physical = path.resolve()
        return any(physical.is_relative_to(root) for root in storage)
    rows = [(path, owner) for path, owner in rows if not in_storage(path)]
    frontiers = [f for f in frontiers if f["kind"] == "git_administration" or not in_storage(Path(f["path"]))]
    frontiers.extend({"path": str(path), "kind": "git_administration"} for path in sorted(storage)
                     if not any(f["path"] == str(path) for f in frontiers))
    return list(dict.fromkeys(rows)), frontiers


def discover_chains(request: ScopeRequest) -> list[ChainReport]:
    return scan(request)["chains"]


def scan(request: ScopeRequest, *, content=None, excluded_paths=()) -> dict:
    validate_request(request)
    content = _protected_content(request, content)
    global_source = _global(request, content)
    inventory, frontiers = _inventory(request, content, excluded_paths)
    chains = [_chain(cwd, root, resolve_settings(request, cwd, content=content), global_source, content) for cwd, root in inventory]
    groups = []
    for group in request.settings.get("environment_groups", []):
        raw = group.get("effective_loader_settings", {})
        ignored = []
        effective = LoaderSettings(limit=raw.get("limit"), fallback_names=_fallback_names(raw.get("fallback_names"), ignored),
            root_markers=raw.get("root_markers"), trust=raw.get("trust", "unknown"),
            client=dict(request.settings.get("client", {})),
            provenance={**raw.get("provenance", {}), "scenario": "supplied_group_effective", "ignored_fallback_names": ignored,
                        "client_source": "supplied" if "client" in request.settings else "unattested", "live_runtime_attested": False})
        remaining = effective.limit
        members = []
        for name in group["cwds"]:
            cwd = Path(name)
            owner = next(root for root in request.projects if cwd.is_relative_to(root))
            member = _chain(cwd, owner, effective, global_source, content, remaining)
            member["environment_group_id"] = group["id"]
            member["scenario_id"] = "group:" + group["id"] + ":" + member["scenario_id"]
            members.append(member)
            size = member["project_included_bytes"]
            if size is None:
                remaining = None
            elif remaining is not None:
                remaining = max(0, remaining - size)
        known = all(m["project_included_bytes"] is not None for m in members)
        error = any(m["modeled_loader_error"] for m in members)
        original = sum(m["project_original_bytes"] for m in members) if all(m["project_original_bytes"] is not None for m in members) else None
        warning, excess = _volume_flags(original, effective.limit)
        groups.append({"id": group["id"], "members": members,
            "project_original_bytes": original, "limit": effective.limit,
            "warning": warning, "raw_volume_exceeds_budget": excess,
            "project_included_bytes": sum(m["project_included_bytes"] for m in members) if known else None,
            "global_candidate_bytes": global_source["included_bytes"], "delivered_bytes": None,
            "delivery": "conditional_on_runtime_permissions",
            "possible_outcomes": ["omitted_environment", "propagated_failure"] if error else
                ["assembled"] if known else ["unresolved"]})
    partial = any(row["partial"] for row in chains) or any(f["kind"] in ("blocked", "outside_scope") for f in frontiers)
    partial |= any(member["partial"] for group in groups for member in group["members"])
    findings = any(row["warning"] or row["raw_volume_exceeds_budget"] for row in
                   [*chains, *groups, *(member for group in groups for member in group["members"])])
    scenarios = [*chains, *(member for group in groups for member in group["members"])]
    usable = global_source["state"] == "selected" or any(source["sha256"] for row in scenarios
                 for source in [*row["sources"], *row["scope_sources"]])
    home, origin = _home(request)
    return {"schema_version": 1, "chains": chains, "groups": groups, "frontiers": frontiers,
            "partial": bool(partial), "exit_code": 2 if not usable else 3 if partial else 1 if findings else 0,
            "scope": {"projects": [str(p) for p in request.projects], "cwd": str(request.cwd) if request.cwd else None,
                      "codex_home": str(home), "codex_home_origin": origin, "settings": request.settings},
            "inventory_complete": not any(f["kind"] in ("blocked", "outside_scope") for f in frontiers),
            "semantic_review_complete": False, "assessment": "unassessed"}
