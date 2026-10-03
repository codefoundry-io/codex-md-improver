"""Original, bounded lexical assistance. Candidates never authorize a rewrite."""
from pathlib import Path
import re
from typing import TypedDict


class Candidate(TypedDict):
    rule_id: str
    path: str
    document_kind: str
    classification: str
    locations: list[dict]
    aggregate: dict | None
    explanation: str
    parameters: dict
    exceptions: list[str]


_PATTERNS = {
    "L-C8-BODY-DATE": r"\b\d{4}-\d{2}-\d{2}\b",
    "L-C8-BODY-YEAR": r"\b(?:since|until|as of|in|during|released? in)\s+(?:the year\s+)?(?:19|20)\d{2}\b",
    "L-C8-BODY-SEMVER": r"\bv?\d+\.\d+\.\d+(?:[-+][\w.-]+)?\b",
    "L-C8-BODY-TOOLVER": r"\b(?:python|node(?:\.js)?|java|ruby|rust|go|npm|gradle|kotlin)\s+v?\d+(?:\.\d+)*\b",
    "L-C8-BODY-MODEL": r"\b(?:gpt-\d[\w.-]*|o[134](?:-[\w.-]+)?|claude[- ](?:opus|sonnet|haiku)(?:[- ]\d[\w.-]*)?|gemini[- ]\d[\w.-]*(?: (?:pro|flash|ultra))?)\b",
    "L-C8-BODY-RECENCY": r"\b(?:(?:newly|recently) released|(?:latest|newest|recent) release)\b",
    "L-C4-EXCUSES": r"\bbecause (?:it(?: is|['’]s) (?:trivial|obvious|simple)|it takes too long|there is no time)\b",
    "L-C4-NARRATIVE": r"\b(?:the (?:model|agent|assistant) (?:kept (?:forgetting|failing)|previously failed)|last time (?:we|you|it) failed)\b",
    "L-C3": r"\b(?:price|pricing|usage (?:caps?|limits?)|costs? \$\d+)\b",
    "L-AA1": r"\b(?:as you requested|(?:file|task) we discussed|you asked me to|per our conversation|like you mentioned)\b",
    "L-AA2": r"\b(?:great question|sure(?=!)|let me|as an? (?:AI|language model)|I (?:apologize|hope this helps)|sorry|let me know if)\b!?",
    "L-AA3": r"\b(?:you might want to (?:consider|try)|if you['’]d like,? please|it would be great if you could)\b",
    "L-AA5": r"[\U0001f300-\U0001faff\u2600-\u27bf]",
}
_EXCEPTIONS = {
    "L-C8-BODY-DATE": ["runtime date required by the operation"],
    "L-C8-BODY-YEAR": ["operational temporal condition or required provenance"],
    "L-C8-BODY-SEMVER": ["exact command identifier or compatibility requirement"],
    "L-C8-BODY-TOOLVER": ["runtime requirement or exact command identifier"],
    "L-C8-BODY-MODEL": ["exact command model identifier or tested capability condition"],
    "L-C8-BODY-RECENCY": ["operational condition requiring a current release"],
    "L-C6": ["emphasis needed for a destructive operation"],
    "L-C4-EXCUSES": ["hazard recognition paired with the required action"],
    "L-C4-NARRATIVE": ["quoted example or necessary corrective context"],
    "L-C10": ["necessary scope bound or named hazard"],
    "L-C9-TOC": ["navigation supplied by the consuming interface"],
    "L-C3": ["necessary project fact tied to an input, action or output"],
    "L-AA1": ["quoted example of runtime user input"],
    "L-AA2": ["quoted example or literal response required by a consumer"],
    "L-AA3": ["meaningful uncertainty that must remain explicit"],
    "L-AA5": ["functional formatting or a legend"],
    "L-AA6": ["audience unknown; confirm consumer language before judging"],
}
_LANGUAGE_LIMIT = "English phrase heuristics; non-Latin detection cannot establish audience or detect Latin-language drift."


def _body(text):
    """Keep offsets and all body lines; mask fenced content without changing width."""
    raw = text.splitlines(keepends=True)
    start = 0
    if raw and raw[0].strip() == "---":
        for index, line in enumerate(raw[1:], 1):
            if line.strip() in ("---", "..."):
                start = index + 1
                break
    result, offset, fence = [], 0, None
    for index, line in enumerate(raw):
        visible = line
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if index < start:
            visible = " " * len(line)
        elif fence:
            visible = " " * len(line)
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
            visible = " " * len(line)
        if index >= start:
            result.append((index + 1, offset, visible))
        offset += len(line)
    return result


def _mask_quotes(line):
    return re.sub(r'`+[^`]*`+|"[^"\n]*"|“[^”\n]*”|(?<!\w)\x27[^\x27\n]*\x27',
                  lambda match: " " * len(match[0]), line)


def find_candidates(text: str, path: Path, document_kind: str,
                    enabled_ids: set[str]) -> list[Candidate]:
    if document_kind not in {"agents_guidance", "linked_instruction", "markdown_reference"}:
        return []
    lines = _body(text)
    candidates = []

    def location(line, offset, match):
        return {"start": offset + match.start(), "end": offset + match.end(),
                "line": line, "end_line": line, "text": text[offset + match.start():offset + match.end()]}

    def emit(rule, locations, aggregate=None, parameters=None):
        candidates.append(Candidate(rule_id=rule, path=str(path), document_kind=document_kind,
            classification="heuristic_candidate", locations=locations, aggregate=aggregate,
            explanation="Review this lexical candidate in context; exceptions require semantic evidence.",
            parameters={"language_limit": _LANGUAGE_LIMIT, **(parameters or {})},
            exceptions=list(_EXCEPTIONS[rule])))

    for rule in sorted(enabled_ids & _PATTERNS.keys()):
        for number, offset, visible in lines:
            for match in re.finditer(_PATTERNS[rule], visible, re.IGNORECASE):
                emit(rule, [location(number, offset, match)])
    for rule, pattern, flags in (
        ("L-C6", r"\b(?:MUST|NEVER|MANDATORY|CRITICAL|ALWAYS|REQUIRED)\b", 0),
        ("L-C10", r"\b(?:do not|don['’]t|never|must not|cannot|can['’]t)\b", re.IGNORECASE),
    ):
        if rule not in enabled_ids or len(lines) < 25:
            continue
        hits, matching_lines = [], 0
        for number, offset, visible in lines:
            matches = list(re.finditer(pattern, _mask_quotes(visible), flags))
            matching_lines += bool(matches)
            hits.extend(location(number, offset, match) for match in matches)
        count = matching_lines if rule == "L-C6" else len(hits)
        if count * 100 > 8 * len(lines):
            emit(rule, hits, {"count": count, "body_lines": len(lines),
                             "per_100_lines": 100 * count / len(lines)},
                 {"minimum_body_lines": 25, "strictly_above_per_100": 8,
                  "count_unit": "lines" if rule == "L-C6" else "occurrences"})
    if "L-C9-TOC" in enabled_ids and document_kind == "markdown_reference" and len(lines) > 100:
        toc = any(re.match(r"^\s*#{1,6}\s+(?:table of contents|contents|toc)\s*#*\s*$", line, re.I)
                  for _, _, line in lines)
        if not toc:
            emit("L-C9-TOC", [], {"body_lines": len(lines)}, {"strictly_above_lines": 100})
    if "L-AA6" in enabled_ids:
        korean_audience = any(re.search(r"\baudience:\s*Korean(?:-speaking)?\b|대상\s*:\s*한국어", line, re.I)
                              for _, _, line in lines)
        pattern = r"[\u0370-\u052f\u0590-\u08ff\u0900-\u1fff\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]+"
        for number, offset, visible in lines:
            for match in re.finditer(pattern, _mask_quotes(visible)):
                if korean_audience and re.fullmatch(r"[\uac00-\ud7af]+", match[0]):
                    continue
                emit("L-AA6", [location(number, offset, match)], parameters={"audience": "unknown"})
    return sorted(candidates, key=lambda c: (c["locations"][0]["start"] if c["locations"] else len(text), c["rule_id"]))
