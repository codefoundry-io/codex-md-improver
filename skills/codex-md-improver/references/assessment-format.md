# Assessment JSON schema, version 1

Use `report --audit scan/audit.json --assessment assessment.json --out NEW_OUT`.
Write the assessment outside audit inputs. All paths below are absolute audited
aliases, not arbitrary files. Every object rejects unknown fields unless listed
optional. Arrays default to empty when their optional top-level field is absent.

Required top-level fields are `schema_version: 1` and `audit_sha256`: SHA-256 of
the **actual audit JSON file bytes**. Optional top-level fields are `findings`,
`dimensions`, `dispositions`, `resolves`, `owner_decisions`, `proposals`,
`reviewed_sources`, `semantic_review_complete` and `criterion_verdicts`.
No narrative `summary`, `status` or scoring parser field is accepted.

## Source evidence

An evidence object requires `source`, `source_sha256`, `span: [start, end]`, and
`text`. Hash original source bytes with SHA-256; decode UTF-8 without newline
normalization to compute a nonempty half-open Unicode-character span and its exact
text. The alias/hash must appear among readable scan nodes and still match the
current file. Optional `scenario_id` must identify a scenario where that alias is
readable; optional `provenance` is a nonempty string. Evidence arrays are nonempty.

`reviewed_sources` contains `{source, source_sha256}` records, with no duplicate
source. Set `semantic_review_complete` to a boolean only for work actually done.
Complete semantic coverage requires every readable alias and a non-partial scan.
Inaccessible branches stay partial even when all available text was reviewed.

## Findings and judgments

- A `findings` record requires `id`, `rule_id`, `anchor`, `evidence`, `explanation`
  and `confidence`. IDs are unique nonempty strings; rule IDs come from
  `assets/criteria.json`. Use a stable semantic anchor independent of offsets.
  Confidence is `low`, `medium` or `high`. Findings begin `open`; do not add an
  input `status` field.
- `dimensions` maps any of the names below to `null` or `{score, evidence}`. Score
  is an integer earned-point count from zero through the named weight. Omitted
  and null dimensions remain unassessed; no total is available until all are scored.
  Names/weights: `commands_workflows` 20, `structure` 20, `non_obvious_patterns` 15,
  `concision` 15, `freshness` 15, `actionability` 15.
- `criterion_verdicts` requires `schema_version: 1` and `entries`, each exactly
  `{rule_id, verdict}`. Verdict is `PASS`, `FAIL` or `NA`; duplicate IDs are invalid.
  Missing IDs remain unassessed. Applicable=PASS+FAIL and rate=PASS/applicable
  (null at zero); NA and unassessed are separate. These are supplied judgments.

## Decisions and dispositions

`owner_decisions` records require unique `id`, `decision`, `scope` and `provenance`.
Decision is `approved`, `deferred` or `rejected`; scope is a nonempty list of
absolute paths. Provenance is a nonempty record of the actual owner's decision.
Do not invent a decision merely because a proposal needs one. Without a decision,
leave the finding open, state the pending question in its explanation/proposal,
and leave `required_decisions` empty. Recorded decisions do not authenticate consent.

A `dispositions` record requires `finding_id`, `status` and nonempty `reason`.
Each finding may have one disposition. Status is `open`, `rejected` or
`owner_deferred`; optional keys are `evidence` and `owner_decision_id`.
Rejection requires nonempty source evidence. Owner deferral requires a recorded
`deferred` decision whose scope includes every source of the finding; refer to its
ID via `owner_decision_id`. Awaiting a decision is not an owner-deferred decision.

## Proposals

Each proposal requires all of these fields:

| Field | Value |
| --- | --- |
| `id` | Unique nonempty identifier |
| `kind` | `replacement` or `addition` |
| `evidence` | Nonempty source evidence array |
| `destination` | Absolute target path |
| `replacement` | Exact replacement/addition text, possibly empty for deletion |
| `reason` | Nonempty rationale, alternatives and pending owner questions |
| `affected_references` | Array of readable audited aliases; each is rechecked |
| `expected_byte_delta` | Integer estimate, negative for reduction |
| `expected_reading_change` | Nonempty expected scope/reading effect |
| `required_decisions` | Unique IDs of actual recorded decisions, or empty |

Optional `observation` is mandatory for `addition`. It requires
`provenance: "current_supplied_session"` and nonempty `detail`, `information_gap`,
`utility`, `diff`. Do not mine history to populate it. A destination outside the
readable linked set remains `pending_new_destination` without a recorded approval
covering that destination. Existing destinations remain `proposal_only` without
such approval. No output state performs a target edit or grants migration authority.

## Cross-run resolutions

Each `resolves` record requires `before_report_sha256`, `before_finding_id`,
nonempty after-source `evidence` and `reason`. Bind the actual before JSON bytes
for CLI use. One binding per before hash/finding pair is allowed. The `report`
command records pending baseline validation; `compare` verifies the actual before
input, matching requested scope and complete reviewed evidence for affected sources.
Disappearance alone, shifted spans and uncovered sources are not proof of repair.

Direct Python API callers default to `report_hash()` canonical JSON; pass explicit
`input_sha256`/`before_sha256` to bind file transports. Never interchange those hashes.
