"""Pure evaluator for controlled choice probes; never dispatches providers."""
from copy import deepcopy
import json
from pathlib import Path
import re

_DEFAULT = json.loads((Path(__file__).resolve().parent.parent / "assets/defaults.json").read_text())["recognition"]
_ANSWER = {"case_id", "selected_sources", "scope", "next_action", "unresolved"}


def _string(value):
    return isinstance(value, str) and bool(value.strip())


def _answer(value):
    if not isinstance(value, dict) or set(value) != _ANSWER:
        return False
    if not all(_string(value[k]) for k in ("case_id", "scope", "next_action")):
        return False
    return all(isinstance(value[k], list) and all(_string(v) for v in value[k])
               and len(value[k]) == len(set(value[k])) for k in ("selected_sources", "unresolved"))


def _differences(expected, observed):
    return [key for key in sorted(_ANSWER - {"case_id"})
            if (sorted(expected[key]) != sorted(observed[key]) if isinstance(expected[key], list)
                else expected[key] != observed[key])]


def _runtime_valid(runtime):
    if not isinstance(runtime, dict):
        return False
    if runtime.get("delivered") is not True or runtime.get("tool_status") != "ok":
        return False
    if not all(isinstance(runtime.get(k), str) and re.fullmatch(r"[0-9a-f]{64}", runtime[k])
               for k in ("source_hash", "packet_hash")) or not _string(runtime.get("client_version")):
        return False
    requested, resolved, effective = [runtime.get(k) for k in ("requested", "resolved", "effective")]
    if not all(isinstance(v, dict) for v in (requested, resolved, effective)):
        return False
    if requested != {"model": _DEFAULT["model_family"], "effort": _DEFAULT["effort"]}:
        return False
    if not _string(resolved.get("model")) or resolved.get("effort") != requested["effort"]:
        return False
    if effective.get("status") == "UNEXPOSED":
        if set(effective) != {"model", "effort", "status"} or effective["model"] is not None or effective["effort"] is not None:
            return False
    elif effective.get("status") == "EXPOSED":
        if any(effective.get(k) != resolved.get(k) for k in ("model", "effort")):
            return False
    else:
        return False
    isolation, constraints = runtime.get("isolation"), runtime.get("tool_constraints")
    if not isinstance(isolation, dict) or not isinstance(constraints, dict):
        return False
    return (isolation.get("fork_turns") == _DEFAULT["fork_turns"] and isolation.get("history") == "none"
            and isolation.get("memory") in ("isolated", "shared", "unknown")
            and isolation.get("target_guidance") == "present"
            and isolation.get("host_guidance") in ("present", "absent", "unknown")
            and constraints.get("containment") in ("prompt_only", "enforced")
            and _string(constraints.get("detail")))


def evaluate_probe(expected, observed, control, runtime):
    """Validate delivery/control before comparing choices; return a detached receipt.

    Hashes and identity are host-supplied provenance, not authentication. A valid
    mismatch permits considering a bounded revision, never applies one.
    """
    data = runtime if isinstance(runtime, dict) else {}
    result = {"case_id": expected.get("case_id") if isinstance(expected, dict) else None,
              "status": "invalid_probe", "revision_eligible": False,
              "expected": deepcopy(expected), "observed": deepcopy(observed), "mismatch": [],
              "control_result": "invalid", "invalid_reasons": []}
    for key in ("isolation", "source_hash", "packet_hash", "requested", "resolved", "effective",
                "client_version", "tool_constraints"):
        result[key] = deepcopy(data.get(key))
    isolation = data.get("isolation")
    isolation = isolation if isinstance(isolation, dict) else {}
    limitations = []
    for key, clean in (("memory", "isolated"), ("host_guidance", "absent")):
        if isolation.get(key) != clean:
            value = isolation.get(key)
            label = value if isinstance(value, str) else "unverified"
            limitations.append(key + "_" + label)
    result["context_status"] = "limited" if limitations else "isolated"
    result["context_limitations"] = limitations
    if not _answer(expected) or not _answer(observed):
        result["invalid_reasons"].append("answer_shape")
    elif expected["case_id"] != observed["case_id"]:
        result["invalid_reasons"].append("wrong_case")
    if not _runtime_valid(runtime):
        result["invalid_reasons"].append("runtime_or_delivery")
    if (isinstance(control, dict) and control.get("delivered") is True and control.get("tool_status") == "ok"
            and _answer(control.get("expected")) and _answer(control.get("observed"))
            and control["expected"]["case_id"] == control["observed"]["case_id"]
            and not _differences(control["expected"], control["observed"])):
        result["control_result"] = "passed"
    else:
        result["invalid_reasons"].append("control")
    if result["invalid_reasons"]:
        return result
    result["mismatch"] = _differences(expected, observed)
    result["status"] = "nonrecognition" if result["mismatch"] else "recognition"
    result["revision_eligible"] = bool(result["mismatch"])
    return result
