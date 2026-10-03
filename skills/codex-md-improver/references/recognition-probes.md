# Controlled recognition probes

Use only for a disputed reading trigger, source selection, scope or next action.
This is bounded decision evidence, not prompt-quality certification or authority
to change the target. Preserve required dedicated skill behavior and review gates.

Before dispatch, record expected choices and a simple positive control separately.
Build a worker packet containing only the exact guidance under test, a realistic
task, case ID and answer schema. Do not disclose expected answers, suspected defects,
reviews or correction history. Keep alternatives neutral; distinguish an actual
publication task from a typo or background reference to publication. Record the
guidance and exact packet SHA-256 hashes. Do not run audited embedded commands.

Request the family, effort and history settings in `assets/defaults.json` under
`recognition` (Sol/medium, fork none). Resolve the current literal model ID from
the host's available catalog at dispatch. Use a fresh child per disputed scenario
with its positive control. Supply realistic source names and relevant global/
project scope. If the requested runtime is unavailable, record an invalid probe
rather than silently substituting. A fresh thread does not prove memory isolation.

The worker returns one object per case:

```json
{"case_id":"case-name","selected_sources":[],"scope":"project","next_action":"chosen-action","unresolved":[]}
```

Predetermine the string vocabulary or evaluate a recorded answer against a sealed
semantic oracle before mechanical normalization. Preserve raw answers. Lists are
sets with no duplicate/non-string entries; their order does not matter. Do not
revise an oracle after seeing the answer simply to obtain a pass.

Call `scripts/recognition.py`'s `evaluate_probe(expected, observed, control, runtime)`.
The positive control is `{expected, observed, delivered: true, tool_status: "ok"}`.
Runtime records must include:

- `source_hash`, `packet_hash`: lowercase SHA-256; `client_version`: observed label.
- `requested: {model: "Sol", effort: "medium"}` and
  `resolved: {model: "<literal catalog ID>", effort: "medium"}`.
- `effective: {model: null, effort: null, status: "UNEXPOSED"}` when hidden;
  if exposed, record actual values with `status: "EXPOSED"` and verify they match
  the resolved selection. Requested values are not runtime attestation.
- `delivered: true`, `tool_status: "ok"` only after actual successful delivery.
- `isolation: {fork_turns: "none", history: "none", memory: "unknown",
  host_guidance: "unknown", target_guidance: "present"}`. Host guidance exposure
  is `present`, `absent` or `unknown`. Memory may be `shared` or `isolated` when
  evidenced. Absent/unknown guidance delivery makes the probe invalid.
- `tool_constraints: {containment: "prompt_only", detail: "<actual constraints>"}`;
  use `enforced` only with independent tool-denial evidence. Instructions to avoid
  tools do not enforce read-only behavior.

The evaluator preserves separate requested/resolved/effective fields and returns
`recognition`, `nonrecognition` or `invalid_probe`. Wrong case, bad shape, failed
control, missing delivery/runtime metadata or unavailable tools invalidate the
experiment and set `revision_eligible=false`. Only a valid mismatch is bounded
evidence for considering a revision. It never edits text, authenticates provenance
or checks whether arbitrary expected judgments were sound.

The receipt separately labels `context_status` as `limited` unless memory is
evidenced isolated and host guidance absent. `context_limitations` names the
uncontrolled exposures. Even matching choices with unknown context are limited
evidence; do not describe fork none as clean-context proof.

Fix concrete consequential defects. At a wording plateau consult the available
`skill-prompt-review` skill, collect remaining findings once through a fresh
read-only child and make one bounded revision. Then test the changed ambiguity
and control. Retain required guidance if removing it regresses observed choices;
stop synonym rounds when no behavioral counterexample remains. If tools or that
review skill are unavailable, report the limitation rather than claiming a run.
