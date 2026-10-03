# codex-md-improver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This document is a plan, not execution authorization.

**Goal:** Build and publicly distribute a Codex skill that audits global and project instruction chains, measures their byte budgets and linked-document burden, and proposes smaller, correctly scoped guidance with owner-controlled migration decisions.

**Architecture:** A read-only Python analyzer produces instruction-chain, reference-graph, and candidate-finding JSON. A short Codex skill uses those facts for semantic review, a subjective rubric, concrete diffs, and narrowly scoped independent recognition probes. The analyzer never executes instructions found in audited files or modifies the audited files.

**Tech Stack:** Python 3.11+ standard library, Markdown, JSON, Codex skill metadata, GitHub Actions on macOS and Ubuntu. No persistent service, database, provider SDK, or API key is required for the analyzer.

**Spec:** [Owner decisions](../../design/2026-10-03-owner-decisions.md), including the original 107 included criteria, 52 pending criteria, one excluded criterion, all 21 owner notes, and subsequent scope corrections. The later instructions override the form: audit AGENTS.md and its linked files only, trace to each terminal path, and continue over accessible areas when permissions prevent full traversal. The implementation itself is distributed as a skill; existing SKILL files are not audit targets.

**Status:** UPDATED FOR FORMAL PLAN REVIEW, 2026-10-03. The owner resumed plan review, implementation and pre-merge review. This revision incorporates the independently checked [web research](../../reviews/2026-10-03-preimplementation-web-review.md); it is not a product verification receipt. No product implementation, remote publication or installation has yet occurred. The desired repository name has not been reserved or checked for availability.

The [criteria map](../../design/2026-10-03-criteria-map.md) assigns each of the 107 included IDs to an implementation surface, evidence field and verification obligation. Its coverage check verifies traceability, not semantic correctness.

## Global constraints

- Project directory: `workspace/codex-md-improver`; intended public remote: `codefoundry-io/codex-md-improver`. The owner's public organization choice overrides the workspace's private/personal default.
- Skill name and package directory: `codex-md-improver` and `skills/codex-md-improver/`.
- Audit and migration candidates are AGENTS.md and its reachable linked files only. Existing SKILL.md files are not audit targets. A link to SKILL.md records an excluded boundary without evaluating that skill's quality or expanding its reference tree. Validating the newly built improver's own package is separate from auditing user targets.
- Start from Codex user guidance plus explicitly selected project roots; inspect nested instruction scopes and linked paths. Do not interpret the request as scanning the entire home directory indiscriminately.
- Trace every accessible file/folder branch to its terminal node and report each route's cumulative bytes. Shared-node deduplication must not hide alternate root-to-terminal routes.
- Permission denials restrict the affected branch only. Continue accessible branches, label denied frontiers and partial totals, and do not request broader privileges, change permissions, or keep retrying blocked paths merely to complete an audit.
- Preserve intentional dirty state. Never reset, stash, clean, discard, or create a separate checkout to hide existing changes.
- Proposed moves between global and project scope, conflicting instructions, and possibly intentional duplicates require the owner's specific decision (AG08, C15, P17). Prepare location, reason, alternatives, and diff before asking.
- Preserve exact CLI model IDs, environment facts, meaningful exceptions, execution boundaries, and existing JSON configuration arrangements. A regex hit never authorizes removal.
- Web search is allowed for current model behavior, configuration alternatives, and concrete product claims (AG13, AG15, P11, AA4). Prefer official sources and report unresolved facts. This does not authorize configuration changes.
- macOS and Ubuntu are supported. CI executes each operating system's checks on that operating system; a Mac run does not prove Ubuntu behavior. U07 remains pending as a reusable audit criterion.
- User review is the selected acceptance method. Unit tests and recognition evidence support that review; they do not replace it.
- Pending questionnaire criteria remain pending, including vendor O/A/G criteria, SKILL 200-line warnings, and the legacy score parser. AG24's `/init` workflow is excluded.
- Complete the approved plan through implementation and pre-merge review after formal plan admission. Target migration, final merge, public release and actual owner installation retain their separate authorization boundaries.
- Adopt TRIAD public-v2 for this project: all enabled legs must explicitly approve the same immutable basis. The configured roster is Opus 5.5/xhigh, Google Pro/high, Flash/high and Astra/high; exact IDs and routes live in `.agents/triad-review-legs.json`. Plan review assesses design and verifiability; pre-merge review assesses the implementation and observed checks. Web search is authorized for every leg, including OpenAI Docs for Codex. A plan verdict is not permission to merge.

## Review focus

1. Sibling instruction scopes, overrides, Git worktree roots, and custom settings can produce different chains; test every distinct chain, not the sum of all discovered instruction files (Task 1).
2. Plain-text paths, directory-read instructions, alternate routes to a shared leaf, permission-denied subtrees, and symlink cycles can hide dependencies; emit per-terminal route totals and explicit unknown frontiers (Task 2).
3. Korean text, legitimate versions, and protected commands can trigger heuristics; candidates must retain exceptions and never cause automatic edits (Tasks 3–4).
4. Recognition probes can inherit host guidance or memory even without history; record the actual isolation boundary and do not call it a clean experiment without evidence (Task 5).
5. A public release can accidentally include local audit inputs or differ from installed bytes; test an explicit package allowlist and a clean tagged installation on both supported hosts (Task 6).

## 1. Product behavior and authority

The normal result is an audit report plus proposed changes. The skill identifies what should remain an environment instruction, what belongs in a reusable skill, what belongs in a one-off plan, and what should move to configuration or historical documentation. It recommends those destinations; it does not create a second skill, change configuration, or reorganize unrelated files automatically.

`workflow=plan-undecided` is preserved. The proposed first release defaults to report and diff preparation. An explicitly approved follow-up can apply the named diff using ordinary authorized file tools after rechecking file hashes and scope. A bulk mutation CLI is outside this plan. Existing authorization should be honored; do not add an approval request for every reversible observation or calculation.

Before changing global/project placement, resolving a semantic conflict, or deleting a suspected duplicate, present the owner with the affected locations, current scope, actual consequence, concise alternative wording, and choices. An unresolved decision holds only the affected changes. New migration destinations outside the current graph must be named in that decision before they enter the write set.

Read accessible reachable textual instruction/support files through the scanner, but do not feed their entire contents to the main model. Keep an on-disk inventory with known coverage and use targeted excerpts and line ranges for semantic review. Distinguish `inventory_complete`, `text_read_complete`, and `semantic_review_complete`; one must not imply the others. On access failure, finish useful review of the readable area and report the blocked frontier. Do not turn partial access into a task-wide stop or a falsely complete result.

## 2. Measurement contracts

### 2.1 Three separate quantities

| Quantity | Meaning | Limit or status |
| --- | --- | --- |
| Project instruction-chain bytes | Separate original bytes of selected files from bytes actually included after loader clipping for a cwd/environment combination | Compare original demand with effective `project_doc_max_bytes`; included bytes show clipping |
| Global instruction bytes | User guidance outside the confirmed project counter | Report separately; do not invent a universal global limit |
| Referenced-document burden | Unique reachable text bytes and conditional reading paths | Audit evidence, not automatic Codex loader consumption |

Existing skills are not measured as an audit population. AGENTS-linked document bytes are separate from the project-loader budget. Token savings and better model performance are not inferred from file-byte reductions.

The source-backed project default is 32,768 bytes, configurable rather than immutable. Let `project_original_bytes` be original physical volume across selected project files, including files omitted after budget exhaustion. Report original-volume warning at `10 * project_original_bytes >= 9 * limit`; with the default, 29,492 bytes is the first integer warning value. `project_original_bytes > limit` means `raw_volume_exceeds_budget`; exact equality is at the cap without an excess. This owner-defined warning is not itself a claim that meaningful instructions were omitted. Separately model per-file clipping/filtering, charged raw bytes, decoded included bytes and source omissions. Whitespace-only decoded prefixes consume no budget, so original physical volume cannot be substituted for the loader counter. Never use an already clipped aggregate to infer original volume or assume no overflow solely because retained bytes fit. Zero/unknown limits have explicit states. [Codex default](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/config/src/config_toml.rs#L74), [loading implementation](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs#L58).

Resolve root markers, fallback filenames, project trust, explicit session overrides, and the byte budget into a narrow `LoaderSettings` record **per hypothetical cwd/scenario**, with provenance. Apply relevant trusted project configuration from root to cwd; nearer settings override ancestor values, subject to field-specific loader behavior. **Root discovery markers exclude Project configuration layers** in the pinned loader; derive them from non-project layers and explicit non-project overrides. Read only relevant nonsecret settings; do not copy whole configuration files into reports. Unresolved trust or session overrides remain explicit uncertainty. If the active Desktop/session configuration is unavailable, report a stated default or supplied scenario, not a verified live-runtime result. This is a narrow settings resolver, not a full managed-policy/configuration emulator.

Read relevant fields from `<codex-home>/config.toml`; apply supplied `non_project` values over that observed base, then eligible trusted project fields, then explicit session overrides. For root markers, omit the project step. Supplied trust facts override observed user-config trust entries. Unobserved system, profile, cloud and session layers remain labeled unknown unless supplied as scenario facts. The selected project limits inventory, not loader ancestor discovery: a cwd inside a selected subdirectory can have a marker root above it, whose applicable ancestor instruction files are included read-only in that scenario.

By default inventory every accessible directory in each selected project. Collapse regions only when their ordered selected chains, effective relevant settings, trust and unresolved provenance match; a nested configuration file can create a region without a new AGENTS.md. Evaluate intermediate and sibling regions as well as leaf directories. `--cwd` explicitly narrows one selected project to that current-directory chain. Recognize nested Git repositories and worktree `.git` files as loader boundaries only when the effective non-project marker contract selects `.git`; inventory their existence separately. With no matching marker, use the pinned cwd-only fallback. Multiple simultaneous roots share a budget only when explicitly supplied as one ordered turn-environment group with common session settings; independent project runs are not added together. Without a verified grouping, report separate scenarios.

Conformance fixtures must pin the selected loader contract for overrides, fallback ordering, empty/whitespace files, read failures, decoding, and clipping. Do not guess an edge behavior from filenames alone. The CLI discovery model and GitHub changed-file review scope are labeled separately; this tool does not pretend to implement GitHub's review service. [Official discovery guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Model the pinned loader separately from scanner accessibility. Selection precedes empty-content filtering: an empty override shadows ordinary AGENTS.md. A non-NotFound read failure aborts that environment's modeled load; whether the caller omits it or fails depends on runtime context and may remain unknown. A readable-area lower bound is not automatically a lower bound on loaded context. Track retained raw source bytes and decoded content bytes separately: truncating UTF-8 before lossy decoding may increase decoded length. Preserve within-environment raw-byte accounting and outer simultaneous-environment decoded-byte accounting from the pinned source. Do not claim the scanner's permissions establish runtime permissions.

Pin the loader's Unicode whitespace definition, not Python's broader default stripping: Rust uses `White_Space`; Python also uses bidi classes. Include U+001C–U+001F as non-whitespace loader content and ordinary Unicode space controls in conformance fixtures. [Rust definition](https://doc.rust-lang.org/std/primitive.char.html#method.is_whitespace), [Python definition](https://docs.python.org/3/library/stdtypes.html#str.isspace).

### 2.2 Reference graph

- Start with selected global/project instruction files and discovered instruction variants needed for scope analysis. Mark active versus shadowed variants. Do not seed or audit standalone SKILL files; a reachable SKILL.md is an `excluded_skill` boundary rather than an instruction to expand its contents.
- Find Markdown inline/reference-style links, table cells, backtick paths, plain-text file paths, and prose that instructs reading files or directories. Generalize C9 beyond a folder named `references`.
- Resolve absolute paths, `~`, and relative paths. Markdown links default to the referring document's directory; an explicit declared base takes precedence. Plain instruction paths may be document-relative or project-relative: retain both candidates and request a decision if context cannot establish one. Existence alone is not proof of the intended base.
- Resolve each occurrence in its `ChainReport` scenario. A declared base has kind `document_dir`, `scenario_project_root`, `scenario_cwd`, or `absolute` (with its path); do not freeze a scenario-relative meaning into one global absolute path. Bind semantic decisions to source hash/span and, when specific, scenario ID. One global instruction can therefore point to different project documents in two scenarios while its physical text is cached once.
- Separate URL fragments and `path:line` suffixes from the file identity. Support documented environment placeholders and finite globs without invoking a shell. Unknown variables, natural-language folder descriptions, and ambiguous expansions remain unresolved edges.
- Classify a path as a read dependency, informational example, output destination, or uncertain candidate before recursively following it. Report all recognized path candidates; do not treat output paths as instructions or execute sample commands.
- A linked directory is enumerated recursively. Keep aliases while deduplicating content by resolved identity; detect file and directory symlink cycles. Explicit linked absolute/tilde targets outside selected projects are included when readable under the existing process permissions and owner scope; this never authorizes unrelated home-directory crawling or bypassing a host deny rule. Missing, denied, changed-during-read, undecodable, binary, and special-file targets retain explicit statuses. Catch access errors per file/directory and continue siblings without privilege escalation or permission changes.
- During recursive enumeration, a directory containing SKILL.md is one `excluded_skill` frontier; do not enumerate its skill subtree. A separately explicit link from AGENTS guidance to a non-SKILL support file in that directory remains a related-file target, without authorizing a surrounding skill audit.
- Normal text is read and hashed once; binaries receive metadata and an explicit content-review limit. Do not read devices, sockets, or FIFOs. A technical exclusion such as Git object storage appears as an excluded frontier with limited coverage, not a complete leaf. Do not exclude a readable linked folder merely because it contains generated reports or another tool's output. Snapshot the input inventory before writing this run's output, so generating reports does not expand the audit recursively. Any user-imposed resource cap produces `partial`, never an unqualified all-files result.
- The deterministic lexer cannot prove it found every natural-language reference. A semantic residual pass checks unmatched read instructions and ambiguous path spans; a remaining ambiguity prevents an exhaustive-coverage claim, but does not prevent review of the accessible resolved area.
- URL references are inventoried, not automatically crawled. Fetch only sources needed to verify the selected factual claim, recording the URL and retrieval evidence.
- Cache physical content separately from reference occurrences: each occurrence retains its referring alias/base, source span and condition. A verified semantic decision may resolve one occurrence through an explicit resolution input and bounded rescan; unresolved alternatives are not both traversed automatically. The resolution must bind the source hash/span, and stale decisions are rejected visibly.

Removing a link must account for incoming references, consumers of exact text, and load-bearing constraints. Prefer a narrower reading condition or a short retained rule when it preserves the original purpose. Removing the edge does not authorize deleting the linked file or its history.

#### Per-terminal path reporting

The filesystem and links are presented as a tree for reading, but the underlying structure can be a graph. Read and hash each physical text file once, then enumerate each distinct accessible root-to-terminal route. Use an ancestor set per route for cycle detection; a global visited set alone would incorrectly erase routes through shared files. Stream rows to disk so a large set of routes does not require retaining all expanded paths in memory.

Store shared immutable chain/node records plus streamed route records; report progress and write a usable partial receipt on interruption or an explicitly chosen resource cap. Route count can grow combinatorially even with few files. Do not promise bounded runtime/output from streaming and do not silently impose a fixed route/depth cap or replace full routes with samples. Markdown may summarize/link the complete route stream instead of duplicating it all in memory.

Each `TerminalPathReport` contains the scope/cwd region, ordered global and project loader sources, originating instruction file, full reference route, edge reading conditions, terminal kind, terminal file size when known, and cumulative known unique original file bytes on that route. Keep `global_original_bytes`, `project_original_bytes`, `project_included_bytes`, and conditional reference-file bytes as separate columns. The combined route-original total is a file-volume measure, not proof of consumed context. Do not add a range-level rereading simulator or claim real tokens, message overhead or actual repeated tool reads.

An accessible leaf with no outgoing read dependencies is `leaf`; also emit `empty_directory`, `blocked_frontier`, `missing_target`, `unresolved`, `cycle`, and `excluded_skill` terminal rows. A denied directory is an unknown subtree, not an ordinary completed leaf; its number of hidden leaves is unknown. Unknown sizes are null, never zero. Known totals for incomplete routes are lower bounds, and readable content is distinguished from size-only metadata.

For example, a 1,000-byte AGENTS source that links a 200-byte shared guide, which links leaves of 300 and 400 bytes, produces route totals of 1,500 and 1,600 bytes. The unique graph total is 1,900 bytes; adding the route totals would double-count shared content. A second route to the same leaf remains a separate row while its physical content is read once. Where a reference repeats an already loaded AGENTS source, do not add that file again to the route's unique context total.

The owner-defined original-volume warning compares `project_original_bytes` with `project_doc_max_bytes`; actual loader effects come from per-file conformance modeling. A large conditional reference-route total is reading burden, not loader overflow. No reference-context cap is invented. The terminal report and both before/after comparisons cover every accessible route, not just the deepest directory or largest leaf.

For each directory-read dependency also report known unique descendant text bytes, file count, read conditions and unresolved frontiers. For example, 200 distinct 5 KiB files yield a 1,000 KiB directory subtotal alongside all 200 routes. A scenario total includes shared AGENTS prefixes once. This aggregate measures file volume, not actual reads or tokens.

### 2.3 Heuristics, assessment, and comparison

Implement only the selected lint branches: six C8 body checks, C6, both C4 checks, C10, C9 reference TOC, C3, and AA1/AA2/AA3/AA5/AA6. Use explicit criterion allowlists; do not execute the existing lint script wholesale because it also enables pending checks. Its code may be studied as behavior evidence; any code reuse requires license/provenance verification before public redistribution.

Each candidate includes its rule ID, document kind, evidence span or aggregate, detector parameters, and applicable exception. English phrase and non-Latin heuristics must disclose language limits. A Korean audience does not make Korean text an error. Version/model candidates preserve exact command identifiers and legitimate runtime dates. Hard factual failures, heuristic hits, semantic findings, unresolved decisions, and read errors are separate classes.

Classify readable targets as AGENTS guidance, linked instruction text, Markdown reference, or code/config evidence. Review prose rules only where the content is guidance; reading a code file to verify a command does not make that code a prompt to rewrite. The reference TOC candidate applies to Markdown reference text, not arbitrary source files. SKILL-only criteria have no user-target application after the scope correction; applicable ideas such as recognizable conditional reads remain covered by AG10/C9. Required structure of the newly created improver skill is a separate package concern.

Selected detector behavior supplies the C6/C10 density threshold (more than 8 per 100 lines, minimum 25 body lines) and the reference TOC threshold (more than 100 lines). These are candidate defaults, not universal constraints. The unselected general threshold policy and SKILL 200-line detector are not enabled. Keep full locations in JSON; the report can summarize the first six and link the remainder. Missing input is an error even if the legacy lint CLI would have skipped it with exit 0.

Honor the selected I03 rubric without presenting model judgment as an objective measurement:

| Dimension | Weight | Proposed coverage of the additional selected requirements |
| --- | ---: | --- |
| Commands and workflows | 20 | Actual commands, non-executed examples, scope of permission and configuration alternatives |
| Structure | 20 | Global/project placement, all distinct chains, reference graph, instruction/skill/plan boundaries |
| Non-obvious patterns | 15 | Necessary project facts, exceptions, valid duplicates, preserved rationale |
| Concision | 15 | Byte burden, unnecessary links, repeated history, unnecessary choreography |
| Freshness | 15 | Verified paths and current claims, useful exact identifiers retained |
| Actionability | 15 | Concrete replacements, owner decision records, recognizable reading conditions |

This mapping is a proposed implementation decision for I03's extra note. It keeps the original 100 points instead of silently inventing more weights. Report evidence and unscored dimensions; compute a total only when all six are assessed. Coverage failures and overflow remain prominent regardless of score. The owner can adjust the mapping during plan review.

For L-SCORE-DELTA, use structured audit JSON, not the unselected legacy Markdown parser. Compare findings by stable rule/evidence identity and explicit disposition. A missing finding in a partial scan is not a fix; changes of scope are labeled incomparable. Provide newly identified, retained, resolved-with-evidence, and owner-deferred findings plus byte/reference deltas. No automatic pass-rate gate, A–F grade, majority vote, or family-averaged quality score is introduced.

The selected L-SCORE-DELTA wording additionally requests BEFORE/AFTER applicable counts, PASS/FAIL counts, pass rates, and FAIL-to-PASS transitions. Preserve that requested output in the requirements. Its denominator, missing-verdict handling, and duplicate-verdict semantics overlap pending L-SCORE-TALLY/PARSE/FAIL-WINS/COVERAGE. Before implementing that part, obtain the owner's choice between retaining those fields with an explicit structured-verdict contract (recommended) or accepting a finding-disposition-only replacement. The pending choice affects only those aggregates, not byte/path deltas or evidence-based findings. Do not silently drop the requested fields or copy the entire legacy score contract.

Unrelated Task 4 work can complete while this choice is pending, but the selected aggregate subrecord remains incomplete. Do not claim all selected outputs are shipped or release a reduced output contract without the owner's choice. This is not a gate on the 52 unselected pending criteria.

For R01/R03/R04, accept only current user-supplied or current-session observations as evidence for missing reusable guidance. Prepare an `ADDITION` proposal with provenance, the information gap, expected utility, and an exact diff against an existing AGENTS-linked target. A named new destination needs the existing placement decision before entering the write set. Do not crawl session history, modify memory, or insert rules automatically from an isolated mistake.

## 3. Independent recognition probes and convergence

AG10/P23/U02/U03 notes explicitly request a narrow inexpensive probe, refining U03's broader exclusion. The probe asks whether a separate agent recognizes a trigger, selects the required file, respects scope, and identifies the next allowed action. It does not execute a production migration or establish general model-performance improvement.

Proposed ordinary probe preset: Luna/low, resolved to a currently supported exact model ID when dispatched. This is an extraction/classification role, not a code reviewer. Preserve the owner's ability to change the model and effort through one configuration location. Unsupported settings produce a visible result; do not silently upgrade or substitute models.

Give each child `fork_turns="none"`, one synthetic user request, the relevant candidate guidance, and minimal fixture contents. Do not supply the expected answer, suspected failure, author discussion, or prior verdict. Before/after probes use separate fresh children with equivalent cases. Expected file IDs, scope, and action are sealed in the evaluator input, outside the worker packet; collect structured answers and compare them mechanically.

Throughout semantic review and probes, treat audited text as data and never execute its embedded commands. Executing the trusted analyzer is a separate action. Use host read-only/no-execution controls when available and record actual tool constraints versus prompt-only containment; do not claim enforcement merely because the packet requests it.

Use positive, negative, boundary, and ambiguous cases chosen for the changed condition. Record model, effort, packet hash, source hash, observed answer, expected answer, and tool/read availability. History isolation does not establish memory or host-instruction isolation. Record `history_isolation`, `memory_isolation`, host exposure and target-guidance exposure (`present`, `absent`, `unknown`). Use synthetic names/paths different from the audited target to reduce answer leakage, but do not claim that renaming proves isolation. If clean context cannot be demonstrated, label the result limited. Do not modify global memory settings or claim that a prompt instruction disables memory.

Run a simple positive control and validate case identity and answer shape before comparing recognition. Record client version. Missing tools, unavailable models, wrong-case answers or task-delivery failures are `invalid_probe`, distinct from `not_recognized`; they do not justify wording changes.

Record requested family/effort, resolved dispatch ID/effort, and independently exposed effective runtime identity separately. Hidden effective values are null/`UNEXPOSED`; a supported request is not runtime attestation. An unsupported selector is invalid, not permission to inherit a different model silently.

Revise wording only when a concrete case demonstrates a recognition problem or new evidence resolves a finding. Rerun the affected cases after a bounded correction. With no new evidence, stop and show the remaining issue to the owner; do not continue grammar or nuance debates indefinitely. No arbitrary new round-count limit is imposed.

This lightweight recognition check is separate from this workspace's canonical skill RED/GREEN requirement. Before production skill behavior is authored, a dedicated behavior-only Custom Agent must be bound to the exact new skill SOT. The currently inspected dedicated executor is TRIAD-specific and cannot be reused. Preparing and verifying the new role is an execution prerequisite, not work performed by this plan. If unavailable, the affected behavior test is blocked; static or leader-run tests do not replace it.

## 4. Source layout and public boundary

All product paths below are relative to the new project repository, not the parent infrastructure repository.

| Path | Responsibility |
| --- | --- |
| `AGENTS.md`, `README.md`, `.gitignore`, `LICENSE` | Portable contributor guidance, usage/install instructions, generated-file exclusions, selected license |
| `skills/codex-md-improver/SKILL.md` | Short entrypoint: triggers, audit sequence, actual authority boundaries, conditional references |
| `skills/codex-md-improver/agents/openai.yaml` | Codex UI metadata/policy; does not register arbitrary source folders |
| `.agents/skills/codex-md-improver` | Repository discovery symlink to `../../skills/codex-md-improver`; one canonical source |
| `.agents/triad-review-legs.json` | Public-v2 review roster; exact model IDs, efforts and routes in one place |
| `skills/codex-md-improver/LICENSE` | MIT license inside the installable subtree, equal to the repository license |
| `skills/codex-md-improver/assets/defaults.json` | Byte-warning policy, selected detector IDs, probe family/effort; exact resolved IDs recorded per run |
| `skills/codex-md-improver/assets/criteria.json` | Included-ID traceability to conditional rule groups, evidence fields and verification kinds |
| `skills/codex-md-improver/scripts/md_improver.py` | CLI, input validation, report serialization, explicit output ownership |
| `skills/codex-md-improver/scripts/discovery.py` | Loader settings, source inventory, scope regions, project budgets |
| `skills/codex-md-improver/scripts/references.py` | Path extraction/resolution, graph traversal, completeness and reader statuses |
| `skills/codex-md-improver/scripts/lint_candidates.py` | Included detectors and explicit candidate exceptions |
| `skills/codex-md-improver/scripts/reporting.py` | Assessment records, subjective rubric arithmetic, structured before/after comparison |
| `skills/codex-md-improver/scripts/recognition.py` | Pure probe-validity and recognition evaluator; no provider invocation |
| `skills/codex-md-improver/references/review-rules.md` | Consolidated selected semantic rules and placement decisions; no 160-item preload |
| `skills/codex-md-improver/references/recognition-probes.md` | Conditional independent recognition procedure and evidence limits |
| `tests/test_discovery.py`, `tests/test_references.py`, `tests/test_lint_candidates.py`, `tests/test_reporting.py`, `tests/test_recognition.py`, `tests/test_distribution.py` | Deterministic behavior, probe evaluation and packaging tests with synthetic fixtures |
| `tests/test_rule_coverage.py` | Exact included-ID set and uniqueness, group references and selected detector coverage; no semantic oracle |
| `tests/fixtures/`, `tests/recognition-cases.json` | Small synthetic edge cases and sealed recognition expectations |
| `.github/workflows/ci.yml`, `.github/workflows/release.yml` | Per-OS checks and reproducible release of the approved tag |
| `tools/package_skill.py` | Explicit package allowlist, sorted hashes, archive creation |

The exact canonical SOT is `<project-root>/skills/codex-md-improver`. Installed folders and caches are consumers. Resolve bundled scripts/resources relative to the loaded skill's directory and pass the target project as a separate absolute argument; never assume the target contains the skill source. A dedicated executor definition is host-owned configuration; it is not part of the public skill package and must point to this SOT through the verified host mechanism.

Generated run files live under an explicit new output directory outside selected project roots and linked input directories by default, such as a user-chosen report folder containing `.codex-md-improver-runs/<run-id>/`. A deliberate output-inside-target choice requires `--allow-output-in-target` and is recorded; existing input files remain read-only. Reject an output path that already exists or aliases an input, even with that flag. The run owns `audit.json`, `audit.md`, the route stream, optional proposal patch and a manifest of created paths. Recognition fixtures use one run-owned temporary root. Retain requested reports/proposals/evidence; remove only this run's disposable fixtures. Never recursively clean a caller directory or delete referenced research as a side effect of pruning a link.

Public commits use an explicit allowlist. Exclude actual audited documents, personal absolute paths, raw owner attachments, configuration dumps, provider logs, probe transcripts from real work, installed caches, and local executor definitions. This decision record is paraphrased/limited to planning choices and contains no local attachment path. The owner selected MIT on 2026-10-03. Verify any borrowed-code rights separately; required notices must be inside the installed skill subtree or have an explicit tested installation mapping.

## 5. Data interfaces

Use typed records in the module that owns them; do not add an otherwise unnecessary shared framework.

| Interface | Owner and minimum contract |
| --- | --- |
| `LoaderSettings` | `discovery.py`: cwd/scenario, limit, fallback names, root markers, trust facts, client/version, provenance, unresolved overrides; hashable region identity |
| `ScopeRequest` | `discovery.py`: Codex home, selected project roots/cwds, optional simultaneous-environment groups; no standalone skill target |
| `ChainReport` | `discovery.py`: scope/settings region, ordered sources, original/retained raw/decoded project bytes, separate global bytes, clipping/omissions, modeled loader outcome, warning state, uncertainty |
| `ReferenceGraph` | `references.py`: cached physical nodes/aliases/read states; scenario-bound edge occurrences with source hashes/spans/base kinds, resolved bases, alternatives, conditions, directory aggregates, completeness limits |
| `TerminalPathReport` | `references.py`: scope region, loader sources, complete reference route, terminal kind, known component/total bytes, exclusions, size/content status, lower-bound flag |
| `Candidate` | `lint_candidates.py`: rule ID, path, kind, evidence spans or aggregate, explanation, parameters, exceptions |
| `AuditReport` | `reporting.py`: schema version, run scope/fingerprints, chains, graph summary, findings, subjective assessments, pending owner decisions, completeness |
| `AuditDelta` | `reporting.py`: comparable scope, matched findings and dispositions, byte/reference changes, incomparable or unresolved cases |
| `AssessmentInput` | `reporting.py`: version, audit SHA-256, source-hash bindings, semantic findings, dimension assessments, dispositions, owner-decision records and proposals, each labeled with its source/provenance |

Proposed CLI: `python3 <loaded-skill-directory>/scripts/md_improver.py scan --project <absolute-root> [--project <absolute-root> ...] [--cwd <absolute-directory>] [--codex-home <path>] [--settings <narrow-settings.json>] [--resolutions <verified-decisions.json>] --out <new-run-directory>`; `compare --before <audit.json> --after <audit.json> --out <new-run-directory>`. `--cwd` requires exactly one selected project and must belong to it; omitted means whole-project coverage. There is no `--skill` audit option. Check Python >=3.11 before imports requiring that version and provide a clear setup error; do not implement a replacement TOML parser.

Add `report --audit <audit.json> --assessment <assessment.json> --out <new-run-directory>` to ingest the skill's judgments into a **new** enriched report; never hand-edit scanner output or overwrite the original run. `AssessmentInput` version 1 binds the input audit hash and every cited source hash/span. It carries semantic finding IDs/rules/evidence, six optional dimension scores with evidence, explicit dispositions, owner-decision provenance and proposal records. Unknown IDs, wrong types, invalid score ranges, stale hashes or dispositions without an identified finding are rejected. Model judgment and recorded owner decisions remain distinct; file/schema validity does not authenticate consent. Only the skill/leader records actual owner decisions. `compare` consumes these enriched reports and treats missing assessment as unassessed, not PASS or resolution. No Markdown parser is introduced. The aggregate-verdict subrecord remains disabled until the pending owner contract is resolved.

`--settings` accepts a narrow version-1 object: `client` (name/version), `non_project` (budget, ordered fallback names, ordered root markers), `trust` (absolute root to trusted/untrusted/unknown), `session_overrides` (budget/fallback names/root markers), `environment_groups` (unique ID, ordered explicitly selected cwds, common session overrides) and `declared_bases` (source alias to a base-kind record as defined above). Missing values retain labeled defaults/unknowns; unknown keys and invalid types are input errors. Each group member must lie in a selected root, cannot appear twice or belong to two groups, and uses a recorded order. Relevant user and trusted project TOML fields are layered under the stated precedence; project-local root markers are ignored by discovery. This schema transports only the modeled fields, not arbitrary Codex configuration.

Scanning and comparison return `0` for a complete result without candidates, `1` for a complete result containing findings/candidates, `3` for a successfully produced partial-area report, and `2` for invalid input, no usable readable inputs, or inability to write the requested report. The skill treats code 3 as a usable result and continues reviewing the accessible area; it does not retry for greater permissions. Findings remain in partial reports. CLI help states that exit 0 does not certify prompt quality or runtime behavior.

`report` uses the same precedence and returns 1 for any open candidate/finding, including deferred items. `compare` returns 1 for new or retained open findings (not just regressions); a complete resolved-only delta returns 0. These statuses do not imply completion of unassessed semantic work.

Exit precedence is 2, then 3, then 1, then 0. Missing/denied/changed/unresolved dependencies, truncated traversal, technical exclusions, and unreviewable binary/special/undecodable linked content yield 3 when usable input remains; incomparable comparison also yields 3. Intentional `excluded_skill`, cycle terminals, inventoried URLs and non-read examples/outputs do not alone make the declared local audit partial. Scanner completion never implies completed semantic review: absent semantic assessment is labeled unassessed, not fabricated failure or success. An assessment declaring unresolved semantic coverage yields 3 in `report`. Unsupported Python yields 2 via an older-interpreter-parseable entrypoint. Pin these cases in CLI tests.

## 6. Implementation tasks

Task-file shorthand `scripts/`, `assets/`, `references/`, `agents/openai.yaml` and `SKILL.md` below is relative to `skills/codex-md-improver/`; tests, tools, workflows and project metadata remain repository-relative.

### Task 1: Establish the repository and instruction-chain analyzer

**Files:** project metadata, `assets/defaults.json`, `scripts/discovery.py`, `scripts/md_improver.py`, `tests/test_discovery.py`, initial CI workflow. The project AGENTS.md is newly authored; do not invoke the excluded `/init` maintenance workflow.

**Interfaces:** `resolve_settings(request: ScopeRequest, cwd: Path) -> LoaderSettings`; `discover_chains(request: ScopeRequest) -> list[ChainReport]` resolves settings for each candidate region and shares proven-identical prefixes.

- [x] Established planning-only Git history on `main` and branch `codex/initial-skill`; created project AGENTS.md. Before future staging, recheck this Git root and preserve parent dirty changes. No remote was created.
- [ ] Write failing synthetic tests: `test_override_and_fallback_selection`, `test_sibling_regions_not_combined`, `test_git_worktree_and_nested_root`, `test_unknown_effective_settings_are_labeled`, and `test_simultaneous_group_budget`.
- [ ] Add `test_identical_chain_different_config_region` (20,000 bytes with 32,768 versus 16,384 budgets), untrusted/unknown nested settings, explicit session overrides, and `test_cwd_narrowing_is_explicit`. Assert default traversal retains every configuration/instruction region.
- [ ] Assert project-local root markers do not change discovery; a non-project marker override excluding `.git` changes the boundary; no matching marker selects only the cwd. Test settings JSON and group/base transport through the CLI, not only function calls.
- [ ] Test relevant Codex-home TOML fields and supplied settings/session precedence, unknown upstream layers, and selected-subdirectory scope with an applicable ancestor marker root and AGENTS file above the selected inventory root.
- [ ] Pin the current official loader edge behavior in fixtures before implementing empty/whitespace files, trust, unreadable files, UTF-8 clipping, and zero budget. Record which behavior remains unverified for Desktop.
- [ ] Assert empty override shadows the ordinary file, environment read failure does not report the readable remainder as actually included, and partial multibyte clipping distinguishes raw retained and decoded lengths both within a chain and between ordered simultaneous environments.
- [ ] Assert U+001C–U+001F remain loader content, while Unicode White_Space-only decoded prefixes are omitted; do not use bare Python `strip()` as the conformance oracle.
- [ ] Add assertions for non-whitespace fixtures: 29,491 project bytes is below warning; 29,492 warns; 32,768 warns without excess; 32,769 has raw-volume excess and actual clipping. A 40,000-space ancestor plus a 100-byte child retains the physical warning while including all child content and charging only 100 bytes. Changing global bytes must not change project utilization. A nondefault budget changes the boundary.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_discovery.py' -v`; observe the intended failure, implement the two interfaces and CLI input contract, rerun to pass.
- [ ] Commit only this repository's named files after verification. Establish macOS/Ubuntu CI with Python 3.11 and 3.12 jobs; local macOS evidence is separate from remote jobs, which cannot run until remote publication is authorized. Test the pre-import version guard, including an older-interpreter-parseable entrypoint.
- [ ] Add a separate Ubuntu Python 3.10 setup-guard smoke job: actual older interpreter invocation must return 2 with the setup message before unsupported imports. This does not claim Python 3.10 support.

### Task 2: Traverse references and measure reading burden

**Files:** `scripts/references.py`, graph integration in `scripts/md_improver.py`, `tests/test_references.py`, synthetic fixtures.

**Interfaces:** `build_reference_graph(chains: list[ChainReport], declared_bases: dict[Path, dict], resolutions: list[dict]) -> ReferenceGraph`; `iter_terminal_paths(graph: ReferenceGraph, chain: ChainReport) -> Iterator[TerminalPathReport]`; `summarize_reading_paths(graph: ReferenceGraph) -> dict`. Each chain supplies scenario project root/cwd, selected and scope-analysis source paths. Resolution records bind source hash/span, optional scenario restriction and chosen base kind/target; they do not grant new access rights.

- [ ] Write failing tests for inline/reference-style links, table/backtick/plain paths, absolute/relative/tilde paths, declared bases, spaces/Korean names, `path:line`, fragments, variables/globs, and file-versus-folder reads.
- [ ] Assert ambiguous bases stay unresolved even when one file exists; output/example paths do not become unconditional read dependencies; referenced Markdown links do not increase the Codex project-loader budget.
- [ ] Assert two aliases of one physical file preserve different relative-reference meanings while reading content once; verified occurrence resolution expands only that branch and rejects a stale source hash.
- [ ] Assert one global source with a scenario-project-root reference resolves to a 10 KiB file in project A and a 50 KiB file in project B, with separate routes/totals and one physical source read. An unresolved base is never guessed from existence.
- [ ] Assert recursive directory coverage, duplicate aliases, cyclic symlinks, missing/denied targets, non-UTF text, binary/special-file statuses, and a file changing during read. A resource-capped scan must remain partial. A SKILL.md edge terminates as excluded and its contents are not quality-audited.
- [ ] Assert a folder read stops at a SKILL.md-containing directory, while an explicit AGENTS link to one non-SKILL support file there includes that file without scanning its surrounding skill.
- [ ] Assert explicitly linked generated documents are traversed, technical exclusions produce visible limited-coverage frontiers, and writing this run's results cannot add new scan inputs.
- [ ] Add `test_each_terminal_path_has_its_own_total`, `test_shared_leaf_keeps_both_routes`, `test_loaded_source_is_not_double_counted`, and `test_denied_subtree_preserves_readable_sibling_report`. Pin the 1,500/1,600 route totals and 1,900 unique-graph total above; assert unknown leaves/bytes remain null and denied paths never invoke an elevation or chmod operation. Inject PermissionError rather than relying on host/root-specific chmod behavior.
- [ ] Assert partial access produces a usable report with exit 3, per-terminal coverage, and retained findings. If no input can be read, produce the coverage/error receipt without claiming any content review.
- [ ] Assert a 200-file directory has a unique descendant subtotal alongside all routes, and that interruption/resource limits retain a partial receipt and already streamed rows without reporting exhaustive coverage.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_references.py' -v` to RED; implement the three interfaces; rerun to GREEN and rerun discovery integration tests.
- [ ] Verify the input tree fingerprint is unchanged. Report necessary read-condition refinements and incoming-reference impacts without editing target files; commit named product/test files.

### Task 3: Implement selected candidate detectors

**Files:** `scripts/lint_candidates.py`, detector allowlist in `assets/defaults.json`, `tests/test_lint_candidates.py`.

**Interface:** `find_candidates(text: str, path: Path, document_kind: str, enabled_ids: set[str]) -> list[Candidate]`.

- [ ] Write failing positive and exception fixtures for every selected detector branch. Assert description-only detectors, frontmatter checks, the 200-line body warning, and other pending detectors are not enabled.
- [ ] Pin C6 line-count versus C10 occurrence-count semantics, their minimum body length, reference-only TOC behavior, and line offsets across CRLF/frontmatter. Preserve all candidate locations in JSON.
- [ ] Assert legitimate exact model IDs and protected commands remain unchanged; Korean audience evidence suppresses an automatic language verdict; the result remains a candidate where context is unresolved.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_lint_candidates.py' -v` to RED, implement `find_candidates`, rerun to GREEN. No inspected command is executed.
- [ ] Record licensing/attribution decisions for any borrowed implementation. Prefer a small original implementation of the selected behavior to a dependency on a user's installed skill; commit named files.

### Task 4: Assemble evidence, scoring, decisions, and migration proposals

**Files:** `scripts/reporting.py`, CLI report/compare integration, `references/review-rules.md`, `assets/criteria.json`, `tests/test_reporting.py`, `tests/test_rule_coverage.py`.

**Interfaces:** `enrich_audit(audit: AuditReport, assessment: AssessmentInput) -> AuditReport`; `render_audit(report: AuditReport) -> str`; `compare_reports(before: AuditReport, after: AuditReport) -> AuditDelta`; `score_assessment(dimensions: dict[str, int | None]) -> dict`.

- [ ] Write failing tests for six rubric weights summing to 100, unassessed dimensions producing an incomplete total, and a high subjective score never concealing loader overflow or incomplete coverage.
- [ ] Drive source-bound semantic findings, dimensions, owner deferrals and proposals through `report` then `compare`; reject stale hashes, invalid IDs/ranges and unsupported structures without mutating input reports. Verify a scan without assessment is unassessed and cannot imply PASS.
- [ ] Resolve the L-SCORE-DELTA aggregate-output decision before writing aggregate tests. If retained, pin the agreed applicable/PASS/FAIL/pass-rate and transition semantics in structured fixtures; do not assume pending legacy parser behavior.
- [ ] Write failing tests that a partial after-scan cannot resolve a previous finding, a moved span does not create a false fix, changed scope is incomparable, and owner-deferred items remain visible.
- [ ] Define proposal records with source spans/hashes, destination, reason, replacement text, affected references, expected byte/reading changes, and required owner decisions. A destination outside the linked migration set stays pending until explicitly accepted.
- [ ] Consolidate selected rules into conditional semantic groups: placement/chain scope, reference burden, durable facts, wording/duplication, verified environment, and actionable proposals. Keep the full decision ledger outside the runtime prompt.
- [ ] Implement the criteria-map metadata and exact 107-ID/17-detector coverage checks. Test source-bound R01/R03/R04 observation ADDITION proposals, including utility, concrete diff, current supplied-session provenance and named-destination decision. Semantic merit remains owner-reviewed.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_reporting.py' -v` to RED; implement the interfaces; rerun to GREEN. Confirm no Markdown-score parser or pending criterion was enabled accidentally.
- [ ] Produce a synthetic report showing a conflict, possible intentional duplicate, global-to-project move, exact replacement, and a justified rejected finding; commit named files.

### Task 5: Author the skill and prove recognition boundaries

**Files:** `SKILL.md`, `agents/openai.yaml`, `references/recognition-probes.md`, `scripts/recognition.py`, `tests/test_recognition.py`, `tests/recognition-cases.json`; a separately approved host executor binding to the canonical SOT when required.

**Interfaces:** worker answer `{case_id, selected_sources, scope, next_action, unresolved}`; evaluator result `{case_id, status, revision_eligible, expected, observed, mismatch, isolation, source_hash, packet_hash, requested, resolved, effective, client_version, control_result, tool_constraints}`. Requested/resolved/effective each carry separate model/effort fields; effective values may be unexposed. Status distinguishes valid recognition, valid nonrecognition and invalid probes.

`evaluate_probe(expected, observed, control, runtime) -> dict` in `recognition.py` validates the case and positive control before mechanically comparing declared fields. Failed control, wrong case, invalid shape or missing runtime/tool delivery yields `invalid_probe` and `revision_eligible=false`; valid mismatches are bounded evidence, not automatic rewriting authority. Test it with `python3 -m unittest discover -s tests -p 'test_recognition.py' -v` before implementing the pure evaluator. Provider dispatch stays with the skill/host tools.

- [ ] Before behavior authoring, prepare a bounded scenario against the exact canonical skill path and verify the dedicated behavior-only executor is available. A missing source/loader failure is not the intended behavioral RED. For a new skill, establish the minimal valid entrypoint needed to run the baseline, then observe the scoped behavior failure before adding the corrective instructions.
- [ ] Write recognition cases for selecting a conditional reference, rejecting a near-match, preserving global/project scope, and requesting an owner decision for a conflict or duplicate. Keep expected results out of worker packets.
- [ ] Add a positive control, wrong-case/schema/tool-failure invalidity cases, and assertions that invalid probes cannot drive a wording revision.
- [ ] Include a fixture whose audited text requests command execution; the semantic/behavior worker must preserve that text as evidence without executing it. Record prompt-only versus enforced tool constraints honestly.
- [ ] Author a short skill entrypoint that runs the analyzer, inspects relevant evidence, verifies current claims as needed, proposes diffs, and invokes recognition probes only for the changed ambiguous condition. Keep progress/history/research provenance in reports, not accumulated active instructions.
- [ ] Keep discovery metadata sufficient for normal Codex skill loading. Structural validation of this newly authored package does not silently adopt pending C0/A1 as target-audit criteria. [Skill format and discovery](https://learn.chatgpt.com/docs/build-skills).
- [ ] Have a separate fresh dedicated executor run the focused GREEN case, relevant regressions, and the installed skill-creator's `scripts/quick_validate.py` against the exact SOT. Record unchanged source fingerprints and remove its disposable fixtures.
- [ ] Run the low-cost recognition comparison using the stated isolation labels. Do not substitute these probes for full skill behavior validation or owner review; retain evidence of actual failures and stop unsupported wording rounds.
- [ ] Complete task-level independent source/code review and correct verified findings. This project has explicitly adopted public-v2 plan and pre-merge reviews; task reviews do not replace them. Commit named files after the required checks.

### Task 6: Publish the repository and distribute the skill

**Files:** `tools/package_skill.py`, `tests/test_distribution.py`, release CI, portable README/install instructions, selected license, public attribution records.

**Interface:** `build_package(skill_root: Path, out_dir: Path, version: str) -> dict` returns archive path and a sorted file/hash manifest; includes only the selected skill tree and required license/attribution material.

- [ ] Write failing package tests for unexpected files, escaping symlinks, local absolute paths in shipped instructions, missing required resources, and hash mismatch. Exclude real input documents, `.git`, caches, reports, fixtures, and machine-specific configs from the release package.
- [ ] Test repository discovery through the approved symlink, script/resource resolution from an installed skill with an unrelated target cwd, and equality of required notices in source, archive and selected-subtree installation.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_distribution.py' -v` to RED; implement packaging; rerun to GREEN and run the complete deterministic suite on the current macOS host. A host-specific unavailable behavior executor remains explicitly unverified. Ubuntu and GitHub CI results remain unverified until their later native jobs run.
- [x] Record the owner's MIT license choice. Required LICENSE files and third-party provenance still need implementation/verification before publication.
- [ ] Verify third-party provenance and the public Git history independently of the package; a clean archive does not prove a clean history.
- [ ] Prepare the exact public file/history allowlist and local verification receipt; resolve the public-source publication authorization for those concrete commits before remote creation/push. Verify organization permission and name availability. An existing repository needs an explicit reuse decision. Keep the owner's **public** repository choice; do not create a private substitute or fabricate an Ubuntu host. Once authorized, run `gh repo create codefoundry-io/codex-md-improver --public --source . --remote origin` and push only the approved commits/work branch. Public source publication is distinct from a tagged release.
- [ ] After the remote exists, run GitHub Actions natively on macOS and Ubuntu for Python 3.11/3.12, collect exact-commit results, and open/update the PR. Then run the project-adopted complete public-v2 pre-merge review against current source and those observations. If source publication is not authorized, complete local work and preserve the remote-dependent steps as pending; no plan gate requires nonexistent CI evidence.
- [ ] Obtain final merge authorization for the concrete PR/commit separately. Once the release stage is authorized and its checks pass, create an immutable tag and GitHub Release with archive/hash manifest/host evidence/limits/install instructions. Proposed first release is `v0.1.0`; select the actual version during execution.
- [ ] Verify a pinned installation from `codefoundry-io/codex-md-improver`, path `skills/codex-md-improver`, at the approved tag using the official skill installer with an explicit disposable `--dest` set to a temporary discovery repository's `.agents/skills`. Its current helper accepts `--repo`, `--path`, and `--ref`; resolve the installed helper rather than hardcoding a developer's home path.
- [ ] Compare source/tag/package/installed hashes; verify resource resolution and an explicit `$codex-md-improver` invocation in a fresh session on each supported host where available. Report discovery, static validation, recognition, behavior, and installed-byte equality separately.
- [ ] Start that installed-discovery session from the temporary repository outside the source checkout, assert the actual loaded installed path/hash and record hidden identity as unverified. A source-discovery symlink or manual source load is not installed exposure.
- [ ] For the owner's actual installation, identify the supported skill destination and its existing contents first. Apply only within the separately authorized installation scope; never blindly overwrite an existing same-name skill. Retain a task-owned recovery copy only when replacing existing bytes, and record its retention/cleanup decision.
- [ ] Publish reproducible GitHub/tag installation instructions and the release receipt. Direct repository installation is the initial distribution route; official marketplace publication or a multi-skill plugin is not claimed. If marketplace distribution is later requested, use the current official plugin format as a separate packaging extension. [Official installation and distribution guidance](https://learn.chatgpt.com/docs/build-skills).

## 7. Verification and execution handoff

Planning-time access check: the two existing known global/workspace AGENTS entrypoints and ten direct workspace policy references were readable (12 files). Three additional instruction candidates were absent; no access denial occurred in this limited sample. This is not a recursive reference-tree audit, a privacy-protected-folder check, or proof of GitHub write permission. Future scans must still use the accessible-area behavior above. No file contents from this check are included in the public package.

Run affected deterministic tests first, then the full suite once integration is ready: `python3 -m unittest discover -s tests -p 'test_*.py' -v`. Use the executing host's approved shell and interpreter. `quick_validate.py` needs its installed runtime dependencies; record tool resolution before running it. No Python or CI test was run against product code in this planning turn because that code does not exist.

The unit-test oracle covers path identity, chain selection, bytes, traversal state, candidate extraction, report schema, arithmetic, comparison, and package contents. Semantic classification and subjective scores remain review judgments. Fresh recognition results test only the presented cases. Canonical skill behavior tests and actual installed exposure require their own evidence.

Planning estimate after formal-review refinements: approximately 1,050–1,600 added production-code lines, zero expected deletions, net +1,050–1,600; 450–650 of those lines are novel core across the whole plan, including approximately 250–300 in Task 2. Separately estimate 750–1,100 test/fixture lines, 300–500 skill/reference instruction lines, 150–250 criteria/default metadata lines, 60–100 CI lines and 150–250 README/release documentation lines, all additions with zero planned deletions. Existing planning records are separate. Growth covers scenario-bound references, selected-criteria traceability, assessment input and pure probe evaluation; removing range-level rereading offsets complexity. The current workspace policy treats about 500 net/300 novel-core lines as guides, not an 800-line ceiling or an L-class approval system. Split when it improves independent review; update estimates from implementation evidence, not arbitrary quotas.

Recommended execution: subagent-driven tasks with the leader retaining interfaces, placement decisions, and owner questions. Tasks 1–2 establish the discovery/graph contract; Tasks 3–4 may proceed independently once their inputs are fixed; Task 5 depends on the analyzer/report and dedicated executor; Task 6 follows verified integration. Source, behavior validation, review, merge, public release, and local installation remain separate completion claims.

## 8. Decisions reserved for the owner or execution preflight

| Question | Proposed starting point | Boundary |
| --- | --- | --- |
| First release mutation mode | Report and concrete diffs; apply only an explicitly selected follow-up diff | `workflow` was left undecided |
| Audit target | AGENTS.md and reachable related files only | SKILL audit removed by the later owner instruction |
| Root set for a real audit | Codex home plus chosen project roots, enumerate every distinct nested chain | No silent entire-home scan |
| Extended I03 assessment | Map new evidence into the original six weights | No invented extra total or pass threshold |
| L-SCORE-DELTA aggregates | Retain requested BEFORE/AFTER counts/rates through an explicit structured-verdict contract | Denominator/missing/duplicate handling remain undecided; disposition-only replacement needs owner acceptance |
| Global/reference warning budgets | Show terminal-route sizes without fabricated utilization | 90% applies only to a known corresponding budget |
| Inaccessible branches | Record blocked frontiers and review accessible paths | No permission escalation or task-wide stop for a partial tree |
| Recognition model | Luna/low extraction probe, exact ID resolved at dispatch | History isolation is not proof of memory isolation |
| Public distribution | Public GitHub repository, tagged skill package, reproducible installer path | Official marketplace acceptance is not promised |
| License | MIT selected by the owner on 2026-10-03 | Retain required notices in the installed subtree |
| Dedicated skill executor | Create/verify an exact-SOT binding before behavioral RED/GREEN | Missing role blocks that test, not planning or static analysis |

There is no need to settle all 52 pending criteria to implement the selected scope. Keep them visible in the decision record and introduce one only if the owner chooses it or explicitly accepts a necessary new design decision. Do not use pending items as hidden release blockers.
