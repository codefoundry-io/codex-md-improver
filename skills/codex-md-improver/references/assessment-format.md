# Assessment JSON schema, version 1

Use `report --audit scan/audit.json --assessment assessment.json --out NEW_OUT`.
NEW_OUT must be new under an existing parent. Write the assessment outside audit
inputs. All paths below are absolute audited
aliases, not arbitrary files. Every object rejects unknown fields unless listed
optional. Arrays default to empty when their optional top-level field is absent.

Required top-level fields are `schema_version: 1` and `audit_sha256`: SHA-256 of
the **actual audit JSON file bytes**. Optional top-level fields are `findings`,
`dimensions`, `dispositions`, `resolves`, `owner_decisions`, `proposals`,
`reviewed_sources`, `semantic_review_complete` and `criterion_verdicts`.
No narrative `summary`, `status` or scoring parser field is accepted.

## Source evidence

Reading volume is recorded separately from assessment judgments. The scan's
`reading_summary.directory_totals` and `directory_totals_by_scenario` retain byte
subtotals. `directory_summaries` and `directory_summaries_by_scenario` use the same
path/scenario keys and add `unique_text_bytes`, `physical_text_files`,
`read_conditions`, `frontiers`, `frontier_counts` and `lower_bound`.
Bytes and file counts deduplicate physical text identities. Aggregate records
union those identities across scenarios; conditions and frontiers retain scenario
provenance. Each condition has `scenario_id`, `source`, `occurrence_id` (null for
directory enumeration), `condition` and `target_path` (null for unresolved edges).
Frontier counts describe observed limited branches, not unknown files below them.
Cycles and nonlocal URLs do not imply missing coverage. Known unreadable directories
and excluded skill boundaries retain explicit lower-bound summaries.

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

## Scan settings input

These are inputs to `scan --settings SETTINGS.json`, separate from assessment
records. The file is a JSON object. Omit facts that are not established; supplied
values describe the requested scenario and never attest a live session.

Optional fields (unknown top-level fields are rejected):

| Field | Contract |
| --- | --- |
| `schema_version` | Integer `1` when present |
| `client` | Object with optional string `name` and `version`; no other fields |
| `non_project` | Supplied non-project loader fields, applied after observed user configuration |
| `session_overrides` | Supplied controlling loader fields, applied after project configuration |
| `trust` | Object mapping absolute lookup paths to `trusted`, `untrusted`, `unset`, or `unknown`; supply actual facts, not desired outcomes |
| `declared_bases` | Object mapping absolute source aliases to reference-base objects below |
| `environment_groups` | Ordered groups with explicit effective loader settings, described below |

Loader-field objects accept only `limit`, `fallback_names` and `root_markers`.
`limit` is a nonnegative integer or null. The other two fields are ordered arrays
of strings or null. Null means unknown. Fallback names are filtered for invalid
filenames and duplicates. Project layers cannot set root markers.

A reference-base object is exactly `{"kind":"document_dir"}`,
`{"kind":"scenario_project_root"}`, `{"kind":"scenario_cwd"}`, or
`{"kind":"absolute","path":"/absolute/base"}`. Relative Markdown links otherwise
default to their source directory. Plain paths retain distinct possible bases;
file existence alone does not decide the intended base.

For an established hypothetical 40000-byte budget, `RULES.md` fallback and
document-directory references, replace the absolute source alias in this example:

```json
{
  "schema_version": 1,
  "non_project": {
    "limit": 40000,
    "fallback_names": ["RULES.md"]
  },
  "declared_bases": {
    "/absolute/project/AGENTS.md": {"kind": "document_dir"}
  }
}
```

Each environment group has a unique nonempty `id`, a nonempty ordered `cwds`
array, and optional `effective_loader_settings`. Cwds are existing absolute
directories inside selected projects; no cwd may occur in two groups. An
explicit `--cwd` must match every grouped cwd. Selected project/cwd/group paths
must not contain `..` components. Symlink aliases retain the existing scenario
and trust semantics.

`effective_loader_settings` accepts the three loader fields above, optional
`trust` (the same four levels), and optional `provenance` (a JSON object).
Omitted controlling group fields remain unknown; they are not silently borrowed
from independent scenarios. Members share the supplied group configuration and
ordered byte budget. Do not create a group unless that runtime relationship is
established.

## Scan occurrence resolutions

`scan --resolutions RESOLUTIONS.json` takes a **JSON array**, not an assessment
object. These decisions classify source occurrences or resolve reference bases;
they differ from the assessment's cross-run finding `resolves` records.

Each record requires:

- `source`: absolute readable source alias.
- `source_sha256`: lowercase 64-character SHA-256 of the original source bytes.
- `span`: nonempty `[start, end]` half-open Unicode-character offsets after UTF-8
  decoding without newline normalization.
- `text`: the exact decoded source substring at that span.
- `classification`: `read_dependency`, `informational`, `example`, `output`, or
  `uncertain`.

Optional fields are `base` (one reference-base object above), `target` (the target
string), and `scenario_id` (an actual scenario containing that source). Without
`scenario_id`, a matching alias decision applies wherever the source occurs.
`informational`, `example` and `output` decisions cannot include `target` or
`base`; they stay inventoried without traversal. An `uncertain` decision still
leaves partial coverage.

Prefer the exact occurrence binding from `audit.json` under `graph.occurrences`.
Keep its `source`, `source_sha256`, `span` and `text`; add the justified decision.
A decision can also introduce a lexer-missed occurrence with a valid source span.
In that case `target` defaults to the span text if omitted. For existing lexer
occurrences an omitted target preserves the extracted target.

For the exact source text ``Use `guide.md` for implementation conventions.\n``
(the final `\n` denotes a newline), the guide span is `[5, 13]`. Replace the
source alias and hash placeholder with the actual scan binding:

```json
[
  {
    "source": "/absolute/project/AGENTS.md",
    "source_sha256": "<sha256 of original source bytes>",
    "span": [5, 13],
    "text": "guide.md",
    "classification": "read_dependency",
    "base": {"kind": "document_dir"}
  }
]
```

Unknown fields, duplicate source/span/scenario bindings, contradictory non-read
target/base fields, stale source/hash/span/text and unmatched decisions are
unusable input (exit 2). A non-read decision requires semantic evidence; an output
or example verb elsewhere on the line is not sufficient proof. Do not remove an
edge merely to make partial coverage disappear.

After reviewing uncertain/unresolved occurrences, write established decisions
outside the inputs and rescan the same selected scope into a **new** permitted
output directory with the settings and resolutions files. Verify terminal
routes and remaining frontiers. Expand only the supplied reference branch;
unresolved intent still needs an owner decision and stays partial. Report and
assess the resulting scan using its new actual JSON-byte hash.
