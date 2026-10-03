# codex-md-improver

A read-only Codex skill for auditing AGENTS.md instruction chains and their linked
documents. It reports loader selection, byte inclusion, conditional reading costs,
candidate issues and source-bound semantic proposals. Existing SKILL.md files are
excluded audit boundaries. It never applies target changes automatically.

Requires Python 3.11+. The runtime analyzer uses the standard library. Source is
available in this public repository. Native macOS and Ubuntu checks passed on
Python 3.11/3.12, with the Python 3.10 rejection guard; see the
[initial implementation run](https://github.com/codefoundry-io/codex-md-improver/actions/runs/37116926970)
and [current CI results](https://github.com/codefoundry-io/codex-md-improver/actions/workflows/ci.yml).
A tagged release and fresh installed-skill verification are still pending.

## Use from a checkout

The canonical source is `skills/codex-md-improver/`. The repository discovery link
`.agents/skills/codex-md-improver` points there. Open a fresh Codex session in this
repository and explicitly invoke `$codex-md-improver`, specifying the project(s)
to audit. Source discovery does not prove an installed copy was loaded.

For a deterministic scan, start from the repository root. Replace `PROJECT` with
the absolute path of the project to audit. The example uses the current Codex home
and a fresh temporary report area; confirm that this location is host-permitted
and outside all audit inputs. Follow the executing host's shell/permission policy.

```sh
SKILL_DIR="$(pwd)/skills/codex-md-improver"
PROJECT="/absolute/path/to/project"
CODEX_HOME_PATH="${CODEX_HOME:-$HOME/.codex}"
AUDIT_RUN="$(mktemp -d "${TMPDIR:-/tmp}/codex-md-audit.XXXXXX")"
SCAN_OUT="$AUDIT_RUN/scan"

python3 -B "$SKILL_DIR/scripts/md_improver.py" scan \
  --project "$PROJECT" --codex-home "$CODEX_HOME_PATH" --out "$SCAN_OUT"
```

Keep the `AUDIT_RUN` value while working; temporary files
may expire under the host's cleanup policy. Copy reports to a chosen persistent
location if they need to survive that cleanup.

Repeat `--project` for multiple roots. Default scope covers accessible nested
instruction chains; `--cwd` explicitly narrows a scenario. Optional `--settings`
and `--resolutions` accept established scenario inputs. Observed files plus defaults
do not attest a live session. Unknown trust and inaccessible branches stay visible.

The scan writes `audit.json`, `audit.md`, complete `routes.jsonl` and `manifest.json`.
Original bytes, loader-charged bytes and linked reading volume are distinct metrics.
Shared physical text is counted uniquely while all route identities are retained.
Directory subtotals count reachable graph text, not filesystem directory size.
Per-scenario subtotals preserve different relative-reference meanings; shared
directory totals count the union of physical text across those scenarios.
Directory summaries also include physical text-file counts, scenario-bound read
conditions and frontier kinds/counts. Counts describe known readable text; a lower
bound does not imply that inaccessible directories contain no additional files.

Large audits have no bounded memory or runtime guarantee. The reader retains whole
file bytes, including binaries; graph construction can revisit shared paths; route
emission synchronously updates its receipt for every row. `--max-routes` limits
emitted routes, not graph construction or retained file bytes.

The skill reviews candidates and writes an assessment using the
[record schema](skills/codex-md-improver/references/assessment-format.md), then runs:

```sh
ASSESSMENT="$AUDIT_RUN/assessment.json"  # create this from the schema first
REPORT_OUT="$AUDIT_RUN/report"
python3 -B "$SKILL_DIR/scripts/md_improver.py" report \
  --audit "$SCAN_OUT/audit.json" --assessment "$ASSESSMENT" --out "$REPORT_OUT"

BEFORE_REPORT="/absolute/path/to/prior/audit.json"
AFTER_REPORT="$REPORT_OUT/audit.json"
DELTA_OUT="$AUDIT_RUN/delta"
python3 -B "$SKILL_DIR/scripts/md_improver.py" compare \
  --before "$BEFORE_REPORT" --after "$AFTER_REPORT" --out "$DELTA_OUT"
```

Each output directory must be new and its parent must already exist. CLI assessment hashes bind the actual input
JSON bytes. Findings retain exact source hashes/spans; rejected leads and pending
owner questions stay visible. Scope moves, conflicts, potentially intentional
duplicates and new destinations require owner decisions before any target edit.
Temporary output is usable when host-permitted; retain needed artifacts before
its host-specific expiry. Inaccessible inputs are not a reason to weaken permissions.

Exit codes: 0 completed analysis without signaled issues; 1 candidates/findings/
warnings; 2 unusable inputs/output; 3 partial coverage. Precedence is 2, 3, 1, 0.
Zero does not certify prompt quality. Missing semantic judgments remain unassessed.
Scores and criterion counts summarize supplied judgments; they do not authorize
edits, publication or release.

## Controlled choice checks

For a disputed trigger/scope/action, the skill requests a fresh Sol/medium child
with no inherited history. Expectations and control results stay outside its
packet. The pure evaluator distinguishes actual mismatches from invalid delivery,
bad shapes and failed controls. Memory/host exposure and effective runtime identity
are recorded separately. Read the [probe procedure](skills/codex-md-improver/references/recognition-probes.md).
These bounded choices do not replace dedicated skill behavior or owner review.

## Verify and build a candidate

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B tools/package_skill.py --skill-root skills/codex-md-improver \
  --out-dir "$NEW_ABSOLUTE_PACKAGE_DIR" --version 0.1.0
```

`0.1.0` is a candidate version, not a published tag. The archive includes an exact
selected-file allowlist, the subtree MIT notice and a sorted SHA-256/size manifest.
Unexpected files, source symlinks, missing resources and machine-specific paths
are rejected. Byte equality is not an authenticity claim; verify the source commit
and release provenance separately. The manual candidate workflow uploads an Actions
artifact only; it creates no tag, GitHub Release or installation.

## Install an approved release

After source publication and an immutable release ref are approved, use the
official Codex skill installer. Resolve its installed helper from the active
`skill-installer` skill; do not substitute this source checkout for installer proof.
Set `INSTALLER` to that helper, `APPROVED_REF` to the approved immutable tag/commit
and `PROBE_REPO` to a newly created disposable discovery repository outside source:

```sh
python3 -B "$INSTALLER" --repo codefoundry-io/codex-md-improver \
  --path skills/codex-md-improver --ref "$APPROVED_REF" \
  --dest "$PROBE_REPO/.agents/skills"
```

Compare source/ref/archive/installed hashes and LICENSE bytes. Start a fresh Codex
session from that disposable repository, explicitly invoke `$codex-md-improver`,
and record the actual loaded path/hash before claiming installed exposure. Native
host results remain separate. This disposable test is not the owner's installation.

Actual installation requires a chosen supported destination, inspection of existing
same-name contents and separate authorization to replace them. When replacement is
approved, preserve a task-owned recovery copy with a stated retention decision.
Direct repository installation is the intended route; marketplace publication is
not claimed. Final merge, tag/release and actual installation have separate gates.

Licensed under [MIT](LICENSE). See [provenance](docs/design/third-party-provenance.md).
