"""Source-bound judgments and deterministic summaries; no semantic oracle."""
import hashlib
import json
import copy
from collections import Counter
from pathlib import Path
import re
from typing import TypedDict


class AuditReport(TypedDict, total=False):
    schema_version: int
    scope: dict
    assessment: dict | str
    partial: bool
    exit_code: int


WEIGHTS = {"commands_workflows": 20, "structure": 20, "non_obvious_patterns": 15,
           "concision": 15, "freshness": 15, "actionability": 15}


def _object(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ValueError("Invalid record fields: expected " + ", ".join(required))
    return value


def _string(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty text")
    return value


def _list(value):
    if not isinstance(value, list):
        raise ValueError("Expected a list")
    return value


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError("Expected SHA-256")
    return value


def _records(rows):
    seen = set()
    for row in _list(rows):
        if not isinstance(row, dict) or _string(row.get("id")) in seen:
            raise ValueError("Duplicate or invalid record ID")
        seen.add(row["id"])
    return rows


def _criteria():
    data = json.loads((Path(__file__).resolve().parents[1] / "assets/criteria.json").read_text())
    return {row["id"] for row in data["criteria"]}


def _report_shape(report):
    """Validate persisted structures consumed by comparison/output routing."""
    if not isinstance(report, dict) or type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        raise ValueError("Unsupported report schema")
    scope = report.get("scope")
    if not isinstance(scope, dict) or not {"projects", "cwd", "codex_home", "settings"} <= scope.keys():
        raise ValueError("Invalid report scope")
    paths = _list(scope["projects"])
    if not paths or any(not isinstance(p, str) or not Path(p).is_absolute() for p in paths):
        raise ValueError("Invalid requested project paths")
    if (not isinstance(scope["settings"], dict) or not isinstance(scope["codex_home"], str)
            or not Path(scope["codex_home"]).is_absolute()
            or scope["cwd"] is not None and (not isinstance(scope["cwd"], str) or not Path(scope["cwd"]).is_absolute())):
        raise ValueError("Invalid requested settings/home/cwd")
    graph = report.get("graph", {})
    if (not isinstance(graph, dict) or not isinstance(graph.get("nodes", {}), dict)
            or not isinstance(graph.get("states", {}), dict)
            or any(not isinstance(s, dict) for s in graph.get("states", {}).values())):
        raise ValueError("Invalid persisted graph")
    aliases = {}
    for node in graph.get("nodes", {}).values():
        if not isinstance(node, dict): raise ValueError("Invalid persisted node")
        for alias in _list(node.get("aliases")):
            if not isinstance(alias, str) or not Path(alias).is_absolute():
                raise ValueError("Invalid persisted alias")
            if node.get("content_status") == "read":
                digest = _hash(node.get("sha256"))
                if alias in aliases and aliases[alias] != digest:
                    raise ValueError("Conflicting persisted alias hashes")
                aliases[alias] = digest
    scenarios = []
    for name in ("chains", "groups", "candidates"):
        rows = _list(report.get(name, []))
        if any(not isinstance(row, dict) for row in rows):
            raise ValueError("Invalid persisted " + name)
        if name == "chains": scenarios.extend(rows)
        if name == "groups":
            for group in rows:
                members = _list(group.get("members", []))
                if any(not isinstance(m, dict) for m in members): raise ValueError("Invalid group members")
                scenarios.extend(members)
    summary = report.get("reading_summary", {})
    if not isinstance(summary, dict): raise ValueError("Invalid reading summary")
    for name in ("unique_text_bytes", "occurrences"):
        value = summary.get(name)
        if value is not None and (type(value) is not int or value < 0): raise ValueError("Invalid reading metric")
    for scenario in scenarios:
        for name in ("warning", "raw_volume_exceeds_budget"):
            if scenario.get(name) is not None and type(scenario[name]) is not bool:
                raise ValueError("Invalid loader warning")
    if "partial" in report and type(report["partial"]) is not bool: raise ValueError("Invalid coverage state")
    if "exit_code" in report and (type(report["exit_code"]) is not int or report["exit_code"] not in {0, 1, 2, 3}):
        raise ValueError("Invalid report exit code")
    allowed = _criteria()
    verdicts = report.get("criterion_verdicts", {})
    if not isinstance(verdicts, dict) or any(id not in allowed or value not in {"PASS", "FAIL", "NA"} for id, value in verdicts.items()):
        raise ValueError("Unknown or malformed persisted verdict")
    def snapshot_evidence(rows):
        if not _list(rows): raise ValueError("Missing persisted evidence")
        for row in rows:
            _object(row, ("source", "source_sha256", "span", "text"), ("scenario_id", "provenance"))
            if not Path(_string(row["source"])).is_absolute(): raise ValueError("Invalid evidence path")
            if _hash(row["source_sha256"]) != aliases.get(row["source"]):
                raise ValueError("Persisted evidence does not match readable snapshot alias/hash")
            if "scenario_id" in row:
                state = graph.get("states", {}).get(row["scenario_id"] + "|" + row["source"], {})
                if state.get("kind") not in {"leaf", "cycle"} or state.get("identity") not in graph.get("nodes", {}):
                    raise ValueError("Persisted evidence scenario does not reach its source")
            span = row["span"]
            if (not isinstance(span, list) or len(span) != 2 or any(type(n) is not int for n in span)
                    or not 0 <= span[0] < span[1] or not isinstance(row["text"], str)):
                raise ValueError("Invalid persisted evidence span")
    for row in _records(report.get("findings", [])):
        _object(row, ("id", "rule_id", "anchor", "evidence", "explanation", "confidence", "status"), ("disposition",))
        if row["rule_id"] not in allowed or row["status"] not in {"open", "owner_deferred", "rejected"}:
            raise ValueError("Invalid persisted finding")
        _string(row["anchor"]); snapshot_evidence(row["evidence"])
    targets = set()
    for row in _list(report.get("resolves", [])):
        _object(row, ("before_report_sha256", "before_finding_id", "evidence", "reason", "baseline_validation"))
        key = (_hash(row["before_report_sha256"]), _string(row["before_finding_id"]))
        if key in targets or row["baseline_validation"] != "pending": raise ValueError("Invalid persisted resolution")
        targets.add(key); snapshot_evidence(row["evidence"]); _string(row["reason"])
    if any(not isinstance(p, str) or not Path(p).is_absolute() for p in _list(report.get("reviewed_sources", []))):
        raise ValueError("Invalid reviewed-source list")


def report_hash(report):
    """Canonical JSON hash for in-memory API calls; CLI binds actual input bytes."""
    return hashlib.sha256(json.dumps(report, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def enrich_audit(audit, assessment, *, input_sha256=None):
    if not isinstance(audit, dict) or type(audit.get("schema_version")) is not int or audit["schema_version"] != 1:
        raise ValueError("Unsupported audit schema")
    _object(assessment, ("schema_version", "audit_sha256"),
            ("findings", "dimensions", "dispositions", "resolves", "owner_decisions", "proposals",
             "reviewed_sources", "semantic_review_complete", "criterion_verdicts"))
    if type(assessment["schema_version"]) is not int or assessment["schema_version"] != 1:
        raise ValueError("Unsupported assessment schema")
    expected = input_sha256 or report_hash(audit)
    if _hash(assessment["audit_sha256"]) != expected:
        raise ValueError("Assessment binds a different audit")
    aliases = {}
    for node in audit.get("graph", {}).get("nodes", {}).values():
        if node.get("content_status") == "read":
            for alias in node["aliases"]:
                aliases[alias] = node["sha256"]
    from discovery import _Content, _POLICY
    content = _Content()
    home = Path(audit["scope"]["codex_home"])
    content.deny([Path.home() / path for path in _POLICY["known_sensitive_paths"]] + [home / "auth.json"])
    texts = {}

    def source(row):
        path = _string(row["source"])
        digest = _hash(row["source_sha256"])
        if aliases.get(path) != digest:
            raise ValueError("Evidence is outside readable audited sources or has a stale hash")
        if path not in texts:
            real = Path(path).resolve()
            if real.name == "SKILL.md" or ".git" in real.parts:
                raise ValueError("Evidence resolves to an excluded source")
            try:
                data = content.read(Path(path))
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError("Source changed since audit")
                texts[path] = data.decode("utf-8")
            except (OSError, UnicodeError) as error:
                raise ValueError("Source evidence cannot be verified: " + path) from error
        return texts[path]

    def evidence(rows):
        if not _list(rows):
            raise ValueError("Source evidence is required")
        for row in rows:
            _object(row, ("source", "source_sha256", "span", "text"), ("scenario_id", "provenance"))
            text = source(row)
            span = row["span"]
            if (not isinstance(span, list) or len(span) != 2 or any(type(n) is not int for n in span)
                    or not 0 <= span[0] < span[1] <= len(text) or text[span[0]:span[1]] != row["text"]):
                raise ValueError("Stale or invalid Unicode evidence span")
            if "scenario_id" in row:
                scenarios = [*audit.get("chains", []), *(m for g in audit.get("groups", []) for m in g["members"])]
                if row["scenario_id"] not in {c["scenario_id"] for c in scenarios}:
                    raise ValueError("Unknown evidence scenario")
                state = audit.get("graph", {}).get("states", {}).get(row["scenario_id"] + "|" + row["source"], {})
                if state.get("kind") not in {"leaf", "cycle"} or state.get("identity") not in audit["graph"]["nodes"]:
                    raise ValueError("Evidence alias is not readable in the named scenario")
            if "provenance" in row:
                _string(row["provenance"])
        return copy.deepcopy(rows)

    reviewed = []
    for row in _list(assessment.get("reviewed_sources", [])):
        _object(row, ("source", "source_sha256"))
        source(row)
        if row["source"] in reviewed:
            raise ValueError("Duplicate reviewed source")
        reviewed.append(row["source"])
    complete = assessment.get("semantic_review_complete", False)
    if type(complete) is not bool:
        raise ValueError("Semantic coverage must be boolean")
    semantic_complete = complete and set(reviewed) == set(aliases) and not audit.get("partial", False)
    allowed = _criteria()
    findings = []
    for row in _records(assessment.get("findings", [])):
        _object(row, ("id", "rule_id", "anchor", "evidence", "explanation", "confidence"))
        if row["rule_id"] not in allowed or row["confidence"] not in {"low", "medium", "high"}:
            raise ValueError("Unknown criterion or confidence")
        _string(row["anchor"]); _string(row["explanation"])
        findings.append(dict(copy.deepcopy(row), evidence=evidence(row["evidence"]), status="open"))
    by_id = {f["id"]: f for f in findings}
    decisions = {}
    for row in _records(assessment.get("owner_decisions", [])):
        _object(row, ("id", "decision", "scope", "provenance"))
        if row["decision"] not in {"approved", "deferred", "rejected"}:
            raise ValueError("Invalid recorded owner decision")
        _string(row["provenance"])
        if not _list(row["scope"]) or any(not isinstance(p, str) or not Path(p).is_absolute() for p in row["scope"]):
            raise ValueError("Decision scope requires absolute paths")
        decisions[row["id"]] = copy.deepcopy(row)
    disposed = set()
    for row in _list(assessment.get("dispositions", [])):
        _object(row, ("finding_id", "status", "reason"), ("evidence", "owner_decision_id"))
        id = row["finding_id"]
        if id not in by_id or id in disposed or row["status"] not in {"open", "rejected", "owner_deferred"}:
            raise ValueError("Unknown, duplicate or invalid disposition")
        disposed.add(id); _string(row["reason"])
        if row["status"] == "rejected":
            evidence(row.get("evidence", []))
        if row["status"] == "owner_deferred":
            decision = decisions.get(row.get("owner_decision_id"), {})
            if decision.get("decision") != "deferred" or not {e["source"] for e in by_id[id]["evidence"]} <= set(decision.get("scope", [])):
                raise ValueError("Deferral requires a matching recorded owner decision")
        by_id[id].update(status=row["status"], disposition=copy.deepcopy(row))
    dimensions = assessment.get("dimensions", {})
    if not isinstance(dimensions, dict) or set(dimensions) - WEIGHTS.keys():
        raise ValueError("Unknown rubric dimension")
    scores = {}
    for name, row in dimensions.items():
        if row is None:
            scores[name] = None
        else:
            _object(row, ("score", "evidence"))
            evidence(row["evidence"])
            scores[name] = row["score"]
    rubric = score_assessment(scores)
    verdicts = {}
    subrecord = assessment.get("criterion_verdicts", {"schema_version": 1, "entries": []})
    _object(subrecord, ("schema_version", "entries"))
    if type(subrecord["schema_version"]) is not int or subrecord["schema_version"] != 1:
        raise ValueError("Unsupported verdict schema")
    for row in _list(subrecord["entries"]):
        _object(row, ("rule_id", "verdict"))
        id = row["rule_id"]
        if id not in allowed or id in verdicts or row["verdict"] not in {"PASS", "FAIL", "NA"}:
            raise ValueError("Unknown/duplicate criterion or invalid verdict")
        verdicts[id] = row["verdict"]
    passed, failed, na = (sum(v == label for v in verdicts.values()) for label in ("PASS", "FAIL", "NA"))
    applicable = passed + failed
    summary = {"pass": passed, "fail": failed, "na": na, "applicable": applicable,
               "unassessed": len(allowed) - len(verdicts), "pass_rate": passed / applicable if applicable else None}
    resolves, targets = [], set()
    for row in _list(assessment.get("resolves", [])):
        _object(row, ("before_report_sha256", "before_finding_id", "evidence", "reason"))
        key = (_hash(row["before_report_sha256"]), _string(row["before_finding_id"]))
        if key in targets:
            raise ValueError("Duplicate resolution")
        targets.add(key); _string(row["reason"])
        resolves.append(dict(copy.deepcopy(row), evidence=evidence(row["evidence"]), baseline_validation="pending"))
    proposals = []
    for row in _records(assessment.get("proposals", [])):
        _object(row, ("id", "kind", "evidence", "destination", "replacement", "reason", "affected_references",
                      "expected_byte_delta", "expected_reading_change", "required_decisions"), ("observation",))
        evidence(row["evidence"])
        if row["kind"] not in {"replacement", "addition"} or not Path(_string(row["destination"])).is_absolute():
            raise ValueError("Invalid proposal kind/destination")
        if not isinstance(row["replacement"], str) or type(row["expected_byte_delta"]) is not int:
            raise ValueError("Proposal needs exact replacement and byte estimate")
        _string(row["reason"]); _string(row["expected_reading_change"])
        if any(p not in aliases for p in _list(row["affected_references"])):
            raise ValueError("Affected references must be audited aliases")
        for alias in dict.fromkeys([*row["affected_references"], *([row["destination"]] if row["destination"] in aliases else [])]):
            source({"source": alias, "source_sha256": aliases[alias]})
        required = _list(row["required_decisions"])
        if any(id not in decisions for id in required) or len(set(required)) != len(required):
            raise ValueError("Unknown/duplicate owner decision reference")
        approved = bool(required) and all(decisions[id]["decision"] == "approved" for id in required)
        destination_approved = approved and any(row["destination"] in decisions[id]["scope"] for id in required)
        state = "recorded_owner_approval" if destination_approved else "pending_new_destination" if row["destination"] not in aliases else "proposal_only"
        if row["kind"] == "addition":
            observation = _object(row.get("observation"), ("provenance", "detail", "information_gap", "utility", "diff"))
            if observation["provenance"] != "current_supplied_session":
                raise ValueError("Additions require current supplied/session provenance")
            for value in observation.values(): _string(value)
        proposals.append(dict(copy.deepcopy(row), decision_state=state))
    result = copy.deepcopy(audit)
    partial = bool(audit.get("partial")) or not semantic_complete
    active = any(f["status"] != "rejected" for f in findings) or failed or audit.get("exit_code") == 1
    result.update(assessment=copy.deepcopy(assessment), input_audit_sha256=expected, findings=findings,
        rubric=rubric, criterion_verdicts=verdicts, verdict_summary=summary, reviewed_sources=reviewed,
        owner_decisions=list(decisions.values()), resolves=resolves, proposals=proposals,
        semantic_review_complete=semantic_complete, partial=partial,
        exit_code=2 if audit.get("exit_code") == 2 else 3 if partial else 1 if active else 0)
    return result


def render_audit(report):
    lines = ["# Instruction audit", "", "Coverage: " + ("partial" if report.get("partial") else "declared area complete") + "."]
    scenarios = [*report.get("chains", []), *(m for g in report.get("groups", []) for m in g.get("members", []))]
    for chain in scenarios:
        if chain.get("raw_volume_exceeds_budget"):
            lines.append("- Loader original-volume overflow at " + str(chain.get("cwd")) + ".")
        elif chain.get("warning"):
            lines.append("- Loader original-volume warning at " + str(chain.get("cwd")) + ".")
    lines += ["", "Loader values are hypothetical; original bytes, included bytes and conditional references are separate.",
              "Directory subtotals measure unique reachable graph text, not filesystem directory size."]
    for finding in report.get("findings", []):
        lines += ["", "- " + finding["id"] + " [" + finding["rule_id"] + "] " + finding["status"] + ": " + finding["explanation"]]
        if finding.get("disposition"):
            lines.append("  Reason: " + finding["disposition"]["reason"])
    candidates = report.get("candidates", [])
    if candidates:
        lines += ["", "Lexical heuristic candidates (exceptions require review):"]
        for candidate in candidates[:6]:
            lines.append("- " + candidate["rule_id"] + ": " + candidate["path"])
        lines.append("All " + str(len(candidates)) + " candidate records and locations remain in audit.json.")
    if not isinstance(report.get("assessment"), dict):
        lines += ["", "Semantic assessment: unassessed. No semantic PASS is implied."]
    else:
        lines += ["", "Subjective rubric: " + str(report["rubric"]["total"]) + "; incomplete dimensions are unassessed.",
                  "Criterion verdict counts: " + json.dumps(report["verdict_summary"], sort_keys=True),
                  "These counts summarize supplied judgments; they are not a quality gate."]
    for proposal in report.get("proposals", []):
        lines += ["", "Proposal " + proposal["id"] + ": " + proposal["decision_state"],
                  "Destination: " + proposal["destination"], "Reason: " + proposal["reason"],
                  "Exact replacement (JSON string): " + json.dumps(proposal["replacement"], ensure_ascii=False)]
    lines += ["", "Full source evidence, exceptions, owner-decision provenance and route metrics are in audit.json.",
              "Recorded decisions do not authenticate consent or perform target changes."]
    return "\n".join(lines) + "\n"


def compare_reports(before, after, *, before_sha256=None):
    for report in (before, after): _report_shape(report)
    comparable = before["scope"] == after["scope"]
    old = {f["id"]: f for f in before.get("findings", [])}
    new = after.get("findings", [])
    def identity(f):
        return f["rule_id"], tuple(sorted({e["source"] for e in f["evidence"]})), f["anchor"]
    old_counts = Counter(identity(f) for f in old.values() if f["status"] != "rejected")
    targets = {}
    for row in after.get("resolves", []):
        if row["before_report_sha256"] != (before_sha256 or report_hash(before)) or row["before_finding_id"] not in old:
            raise ValueError("Resolution binds a different baseline report or unknown finding")
        targets[row["before_finding_id"]] = row
    delta = {"schema_version": 1, "comparable": comparable, "resolved": [], "retained": [], "unresolved": [],
             "new": [], "owner_deferred": [], "ambiguous": [], "fail_to_pass": [], "rejected": []}
    matched = set()
    for id, finding in old.items():
        if finding["status"] == "rejected":
            delta["rejected"].append(id)
            continue
        matches = [f for f in new if identity(f) == identity(finding)] if comparable else []
        if finding["status"] == "owner_deferred":
            delta["owner_deferred"].append(id)
        row = targets.get(id)
        covered = row and {e["source"] for e in [*finding["evidence"], *row["evidence"]]} <= set(after.get("reviewed_sources", []))
        if comparable and covered and not matches and finding["status"] != "owner_deferred":
            delta["resolved"].append(id)
        elif len(matches) == 1 and old_counts[identity(finding)] == 1:
            delta["retained"].append(id); matched.add(matches[0]["id"])
        else:
            delta["unresolved"].append(id)
            if len(matches) > 1 or old_counts[identity(finding)] > 1:
                delta["ambiguous"].append(id)
                matched.update(f["id"] for f in matches)
    delta["new"] = [f["id"] for f in new if f["id"] not in matched]
    b_verdicts, a_verdicts = before.get("criterion_verdicts", {}), after.get("criterion_verdicts", {})
    if comparable:
        delta["fail_to_pass"] = sorted(id for id, value in b_verdicts.items() if value == "FAIL" and a_verdicts.get(id) == "PASS")
    for key, metric in (("byte_delta", "unique_text_bytes"), ("reference_delta", "occurrences")):
        b, a = before.get("reading_summary", {}).get(metric), after.get("reading_summary", {}).get(metric)
        delta[key] = a - b if comparable and type(a) is int and type(b) is int else None
    delta.update(before_verdict_summary=before.get("verdict_summary"), after_verdict_summary=after.get("verdict_summary"),
        observed_regions_changed=before.get("chains") != after.get("chains"),
        semantic_assessment="assessed" if all(isinstance(r.get("assessment"), dict) for r in (before, after)) else "unassessed")
    partial = not comparable or before.get("partial", False) or after.get("partial", False)
    scenarios = [*after.get("chains", []), *(m for g in after.get("groups", []) for m in g.get("members", []))]
    remaining = {"candidate_count": len(after.get("candidates", [])),
                 "loader_warning_count": sum(bool(c.get("warning") or c.get("raw_volume_exceeds_budget")) for c in scenarios)}
    delta["remaining_scan_findings"] = remaining if any(remaining.values()) else {}
    active = delta["unresolved"] or delta["owner_deferred"] or any(f["status"] != "rejected" for f in new) or "FAIL" in a_verdicts.values() or any(remaining.values())
    delta.update(partial=partial, exit_code=2 if 2 in (before.get("exit_code"), after.get("exit_code")) else 3 if partial else 1 if active else 0)
    return delta


def score_assessment(dimensions):
    if not isinstance(dimensions, dict) or set(dimensions) - WEIGHTS.keys():
        raise ValueError("Unknown rubric dimension")
    for name, value in dimensions.items():
        if value is not None and (type(value) is not int or not 0 <= value <= WEIGHTS[name]):
            raise ValueError("Dimension points outside its weight")
    values = {name: dimensions.get(name) for name in WEIGHTS}
    complete = all(value is not None for value in values.values())
    return {"weights": dict(WEIGHTS), "dimensions": values, "complete": complete,
            "total": sum(values.values()) if complete else None}
