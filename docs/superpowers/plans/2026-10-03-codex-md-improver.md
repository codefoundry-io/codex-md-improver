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

Resolve root markers, fallback filenames, project trust, explicit session overrides, and the byte budget into a narrow `LoaderSettings` record **per independent hypothetical cwd/scenario**, with provenance. Apply relevant trusted project configuration from root to cwd; nearer settings override ancestor values, subject to field-specific loader behavior. **Root discovery markers exclude Project configuration layers** in the pinned loader; derive them from non-project layers and explicit non-project overrides. Read only relevant nonsecret settings; do not copy whole configuration files into reports. Unresolved trust or session overrides remain explicit uncertainty. If the active Desktop/session configuration is unavailable, report a stated default or supplied scenario, not a verified live-runtime result. This is a narrow settings resolver, not a full managed-policy/configuration emulator.

The default scan declares an `observed_plus_defaults` hypothetical scenario. Read relevant fields from `<codex-home>/config.toml`; apply supplied `non_project` values over that observed base, then eligible trusted project fields, then explicit session overrides. For root markers, omit the project step. Absent ordinary values use the stated pinned defaults; the hypothesis explicitly assumes no additional contribution from unseen system, profile, cloud or session layers. Record those unseen live layers as unattested provenance, not as unknown values that prevent this hypothetical calculation. Never label its computed results as actual live-runtime attestation. An unreadable/unparseable relevant config, unvalidatable required lookup, or explicitly supplied unknown fact remains unresolved; a default must not conceal such a failure. A missing optional config file is confirmed absence, unlike a denied file. The selected project limits inventory, not loader ancestor discovery: a cwd inside a selected subdirectory can have a marker root above it, whose applicable ancestor instruction files are included read-only in that scenario.

Supplied `trust` facts are entries at actual absolute lookup keys, overlaid on observed entries at the same keys before lookup. Use cwd first, then the validated Git/main-checkout fallback, with canonical then original spelling at each step. Thus one supplied or observed trusted repository-root entry can govern multiple subdirectory scenarios. A selected cwd entry with `unset` or `unknown` prevents fallback; no arbitrary ancestor-prefix inheritance is allowed. Provenance identifies the chosen key and whether its value was observed or supplied. An absent entry after a completely validated lookup is `unset` within this hypothesis; it does not prove the complete live configuration is unset.

Trust lookup is separate from loader marker discovery. Linked-worktree fallback requires the pinned Git metadata validation; unresolved required metadata leaves hypothetical trust unknown. Distinguish a confirmed `unset` level from `unknown`: `unset` is neither trusted nor untrusted, and does not trigger the project-loader's untrusted early return. Lack of live upstream attestation remains a separate provenance limit under the declared hypothesis above. [Trust lookup](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/config/src/project_trust.rs#L41-L95), [validated Git fallback](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/git-utils/src/trust.rs#L71-L223), [trust predicates](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/config/src/config_toml.rs#L596-L607).

By default inventory every accessible directory in each selected project. Collapse regions only when their ordered selected chains, effective relevant settings, trust and unresolved provenance match; a nested configuration file can create a region without a new AGENTS.md. Evaluate intermediate and sibling regions as well as leaf directories. `--cwd` explicitly narrows one selected project to that current-directory chain. Recognize nested Git repositories and worktree `.git` files as loader boundaries only when the effective non-project marker contract selects `.git`; inventory their existence separately. With no matching marker, use the pinned cwd-only fallback. Multiple simultaneous roots share a budget only when explicitly supplied as one ordered turn-environment group; independent project runs are not added together. Without a verified grouping, report separate scenarios.

Each explicit group uses one supplied `effective_loader_settings` record: budget, ordered fallback names, non-project root markers, active-project trust and field provenance for the controlling session. Apply this record to every member; do not merge member-local hypothetical settings or apply another implicit override pass. Preserve member-specific cwd/root discovery and the ordered shared budget. Unknown group fields leave dependent inclusion results unresolved; known untrusted gating or a known zero budget still proves zero project inclusion. Continue separately labeled independent scenarios under their own settings. [One Config and active-project gate per group](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs#L53-L85).

Region collapsing shares immutable loader records only. Preserve every inventoried member's scenario ID, cwd and scenario project root. Resolve references and enumerate terminal routes for every member, even when multiple members reach the same physical target; chain/settings equality never removes a cwd or its routes. Physical content is still read once.

Hypothetical project cwds exclude Git administrative directories (`.git` and identified Git storage), with that inventory boundary reported explicitly; they are not ordinary instruction scopes. Ignored and vendored directories remain included. Traverse in-scope directory aliases with ancestor-cycle detection; an alias target inside another explicitly selected `--project` is in scope. Otherwise an outside-root directory alias is an unresolved inventory frontier with partial coverage/exit 3, not authority to crawl another tree. An explicit read dependency into Git storage is separately a limited reference frontier. Do not apply a reference-exclusion exit code merely because a project's `.git` exists. Full per-scenario route output can scale as cwd count times route count; streaming and opt-in caps do not promise smaller total output.

`scenario_project_root` means the discovered loader marker root; with no marker it is that scenario's cwd. Keep the owner-selected inventory root in a separate field, especially when an ancestor marker lies above a selected subdirectory. Explicit base decisions can select a different absolute base when the guidance actually means one.

Conformance fixtures must pin the selected loader contract for overrides, fallback ordering, empty/whitespace files, read failures, decoding, and clipping. Do not guess an edge behavior from filenames alone. The CLI discovery model and GitHub changed-file review scope are labeled separately; this tool does not pretend to implement GitHub's review service. [Official discovery guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Model the pinned **project-directory** loader separately from scanner accessibility and global selection. Project selection precedes empty-content filtering: an empty override shadows ordinary AGENTS.md. A non-NotFound project read failure aborts that environment's modeled load; whether the caller omits it or fails depends on runtime context and may remain unknown. A readable-area lower bound is not automatically a lower bound on loaded context. Track retained raw source bytes and decoded content bytes separately: truncating UTF-8 before lossy decoding may increase decoded length. Preserve within-environment raw-byte accounting and outer simultaneous-environment decoded-byte accounting from the pinned source. Do not claim the scanner's permissions establish runtime permissions.

For an ordered simultaneous group, a propagated failure in a later member can fail the whole load, including earlier member text and the seeded global text. Keep calculated member/global bytes as conditional assembly evidence; do not report them as successfully delivered group context when the group fails. Unknown runtime permission context leaves delivery conditional even when hypothetical assembly bytes are computable. A fixture with a successful first member, nonempty global seed and a later propagated read error must distinguish their known candidate bytes from failed/unknown group delivery. [Pinned propagation](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs#L90-L103).

The pinned **global** provider tries override then ordinary AGENTS.md, skips missing/nonfiles, decodes the whole file lossily, trims it and selects the first nonempty result. Metadata/read failures warn and continue. If none succeeds and warnings exist, a refresh can retain the last good value; confirmed absence clears it. Model fresh observed selection and label hidden cached runtime content unknown instead of simulating a session history. Report original and trimmed decoded bytes separately. This provider has no byte cap and does not charge the project budget; that does not prove unlimited model context. [Pinned global provider](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/codex-home/src/instructions/mod.rs#L36-L102).

Analyzer home selection is explicit `--codex-home` (existing absolute directory), then nonempty `CODEX_HOME`, then the user's home plus `.codex`. Validate/canonicalize a nonempty environment override as an existing directory; the default path may be absent and is reported as absent. Blank environment values use the default. Record the selected origin without dumping environment variables. [Pinned home resolver](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/utils/home-dir/src/lib.rs#L12-L57).

Project selection probes joined candidate paths using filesystem metadata; do not emulate it by exact-case directory-name matching. Record the discovered alias and physical identity. Filter fallback names exactly as the pinned loader does for the modeled OS (empty, duplicate, `.`/`..` and forbidden path syntax), recording ignored entries. macOS/Ubuntu behavior follows the actual volume's case sensitivity, not an assumption based solely on the OS name.

Trust-key canonical spelling must match the pinned native normalizer, separately from content deduplication by physical identity. A bounded macOS case-insensitive-volume fixture found Python 3.12 `Path.resolve`/`os.path.realpath` retained a lowercase alias while native `realpath` returned stored mixed-case spelling. Python path resolution alone is therefore not the oracle for canonical-first trust lookup. Add distinct canonical/original trust entries to that native-host fixture and prove precedence; if canonical spelling cannot be established, mark the dependent lookup unresolved. This requires a conformant result, not a particular FFI implementation. [Pinned normalizer](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/utils/path-utils/src/lib.rs#L18-L21), [Rust Unix canonicalization](https://doc.rust-lang.org/std/fs/fn.canonicalize.html).

An untrusted active project contributes zero included project bytes while accessible original volume can still be audited; unknown trust leaves inclusion unknown unless another known gate, such as zero budget, proves zero. For a positive environment budget, metadata discovery precedes reading and probes all selected directory candidates (short-circuiting after the first file in each directory). Non-NotFound probe failures abort that environment. Later file reads stop at exhaustion, but their metadata may already have been probed. A zero initial budget or exhausted outer environment budget skips that environment's discovery and reading altogether.

Pin the loader's Unicode whitespace definition, not Python's broader default stripping: Rust uses `White_Space`; Python also uses bidi classes. Include U+001C–U+001F as non-whitespace loader content and ordinary Unicode space controls in conformance fixtures. [Rust definition](https://doc.rust-lang.org/std/primitive.char.html#method.is_whitespace), [Python definition](https://docs.python.org/3/library/stdtypes.html#str.isspace).

### 2.2 Reference graph

- Start with selected global/project instruction files and discovered instruction variants needed for scope analysis. Mark active versus shadowed variants. Do not seed or audit standalone SKILL files; a reachable SKILL.md is an `excluded_skill` boundary rather than an instruction to expand its contents.
- Find Markdown inline/reference-style links, table cells, backtick paths, plain-text file paths, and prose that instructs reading files or directories. Generalize C9 beyond a folder named `references`.
- Resolve absolute paths, `~`, and relative paths. Markdown links default to the referring document's directory; an explicit declared base takes precedence. Plain instruction paths may be document-relative, project-relative or cwd-relative: retain each distinct candidate and request a decision if context cannot establish one. Existence alone is not proof of the intended base.
- Resolve each occurrence in its `ChainReport` scenario. A declared base has kind `document_dir`, `scenario_project_root`, `scenario_cwd`, or `absolute` (with its path); do not freeze a scenario-relative meaning into one global absolute path. Bind semantic decisions to source hash/span and, when specific, scenario ID. One global instruction can therefore point to different project documents in two scenarios while its physical text is cached once.
- Separate URL fragments and `path:line` suffixes from the file identity. Support documented environment placeholders and finite globs without invoking a shell. Unknown variables, natural-language folder descriptions, and ambiguous expansions remain unresolved edges.
- Classify a path as a read dependency, informational example, output destination, or uncertain candidate before recursively following it. Report all recognized path candidates; do not treat output paths as instructions or execute sample commands.
- A linked directory is enumerated recursively. Keep aliases while deduplicating content by resolved identity; detect file and directory symlink cycles. Explicit linked absolute/tilde targets outside selected projects are included when readable under the existing process permissions and owner scope; this never authorizes unrelated home-directory crawling or bypassing a host deny rule. Missing, denied, changed-during-read, undecodable, binary, and special-file targets retain explicit statuses. Catch access errors per file/directory and continue siblings without privilege escalation or permission changes.
- During recursive enumeration, a directory containing SKILL.md is one `excluded_skill` frontier; do not enumerate its skill subtree. A separately explicit link from AGENTS guidance to a non-SKILL support file in that directory remains a related-file target, without authorizing a surrounding skill audit.
- Normal text is read and hashed once; binaries receive metadata and an explicit content-review limit. Do not read devices, sockets, or FIFOs. A technical exclusion such as explicitly referenced Git object storage appears as an excluded frontier with limited coverage, not a complete leaf. Do not exclude a readable linked folder merely because it contains generated reports or another tool's output. Apply the run-owned identity exclusion and late-overlap handling in Section 4 so generating reports cannot expand this audit recursively; do not require a completed traversal before creating the progress receipt. Any user-imposed resource cap produces `partial` when it stops required traversal, never an unqualified all-files result.
- The deterministic lexer cannot prove it found every natural-language reference. A semantic residual pass checks unmatched read instructions and ambiguous path spans; a remaining ambiguity prevents an exhaustive-coverage claim, but does not prevent review of the accessible resolved area.
- A resolution may introduce an occurrence the lexer missed, binding its source hash, span and exact span text plus classification/base/target. Validate it like an existing occurrence; a bounded rescan expands only the supplied branch. No fabricated lexer match is needed.
- Git administrative entries encountered implicitly while recursively reading a linked working directory are inventoried boundaries and do not alone make that traversal partial. An explicit read dependency into Git storage retains the limited-coverage rule; test both directories and submodule `.git` pointer files.
- URL references are inventoried, not automatically crawled. Fetch only sources needed to verify the selected factual claim, recording the URL and retrieval evidence.
- Cache physical content separately from reference occurrences: each occurrence retains its referring alias/base, source span and condition. A verified semantic decision may resolve one occurrence through an explicit resolution input and bounded rescan; unresolved alternatives are not both traversed automatically. The resolution must bind the source hash/span, and stale decisions are rejected visibly.
- A resolution may also decide occurrence classification: `read_dependency`, `informational`, `example`, `output`, or still `uncertain`. Bind it to the same source hash/span and optional scenario. A non-read decision stays inventoried but does not recurse or force partial coverage; a read decision with unresolved base remains partial. Reject stale decisions and contradictory non-read/target combinations. This closes semantic path-classification uncertainty without requiring an invented file target.
- Known credential, authentication and private-key sources are metadata-only `excluded_sensitive` frontiers, never model excerpts or report content. Test explicit aliases to `.aws/credentials`, `.codex/auth.json` and SSH private-key files before content reads, including resolved symlink identity. This is a bounded content boundary, not a generic secret detector or a claim that other text is secret-free. Do not emit credential values found incidentally in other evidence.
- Resolve the Codex authentication source as `<resolved-codex-home>/auth.json` as well as the default location, and apply the no-content boundary by physical identity. Do not hardcode only a directory named `.codex`.
- Enumerate the closed known-path set in `assets/defaults.json`: the above authentication/AWS/standard SSH private-key locations plus user-home `.netrc`, `.git-credentials`, `.pypirc`, `.npmrc` and `.config/gh/hosts.yml`. Check aliases before content reads. This configured set is not exhaustive secret detection; incidental-value non-disclosure remains a semantic/prompt obligation, not a deterministic guarantee.

Removing a link must account for incoming references, consumers of exact text, and load-bearing constraints. Prefer a narrower reading condition or a short retained rule when it preserves the original purpose. Removing the edge does not authorize deleting the linked file or its history.

#### Per-terminal path reporting

The filesystem and links are presented as a tree for reading, but the underlying structure can be a graph. Read and hash each physical text file once, then enumerate each distinct accessible root-to-terminal route. Use an ancestor set per route for cycle detection; a global visited set alone would incorrectly erase routes through shared files. Stream rows to disk so a large set of routes does not require retaining all expanded paths in memory.

Store shared immutable chain/node records plus streamed route records; report progress and write a usable partial receipt on interruption or an explicitly chosen resource cap. Route count can grow combinatorially even with few files. Do not promise bounded runtime/output from streaming and do not silently impose a fixed route/depth cap or replace full routes with samples. Markdown may summarize/link the complete route stream instead of duplicating it all in memory.

Expose optional `--max-routes <positive-int>` with no default cap. If it stops enumeration, return 3 with a partial receipt. Keep a run manifest marked incomplete from the start and flush committed route rows. Catchable SIGINT/SIGTERM handling makes a best-effort partial receipt and exit 3; SIGKILL or host loss cannot promise a final receipt/exit code. Their incomplete manifest and committed prefix remain explicitly incomplete. The skill retains the host process handle and permits long-running scans instead of assuming a short tool-yield timeout means completion.

Each `TerminalPathReport` contains its member scenario ID/cwd/project root, ordered global and project loader sources, originating instruction file, full reference route, edge reading conditions, terminal kind, terminal file size when known, and cumulative known unique original file bytes on that route. Keep `global_original_bytes`, `project_original_bytes`, `project_included_bytes`, and conditional reference-file bytes as separate columns. The combined route-original total is a file-volume measure, not proof of consumed context. Do not add a range-level rereading simulator or claim real tokens, message overhead or actual repeated tool reads.

An accessible leaf with no outgoing read dependencies is `leaf`; also emit `empty_directory`, `blocked_frontier`, `missing_target`, `unresolved`, `cycle`, and `excluded_skill` terminal rows. A denied directory is an unknown subtree, not an ordinary completed leaf; its number of hidden leaves is unknown. Unknown sizes are null, never zero. Known totals for incomplete routes are lower bounds, and readable content is distinguished from size-only metadata.

For example, a 1,000-byte AGENTS source that links a 200-byte shared guide, which links leaves of 300 and 400 bytes, produces route totals of 1,500 and 1,600 bytes. The unique graph total is 1,900 bytes; adding the route totals would double-count shared content. A second route to the same leaf remains a separate row while its physical content is read once. Where a reference repeats an already loaded AGENTS source, do not add that file again to the route's unique context total.

The owner-defined original-volume warning compares `project_original_bytes` with `project_doc_max_bytes`; actual loader effects come from per-file conformance modeling. A large conditional reference-route total is reading burden, not loader overflow. No reference-context cap is invented. The terminal report and both before/after comparisons cover every accessible route, not just the deepest directory or largest leaf.

For each directory-read dependency also report known unique descendant text bytes, file count, read conditions and unresolved frontiers. For example, 200 distinct 5 KiB files yield a 1,000 KiB directory subtotal alongside all 200 routes. A scenario total includes shared AGENTS prefixes once. This aggregate measures file volume, not actual reads or tokens.

### 2.3 Heuristics, assessment, and comparison

Implement only the selected lint branches: six C8 body checks, C6, both C4 checks, C10, C9 reference TOC, C3, and AA1/AA2/AA3/AA5/AA6. Use explicit criterion allowlists; do not execute the existing lint script wholesale because it also enables pending checks. Its code may be studied as behavior evidence; any code reuse requires license/provenance verification before public redistribution.

Each candidate includes its rule ID, document kind, evidence span or aggregate, detector parameters, and applicable exception. English phrase and non-Latin heuristics must disclose language limits. A Korean audience does not make Korean text an error. Version/model candidates preserve exact command identifiers and legitimate runtime dates. Hard factual failures, heuristic hits, semantic findings, unresolved decisions, and read errors are separate classes.

Classify readable targets as AGENTS guidance, linked instruction text, Markdown reference, or code/config evidence. Review prose rules only where the content is guidance; reading a code file to verify a command does not make that code a prompt to rewrite. The reference TOC candidate applies to Markdown reference text, not arbitrary source files. SKILL-only criteria have no user-target application after the scope correction; applicable ideas such as recognizable conditional reads remain covered by AG10/C9. Required structure of the newly created improver skill is a separate package concern.

Extract outgoing references from AGENTS guidance, linked instruction text and Markdown reference text. Code/config evidence is a leaf unless an explicit source-bound resolution supplies a read dependency; ordinary code string paths are not implicit instructions to traverse. Binary/special-file limits remain unchanged.

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

Comparable scope means the same requested roots, cwd narrowing, Codex-home selection and supplied settings/group inputs, with coverage compared separately. It does not require identical discovered regions, chains or source hashes. A migration creating a nested AGENTS.md remains comparable under the same request; changed observed configuration and region membership are reported as deltas, with affected metrics labeled when their effective budgets differ.

Finding identity includes rule ID, source alias and a stable evidence anchor rather than line offsets alone; ambiguous matches stay unresolved. For rewritten/deleted anchors, an after-assessment may carry `resolves` records naming the exact before-report hash/finding ID and source-bound after evidence plus a reason. `report` validates their shape and after bindings but labels the before reference pending validation. `compare` validates those references against its actual before input before classifying resolution; a mismatch is an input error. Disappearance without a verified resolution remains unresolved. No additional history store is needed.

The owner adopted the L-SCORE-DELTA aggregate contract on 2026-10-03: accept one PASS/FAIL/NA verdict per rule ID per audit and reject duplicates. Applicable is PASS+FAIL; pass-rate is PASS/applicable, undefined when applicable is zero. Show NA and missing/unassessed verdicts separately. Report FAIL-to-PASS transitions only for comparable reports with explicit verdicts on both sides. A missing verdict never implies PASS. This records the selected structured contract, without adopting the legacy parser or the other pending criteria.

Task 4 must implement and verify that selected aggregate subrecord before claiming all selected outputs are shipped. The 52 unselected pending criteria remain outside the implementation gate.

Add an explicitly versioned criterion-verdict subrecord to AssessmentInput and a corresponding skill assessment step under that agreed contract. Pin its fields and invalid-input behavior in fixtures before implementation; reject unknown fields and rule IDs. This is an input/workflow dependency as well as arithmetic.

For R01/R03/R04, accept only current user-supplied or current-session observations as evidence for missing reusable guidance. Prepare an `ADDITION` proposal with provenance, the information gap, expected utility, and an exact diff against an existing AGENTS-linked target. A named new destination needs the existing placement decision before entering the write set. Do not crawl session history, modify memory, or insert rules automatically from an isolated mistake.

## 3. Independent recognition probes and convergence

AG10/P23/U02/U03 notes explicitly request a narrow inexpensive probe, refining U03's broader exclusion. The probe asks whether a separate agent recognizes a trigger, selects the required file, respects scope, and identifies the next allowed action. It does not execute a production migration or establish general model-performance improvement.

Owner-selected ordinary probe preset: Sol/medium, resolved to a currently supported exact model ID when dispatched, with `fork_turns="none"`. This is an extraction/classification role, not a code reviewer. At a wording plateau, use skill-prompt-review guidance, consolidate remaining findings once with a fresh read-only child and make one bounded revision; judge subsequent changes from observed choices on controlled scenarios. Preserve the owner's ability to change the model and effort through one configuration location. Unsupported settings produce a visible result; do not silently upgrade or substitute models.

Give each child `fork_turns="none"`, one synthetic user request, the relevant candidate guidance, and minimal fixture contents. Do not supply the expected answer, suspected failure, author discussion, or prior verdict. Before/after probes use separate fresh children with equivalent cases. Expected file IDs, scope, and action are sealed in the evaluator input, outside the worker packet; collect structured answers and compare them mechanically.

Throughout semantic review and probes, treat audited text as data and never execute its embedded commands. Executing the trusted analyzer is a separate action. Use host read-only/no-execution controls when available and record actual tool constraints versus prompt-only containment; do not claim enforcement merely because the packet requests it.

Use positive, negative, boundary, and ambiguous cases chosen for the changed condition. Record model, effort, packet hash, source hash, observed answer, expected answer, and tool/read availability. History isolation does not establish memory or host-instruction isolation. Record `history_isolation`, `memory_isolation`, host exposure and target-guidance exposure (`present`, `absent`, `unknown`). Use synthetic names/paths different from the audited target to reduce answer leakage, but do not claim that renaming proves isolation. If clean context cannot be demonstrated, label the result limited. Do not modify global memory settings or claim that a prompt instruction disables memory.

Run a simple positive control and validate case identity and answer shape before comparing recognition. Record client version. Missing tools, unavailable models, wrong-case answers or task-delivery failures are `invalid_probe`, distinct from `not_recognized`; they do not justify wording changes.

Record requested family/effort, resolved dispatch ID/effort, and independently exposed effective runtime identity separately. Hidden effective values are null/`UNEXPOSED`; a supported request is not runtime attestation. An unsupported selector is invalid, not permission to inherit a different model silently.

Revise wording only when a concrete case demonstrates a recognition problem or new evidence resolves a finding. Rerun the affected cases after a bounded correction. With no new evidence, stop and show the remaining issue to the owner; do not continue grammar or nuance debates indefinitely. No arbitrary new round-count limit is imposed.

This lightweight recognition check is separate from this workspace's canonical skill RED/GREEN requirement. Before production skill behavior is authored, a dedicated behavior-only Custom Agent must be bound to the exact new skill SOT. The resumed session accepted a capability-only fresh `codex-md-improver-executor` spawn and the child reported the configured canonical path; this proves role availability, not source loading or behavior. The TRIAD-specific executor cannot substitute. Under the managed-workspace policy this prerequisite also covers bundled script behavior from Task 1 onward; Task 5 adds entrypoint behavior scenarios. Static preparation can continue, but leader-run tests do not replace the required fresh RED/GREEN sequence or authorize affected production edits.

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

Generated run files live under an explicit new output directory outside selected project roots and linked input directories by default, such as a user-chosen report folder containing `.codex-md-improver-runs/<run-id>/`. The skill first uses a task-owned unique path under an available, host-permitted temporary directory, reports that location and its volatility, and offers a named durable destination when retention is required. If no eligible write location is available, request only an output-location decision or report exit 2; do not escalate target-read permissions. A deliberate output-inside-target choice requires `--allow-output-in-target` and is recorded; existing input files remain read-only. Reject an output path that already exists or aliases an explicit input, even with that flag.

Validate against known roots before exclusive output creation, then register the run directory's physical identity and exclude only those newly owned outputs from all later traversal. If a later discovered linked input directory contains the output and opt-in is absent, finish an invalid-output-location receipt and exit 2; preserve that run's receipt without treating it as audited input. With opt-in, record the owned-output exclusion and continue. A direct input alias to a run-owned output still refuses. Prior reports remain ordinary eligible inputs; this is not a blanket report-directory exclusion. The run owns `audit.json`, `audit.md`, the route stream, optional proposal patch and a manifest of created paths. Recognition fixtures use one run-owned temporary root. Retain requested reports/proposals/evidence; remove only this run's disposable fixtures. Never recursively clean a caller directory or delete referenced research as a side effect of pruning a link.

Public commits use an explicit allowlist. Exclude actual audited documents, personal absolute paths, raw owner attachments, configuration dumps, provider logs, probe transcripts from real work, installed caches, and local executor definitions. The requirements ledger contains verbatim owner text and must receive an explicit public-allowlist decision; it is not already sanitized by being planning material. Before public CI, either approve its inclusion or approve an independently derived included-ID fixture, with ledger-hash provenance, for the coverage test. The owner selected MIT on 2026-10-03. Verify any borrowed-code rights separately; required notices must be inside the installed skill subtree or have an explicit tested installation mapping.

## 5. Data interfaces

Use typed records in the module that owns them; do not add an otherwise unnecessary shared framework.

| Interface | Owner and minimum contract |
| --- | --- |
| `LoaderSettings` | `discovery.py`: cwd/scenario, limit, fallback names, root markers, trust facts, client/version, provenance, unresolved overrides; hashable region identity |
| `ScopeRequest` | `discovery.py`: Codex home, selected project roots/cwds, optional simultaneous-environment groups; no standalone skill target |
| `ChainReport` | `discovery.py`: shared loader/settings record plus every member scenario ID/cwd/project root, ordered sources, original/retained raw/decoded project bytes, separate original/trimmed global bytes, clipping/omissions, modeled loader outcomes, warning state, uncertainty |
| `ReferenceGraph` | `references.py`: cached physical nodes/aliases/read states; scenario-bound edge occurrences with source hashes/spans/base kinds, resolved bases, alternatives, conditions, directory aggregates, completeness limits |
| `TerminalPathReport` | `references.py`: member scenario ID/cwd/project root, loader sources, complete reference route, terminal kind, known component/total bytes, exclusions, size/content status, lower-bound flag |
| `Candidate` | `lint_candidates.py`: rule ID, path, kind, evidence spans or aggregate, explanation, parameters, exceptions |
| `AuditReport` | `reporting.py`: schema version, run scope/fingerprints, chains, graph summary, findings, subjective assessments, pending owner decisions, completeness |
| `AuditDelta` | `reporting.py`: comparable scope, matched findings and dispositions, byte/reference changes, incomparable or unresolved cases |
| `AssessmentInput` | `reporting.py`: version, audit SHA-256, source-hash bindings, semantic findings, dimension assessments, local dispositions, cross-run resolves declarations, owner-decision records and proposals, each labeled with its source/provenance |

Proposed CLI: `python3 <loaded-skill-directory>/scripts/md_improver.py scan --project <absolute-root> [--project <absolute-root> ...] [--cwd <absolute-directory>] [--codex-home <path>] [--settings <narrow-settings.json>] [--resolutions <verified-decisions.json>] [--max-routes <positive-int>] [--allow-output-in-target] --out <new-run-directory>`; `compare --before <audit.json> --after <audit.json> --out <new-run-directory>`. `--cwd` requires exactly one selected project and must belong to it; omitted means whole-project coverage. There is no `--skill` audit option. Check Python >=3.11 before imports requiring that version and provide a clear setup error; do not implement a replacement TOML parser.

Add `report --audit <audit.json> --assessment <assessment.json> --out <new-run-directory>` to ingest the skill's judgments into a **new** enriched report; never hand-edit scanner output or overwrite the original run. `AssessmentInput` version 1 binds the input audit hash and every cited source hash/span. It carries semantic finding IDs/rules/evidence, six optional dimension scores with evidence, explicit local dispositions, cross-run resolves declarations, owner-decision provenance and proposal records. Unknown local IDs, wrong types, invalid score ranges, stale hashes or local dispositions without an identified finding are rejected; cross-run IDs follow the explicit compare-time validation above. Model judgment and recorded owner decisions remain distinct; file/schema validity does not authenticate consent. Only the skill/leader records actual owner decisions. `compare` consumes these enriched reports and treats missing assessment as unassessed, not PASS or resolution. No Markdown-score parser is introduced. The versioned aggregate-verdict subrecord follows the owner-adopted single-verdict contract above.

`--settings` accepts a narrow version-1 object: `client` (name/version), `non_project` (budget, ordered fallback names, ordered root markers), `trust` (absolute lookup key to trusted/untrusted/unset/unknown, using Section 2.1 precedence), `session_overrides` (budget/fallback names/root markers), `environment_groups` (unique ID, ordered explicitly selected cwds, one `effective_loader_settings` record as defined above) and `declared_bases` (source alias to a base-kind record as defined above). Missing ordinary values use disclosed defaults under `observed_plus_defaults`; unreadable/unvalidatable required inputs or explicit unknowns remain unresolved. Missing or explicitly unknown group-effective fields remain unknown, with no member-setting/default inheritance. Unknown keys and invalid types are input errors. Each group member must lie in a selected root, cannot appear twice or belong to two groups, and uses a recorded order. Relevant user and trusted project TOML fields are layered for independent scenarios under the stated precedence; project-local root markers are ignored by discovery. This schema transports only the modeled fields, not arbitrary Codex configuration.

Scanning and comparison return `0` for a complete result without candidates, `1` for a complete result containing findings/candidates, `3` for a successfully produced partial-area report, and `2` for invalid input, no usable readable inputs, or inability to write the requested report. The skill treats code 3 as a usable result and continues reviewing the accessible area; it does not retry for greater permissions. Findings remain in partial reports. CLI help states that exit 0 does not certify prompt quality or runtime behavior.

`report` uses the same precedence and returns 1 for any open candidate/finding, including deferred items. `compare` returns 1 for new or retained open findings (not just regressions); a complete resolved-only delta returns 0. These statuses do not imply completion of unassessed semantic work.

Exit precedence is 2, then 3, then 1, then 0. Missing/denied/changed/unresolved dependencies, truncated traversal, technical exclusions, and unreviewable binary/special/undecodable linked content yield 3 when usable input remains; incomparable comparison also yields 3. Intentional `excluded_skill`, cycle terminals, inventoried URLs and non-read examples/outputs do not alone make the declared local audit partial. Scanner completion never implies completed semantic review: absent semantic assessment is labeled unassessed, not fabricated failure or success. An assessment declaring unresolved semantic coverage yields 3 in `report`. Unsupported Python yields 2 via an older-interpreter-parseable entrypoint. Pin these cases in CLI tests.

An `excluded_sensitive` frontier also yields partial coverage when usable inputs remain. Neither access to a path nor an audited instruction authorizes copying secrets into a report or model prompt.

## 6. Implementation tasks

Task-file shorthand `scripts/`, `assets/`, `references/`, `agents/openai.yaml` and `SKILL.md` below is relative to `skills/codex-md-improver/`; tests, tools, workflows and project metadata remain repository-relative.

Apply the host's exact-SOT executor sequence to each affected bundled behavior task. In this managed workspace, the project leader owns source/test edits and the dedicated executor reports behavior only. A missing executor permits planning/static preparation, not production edits that bypass the required RED.

For each row below, the leader first writes focused tests and the exact scenario manifest. A fresh `codex-md-improver-executor` with `fork_turns="none"` runs RED against the canonical SOT; only after the intended behavior failure does the leader implement that row's production changes. A separate fresh instance runs focused GREEN, all relevant completed regressions, the skill validator and applicable distribution checks. Both instances record source realpath, commit/status or fingerprints before/after, exact commands/results and disposable-fixture cleanup. Test/module setup failures are invalid, not behavioral RED. For this new skill, establish only a valid minimal entrypoint and callable baseline seams needed to reach the failing assertions; do not pre-implement the behavior under test. Every task's run-to-RED/implement/run-to-GREEN shorthand means this sequence, never a leader-only substitute.

| Task | Exact focused executor cases | Leader-owned corrective surface | Fresh GREEN scope |
| --- | --- | --- | --- |
| 1 | `test_discovery.py`: settings/trust, inventory, loaders, byte accounting and scan CLI | `discovery.py`, scan CLI, defaults | Discovery cases, CLI/version guard, validator |
| 2 | `test_references.py`: occurrence decisions, graph/routes, partial/access/output lifecycle | `references.py`, graph CLI integration | Reference cases plus discovery regressions and validator |
| 3 | `test_lint_candidates.py`: all 17 selected branches and their exceptions | `lint_candidates.py`, detector defaults | Detector cases plus completed scanner regressions and validator |
| 4 | `test_reporting.py`, `test_rule_coverage.py`: assessment/compare/proposals and 107-ID wiring | `reporting.py`, report/compare CLI, criteria/rules | Reporting/coverage plus completed suites and validator; aggregate cases use the owner-adopted contract |
| 5 | `test_recognition.py` and bounded entrypoint scenarios: valid controls, scope, audited command as data, output location | `recognition.py`, SKILL.md, probe/rule references and metadata | Pure evaluator, fresh entrypoint behavior, all completed regressions and validator |
| 6 | `test_distribution.py`: allowlist, escaping links, notices and installed resource resolution | Package tool, release/distribution instructions | Distribution and complete deterministic suite, validator; actual installed discovery/OS CI remain separate receipts |

### Task 1: Establish the repository and instruction-chain analyzer

**Files:** project metadata, `assets/defaults.json`, `scripts/discovery.py`, `scripts/md_improver.py`, `tests/test_discovery.py`, initial CI workflow. The project AGENTS.md is newly authored; do not invoke the excluded `/init` maintenance workflow.

**Interfaces:** `resolve_settings(request: ScopeRequest, cwd: Path) -> LoaderSettings`; `discover_chains(request: ScopeRequest) -> list[ChainReport]` resolves settings for each candidate region and shares proven-identical prefixes.

- [x] Established planning-only Git history on `main` and branch `codex/initial-skill`; created project AGENTS.md. Before future staging, recheck this Git root and preserve parent dirty changes. No remote was created.
- [ ] Write failing synthetic tests: `test_override_and_fallback_selection`, `test_sibling_regions_not_combined`, `test_git_worktree_and_nested_root`, `test_unknown_effective_settings_are_labeled`, and `test_simultaneous_group_budget`.
- [ ] Add `test_identical_chain_different_config_region` (20,000 bytes with 32,768 versus 16,384 budgets), untrusted/unknown nested settings, explicit session overrides, and `test_cwd_narrowing_is_explicit`. Assert default traversal retains every configuration/instruction region.
- [ ] Test an explicit environment group with conflicting member-local budgets/fallbacks, proving that its one supplied effective record controls every member. Test unresolved group fields, group-wide untrusted gating, known-untrusted with unknown budget and zero-budget with unknown trust; keep independent scenarios separate.
- [ ] Pin trust lookup independently of loader markers: cwd before validated Git/main root, canonical/original spellings, a cwd entry with unset or unknown trust, nested repo under trusted parent, custom markers and a linked worktree. Run observed and supplied root-key entries through multiple subdirectories without ancestor-prefix inheritance; keep unverifiable required fallback unknown.
- [ ] Add `test_default_cli_observed_trusted_root_subdirectories`: without `--settings`, one trusted repo-root entry in the selected Codex-home config governs at least two inventoried subdirectories; a 32,769-byte non-whitespace root AGENTS source clips at the default 32,768 budget for each. Assert computed hypothesis bytes, selected trust key and disclosed unseen live layers without a live-attestation claim. Add denied/malformed config and explicit-unknown controls that do remain unresolved.
- [ ] Assert project-local root markers do not change discovery; a non-project marker override excluding `.git` changes the boundary; no matching marker selects only the cwd. Test settings JSON and group/base transport through the CLI, not only function calls.
- [ ] Test the hypothetical-cwd inventory boundary independently from the reference graph: Git administration is not a member cwd or automatic partial-reference cause; ignored/vendored directories remain members; alias cycles and outside-scope aliases are visible.
- [ ] Through the CLI, assert an unresolved inventory alias yields partial/3; selecting its target as another project supplies scope without authorizing unrelated descendants outside that scope.
- [ ] Test relevant Codex-home TOML fields and supplied settings/session precedence, unseen live-layer provenance versus unknown required hypothesis inputs, and selected-subdirectory scope with an applicable ancestor marker root and AGENTS file above the selected inventory root.
- [ ] Pin the current official loader edge behavior in fixtures before implementing empty/whitespace files, trust, unreadable files, UTF-8 clipping, and zero budget. Record which behavior remains unverified for Desktop.
- [ ] Assert empty override shadows the ordinary file, environment read failure does not report the readable remainder as actually included, and partial multibyte clipping distinguishes raw retained and decoded lengths both within a chain and between ordered simultaneous environments.
- [ ] Add `test_later_group_failure_conditions_earlier_and_global_delivery`: preserve computable first-member/global candidate bytes, propagate a later member's modeled error to whole-group failure, and leave actual delivery conditional when runtime permissions are unknown. Include explicitly unknown group-effective fields to prove they never acquire the independent-scenario defaults.
- [ ] Assert U+001C–U+001F remain loader content, while Unicode White_Space-only decoded prefixes are omitted; do not use bare Python `strip()` as the conformance oracle.
- [ ] Add distinct global fixtures: empty/whitespace override falls through; invalid UTF-8 decodes lossily; read/metadata error continues to a healthy lower candidate; all-failed refresh has unknown hidden cached content; confirmed absence clears selection. Test explicit/env/default home resolution, trim-versus-original bytes and a global file larger than the project budget without inventing a global cap.
- [ ] Test joined-path selection on the actual case-sensitive/case-insensitive host volume and exact fallback filtering, including ignored duplicates and invalid path syntax. Record the measured filesystem property for each OS result.
- [ ] Add a native canonical-spelling conformance fixture with a mixed-case directory, differently cased cwd alias and conflicting canonical/original trust entries. Confirm canonical-first lookup without conflating alias text and physical identity; record unavailable native evidence as a limit, never a fabricated pass.
- [ ] Test untrusted project included bytes equal zero and unknown trust yields unknown inclusion. Distinguish a later metadata failure (discovery still aborts with positive initial budget) from a later read failure skipped after exhaustion; zero budget and exhausted later environments never discover/read project files.
- [ ] Add assertions for non-whitespace fixtures: 29,491 project bytes is below warning; 29,492 warns; 32,768 warns without excess; 32,769 has raw-volume excess and actual clipping. A 40,000-space ancestor plus a 100-byte child retains the physical warning while including all child content and charging only 100 bytes. Changing global bytes must not change project utilization. A nondefault budget changes the boundary.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_discovery.py' -v`; observe the intended failure, implement the two interfaces and CLI input contract, rerun to pass.
- [ ] Commit only this repository's named files after verification. Establish macOS/Ubuntu CI with Python 3.11 and 3.12 jobs; local macOS evidence is separate from remote jobs, which cannot run until remote publication is authorized. Test the pre-import version guard, including an older-interpreter-parseable entrypoint.
- [ ] Add a separate Ubuntu Python 3.10 setup-guard smoke job: actual older interpreter invocation must return 2 with the setup message before unsupported imports. This does not claim Python 3.10 support.
- [ ] Parse the standalone guarded entrypoint with Python's `ast.parse(feature_version=(3, 9))` and keep pre-guard operations compatible; this supplements the real 3.10 smoke without claiming the user's bundled macOS interpreter version.

### Task 2: Traverse references and measure reading burden

**Files:** `scripts/references.py`, graph integration in `scripts/md_improver.py`, `tests/test_references.py`, synthetic fixtures.

**Interfaces:** `build_reference_graph(chains: list[ChainReport], declared_bases: dict[Path, dict], resolutions: list[dict]) -> ReferenceGraph`; `iter_terminal_paths(graph: ReferenceGraph, chain: ChainReport) -> Iterator[TerminalPathReport]`; `summarize_reading_paths(graph: ReferenceGraph) -> dict`. Each chain supplies member cwds, inventory root, scenario loader root/cwd and selected/scope-analysis source paths. Resolution records bind source hash/span and optional scenario restriction, with a classification decision and/or chosen base kind/target. They do not grant new access rights.

- [ ] Write failing tests for inline/reference-style links, table/backtick/plain paths, absolute/relative/tilde paths, declared bases, spaces/Korean names, `path:line`, fragments, variables/globs, and file-versus-folder reads.
- [ ] Assert ambiguous bases stay unresolved even when one file exists; output/example paths do not become unconditional read dependencies; referenced Markdown links do not increase the Codex project-loader budget.
- [ ] Assert two aliases of one physical file preserve different relative-reference meanings while reading content once; verified occurrence resolution expands only that branch and rejects a stale source hash.
- [ ] Assert one global source with a scenario-project-root reference resolves to a 10 KiB file in project A and a 50 KiB file in project B, with separate routes/totals and one physical source read. An unresolved base is never guessed from existence.
- [ ] Assert same-project sibling cwds with identical loader/settings records retain distinct scenario_cwd routes and totals, and also retain two scenario rows when both reach one physical target. Include a plain path whose cwd candidate differs from document/project candidates.
- [ ] Through the CLI, resolve an uncertain occurrence as informational/output, retain its inventory record and change partial exit 3 to complete 0/1; reject a stale dismissal. Test scenario_project_root at an ancestor marker above the selected subdirectory and at cwd when no marker exists.
- [ ] Add a source-bound occurrence missed by the lexer and expand exactly its declared branch; reject stale span text/hash. Test code/config evidence containing path strings stays a leaf unless an explicit read-dependency resolution adds an edge.
- [ ] Test linked working-directory and submodule recursion: implicit `.git` administrative entries are reported boundaries without partial status, while explicitly referenced storage remains limited coverage.
- [ ] Assert recursive directory coverage, duplicate aliases, cyclic symlinks, missing/denied targets, non-UTF text, binary/special-file statuses, and a file changing during read. A resource-capped scan must remain partial. A SKILL.md edge terminates as excluded and its contents are not quality-audited.
- [ ] Assert a folder read stops at a SKILL.md-containing directory, while an explicit AGENTS link to one non-SKILL support file there includes that file without scanning its surrounding skill.
- [ ] Assert explicitly linked generated documents are traversed, technical exclusions produce visible limited-coverage frontiers, and writing this run's results cannot add new scan inputs.
- [ ] Add `test_each_terminal_path_has_its_own_total`, `test_shared_leaf_keeps_both_routes`, `test_loaded_source_is_not_double_counted`, and `test_denied_subtree_preserves_readable_sibling_report`. Pin the 1,500/1,600 route totals and 1,900 unique-graph total above; assert unknown leaves/bytes remain null and denied paths never invoke an elevation or chmod operation. Inject PermissionError rather than relying on host/root-specific chmod behavior.
- [ ] Assert partial access produces a usable report with exit 3, per-terminal coverage, and retained findings. If no input can be read, produce the coverage/error receipt without claiming any content review.
- [ ] Assert a 200-file directory has a unique descendant subtotal alongside all routes, and that interruption/resource limits retain a partial receipt and already streamed rows without reporting exhaustive coverage.
- [ ] Drive `--max-routes` through the CLI; exercise a catchable interrupt and a terminated-process incomplete manifest separately. Test known credential aliases and symlinks as metadata-only frontiers with no content read or excerpt while ordinary related files remain reviewable.
- [ ] Test authentication exclusion with a nondefault Codex home, and late output/input-directory overlap with and without explicit opt-in; own output never becomes input while earlier reports remain traversed.
- [ ] Test each configured known-sensitive path and a physical alias before content reads; do not claim these checks detect arbitrary secret values in ordinary files.
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
- [x] Resolve the L-SCORE-DELTA aggregate-output decision: owner adopted the recommended contract on 2026-10-03.
- [ ] Pin the agreed applicable/PASS/FAIL/NA/unassessed/pass-rate and transition semantics in structured fixtures; do not assume pending legacy parser behavior.
- [ ] Write failing tests that disappearance in a partial/uncovered area cannot resolve a previous finding, a moved span does not create a false fix, changed scope is incomparable, and owner-deferred items remain visible. A verified resolution with complete affected evidence may succeed despite an unrelated denied branch; the overall report remains partial.
- [ ] Assert that an unchanged requested scope remains comparable after adding/removing a nested AGENTS.md or changing observed config regions; report those changes and affected budget metrics rather than confusing them with a new requested scope.
- [ ] Add a successful rewritten-span resolution bound to the before-report hash/finding ID and after source evidence; reject wrong baseline IDs/hashes and keep unacknowledged disappearance unresolved. Test ambiguous anchors rather than guessing matches.
- [ ] Define proposal records with source spans/hashes, destination, reason, replacement text, affected references, expected byte/reading changes, and required owner decisions. A destination outside the linked migration set stays pending until explicitly accepted.
- [ ] Consolidate selected rules into conditional semantic groups: placement/chain scope, reference burden, durable facts, wording/duplication, verified environment, and actionable proposals. Keep the full decision ledger outside the runtime prompt.
- [ ] Implement the criteria-map metadata and exact 107-ID/17-detector coverage checks. Test source-bound R01/R03/R04 observation ADDITION proposals, including utility, concrete diff, current supplied-session provenance and named-destination decision. Semantic merit remains owner-reviewed.
- [ ] Derive expected included IDs from the checked-in owner ledger's Included table, independently of criteria.json. Tag non-detector criteria beside their shipped conditional rules and verify each tag/group target exists; this detects missing rule wiring without certifying semantic quality.
- [ ] Resolve the ledger's public allowlist before CI publication. If excluded, use the explicitly approved independently derived ID fixture with ledger-hash provenance; do not derive expected IDs from the implementation metadata itself.
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
- [ ] Cover choosing a host-permitted output location outside the synthetic target, reporting temporary retention limits and handling unavailable output permission without broadening target reads.
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
- [ ] Before release, verify the owner's selected aggregate-output choice is recorded and implemented, or the exact reduced contract was accepted. Preserve the dedicated behavior sequence and other required verification as separate preconditions.
- [ ] Verify a pinned installation from `codefoundry-io/codex-md-improver`, path `skills/codex-md-improver`, at the approved tag using the official skill installer with an explicit disposable `--dest` set to a temporary discovery repository's `.agents/skills`. Its current helper accepts `--repo`, `--path`, and `--ref`; resolve the installed helper rather than hardcoding a developer's home path.
- [ ] Compare source/tag/package/installed hashes; verify resource resolution and an explicit `$codex-md-improver` invocation in a fresh session on each supported host where available. Report discovery, static validation, recognition, behavior, and installed-byte equality separately.
- [ ] Start that installed-discovery session from the temporary repository outside the source checkout, assert the actual loaded installed path/hash and record hidden identity as unverified. A source-discovery symlink or manual source load is not installed exposure.
- [ ] For the owner's actual installation, identify the supported skill destination and its existing contents first. Apply only within the separately authorized installation scope; never blindly overwrite an existing same-name skill. Retain a task-owned recovery copy only when replacing existing bytes, and record its retention/cleanup decision.
- [ ] Publish reproducible GitHub/tag installation instructions and the release receipt. Direct repository installation is the initial distribution route; official marketplace publication or a multi-skill plugin is not claimed. If marketplace distribution is later requested, use the current official plugin format as a separate packaging extension. [Official installation and distribution guidance](https://learn.chatgpt.com/docs/build-skills).

## 7. Verification and execution handoff

Planning-time access check: the two existing known global/workspace AGENTS entrypoints and ten direct workspace policy references were readable (12 files). Three additional instruction candidates were absent; no access denial occurred in this limited sample. This is not a recursive reference-tree audit, a privacy-protected-folder check, or proof of GitHub write permission. Future scans must still use the accessible-area behavior above. No file contents from this check are included in the public package.

Run affected deterministic tests first, then the full suite once integration is ready: `python3 -m unittest discover -s tests -p 'test_*.py' -v`. Use the executing host's approved shell and interpreter. `quick_validate.py` needs its installed runtime dependencies; record tool resolution before running it. No Python or CI test was run against product code in this planning turn because that code does not exist.

The unit-test oracle covers path identity, chain selection, bytes, traversal state, candidate extraction, report schema, arithmetic, comparison, and package contents. Semantic classification and subjective scores remain review judgments. Fresh recognition results test only the presented cases. Canonical skill behavior tests and actual installed exposure require their own evidence.

Planning estimate after formal-review refinements: approximately 1,100–1,700 added production-code lines, zero expected deletions, net +1,100–1,700; 500–700 of those lines are novel core across the whole plan, including approximately 250–350 in Task 2. Separately estimate 900–1,250 test/fixture lines, 300–500 skill/reference instruction lines, 150–250 criteria/default metadata lines, 60–100 CI lines and 150–250 README/release documentation lines, all additions with zero planned deletions. Existing planning records are separate. Growth covers scenario-bound/classified references, selected-criteria traceability, assessment input, output lifecycle and pure probe evaluation; removing range-level rereading offsets complexity. The current workspace policy treats about 500 net/300 novel-core lines as guides, not an 800-line ceiling or an L-class approval system. Split when it improves independent review; update estimates from implementation evidence, not arbitrary quotas.

Recommended execution: subagent-driven tasks with the leader retaining interfaces, placement decisions, and owner questions. Tasks 1–2 establish the discovery/graph contract; Tasks 3–4 may proceed independently once their inputs are fixed; Task 5 depends on the analyzer/report and dedicated executor; Task 6 follows verified integration. Source, behavior validation, review, merge, public release, and local installation remain separate completion claims.

Implementation size update (local Tasks 1–6, before remote publication): 2,060
production Python lines across seven files, approximately 800–1,000 novel core
lines. Relative to the admitted plan's no-code baseline this is +2,060 additions,
zero deletions, net +2,060. Separately: 2,630 test/fixture lines, 285 shipped
instruction lines, 1,119 formatted metadata lines, 66 CI lines and 136 README/
provenance lines, each added from zero. Growth covers the approved trust/scenario
resolution, graph routes, strict source-bound report transport and regression
boundaries; the metadata total includes expanded JSON formatting for 107 IDs.
The functional outcome is unchanged. Local verification now comprises 150 tests,
separate dedicated semantic behavior and bounded context-limited choice probes.

Code R1 correction size: production +137/-32 lines, net +105, giving 2,165
production Python lines across the same seven files. Estimated novel core is
approximately 850-1,050 lines. Regression additions are 297 test lines across
three files; review/status/provenance documentation is counted separately.
Growth corrects approved reference, partial-coverage, snapshot-binding and scenario
contracts; it adds no new audit population or configuration emulator. Final local
dedicated verification now passes 166 tests plus the skill validator.

Code R3 correction size: production +58/-32 lines, net +26, giving 2,191 Python
lines across the same seven files; estimated novel core remains approximately
850–1,100 lines. Separately, new regressions add 388 lines across three files,
existing tests change +10/-4, and shipped skill/reference instructions add 123
lines. Review/status/README records are separate. Growth closes existing sensitive
read, reference, scope, interruption and input-transport contracts. Final local
dedicated verification passes 182 tests plus the validator, with a separate
documentation-driven rescan and two bounded decision checks. No new objective,
generic parser framework or owner-gate change is introduced.

Code R4 correction size: production +114/-28 lines, net +86, giving 2,277 Python
lines across the same seven files; estimated novel core remains approximately
850–1,150 lines. New regressions add 337 lines across four files; review/status
records are separate and shipped skill instructions are unchanged. Growth closes
known-sensitive metadata, nonregular configuration and reference parsing/inventory
contracts, including independently reproduced delimiter/context regressions.
Final local dedicated verification passes 199 tests plus the validator. The
known Minor repeated graph-build work is explicitly deferred; route enumeration
limits do not promise bounded graph construction. No new objective is added.

Code R5 correction size: production +100/-35 lines, net +65, giving 2,342 Python
lines across the same seven files; estimated novel core remains approximately
850–1,200 lines. New regression tests add 482 lines across four files. Shipped
instructions/reference changes are +17/-3; repository review/status/README/AGENTS
records are separate. These changes close existing traversal, input, output
ownership, classification and per-directory reporting contracts. Final dedicated
verification passes 26 focused / 225 full tests and the skill validator; two fresh
Sol/medium choices cover the existing-parent output condition. Whole-file caching
and per-route synchronous receipts are separately recorded performance limitations,
alongside prior graph-build work; no new memory threshold or runtime guarantee is
introduced. No audit population, semantic approval boundary or objective changes.

## 8. Decisions reserved for the owner or execution preflight

| Question | Proposed starting point | Boundary |
| --- | --- | --- |
| First release mutation mode | Report and concrete diffs; apply only an explicitly selected follow-up diff | `workflow` was left undecided |
| Audit target | AGENTS.md and reachable related files only | SKILL audit removed by the later owner instruction |
| Root set for a real audit | Codex home plus chosen project roots, enumerate every distinct nested chain | No silent entire-home scan |
| Extended I03 assessment | Map new evidence into the original six weights | No invented extra total or pass threshold |
| L-SCORE-DELTA aggregates | Owner adopted one PASS/FAIL/NA per ID, duplicate rejection, PASS/(PASS+FAIL), separate NA/unassessed | Zero denominator is undefined; comparable explicit FAIL-to-PASS only |
| Global/reference warning budgets | Show terminal-route sizes without fabricated utilization | 90% applies only to a known corresponding budget |
| Inaccessible branches | Record blocked frontiers and review accessible paths | No permission escalation or task-wide stop for a partial tree |
| Recognition model | Owner-selected Sol/medium choice probe, exact ID resolved at dispatch, fork_turns=none | History isolation is not proof of memory isolation |
| Public distribution | Public GitHub repository, tagged skill package, reproducible installer path | Official marketplace acceptance is not promised |
| Public requirements ledger | Approve verbatim ledger inclusion, or approve an independently derived included-ID fixture with ledger-hash provenance | Decide before public-source/CI publication; local coverage work can use the private ledger |
| License | MIT selected by the owner on 2026-10-03 | Retain required notices in the installed subtree |
| Dedicated skill executor | Create/verify an exact-SOT binding before behavioral RED/GREEN | Missing role blocks that test, not planning or static analysis |

There is no need to settle all 52 pending criteria to implement the selected scope. Keep them visible in the decision record and introduce one only if the owner chooses it or explicitly accepts a necessary new design decision. Do not use pending items as hidden release blockers.
