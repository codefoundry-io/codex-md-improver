# Included-criteria traceability

Design coverage for the [owner ledger](2026-10-03-owner-decisions.md) and
[implementation plan](../superpowers/plans/2026-10-03-codex-md-improver.md).
Each included identifier has exactly one row below. These are planned surfaces
and verification obligations, not claims that implementation or tests exist.
The 52 pending criteria and the excluded seed-and-edit criterion remain outside
the enabled rule set and create no acceptance gates.

## Coverage metadata and verification notation

Ship `assets/criteria.json` in the canonical skill subtree as coverage metadata:
included ID, rule group, applicable surface, evidence/report field, and
verification kind/reference. `tests/test_rule_coverage.py` must assert exact set
equality with the 107 included IDs, uniqueness, valid group references, and the
17 selected detector IDs. Packaging must include that asset. This is mechanical
traceability; neither a group reference nor a passing coverage test proves that
a semantic criterion was assessed or satisfied. Do not preload this full table
or the questionnaire into the runtime prompt.

The expected included-ID set comes from the checked-in owner ledger's Included
table, independently of criteria.json. Tag each non-detector ID beside its shipped
conditional review rule and verify those tag/group targets exist. This catches
missing wiring, not the quality or actual execution of a semantic judgment.

Paths below are relative to the installable skill subtree unless prefixed with
`tests/`. Proposed evidence fields refer to the plan's typed records, not a new
schema replacing them. The implementer must carry these concepts into the
validated `AssessmentInput` and report schema with source/provenance bindings.

| Rule group | Conditional surface and evidence |
| --- | --- |
| `placement` | `scripts/discovery.py`, `references/review-rules.md`: selected chains, scope and instruction/skill/plan/configuration placement |
| `burden` | `scripts/references.py`, `references/review-rules.md`: reachable paths, conditions, terminal-route totals, coverage frontiers |
| `durable` | `references/review-rules.md`: reusable facts, current rules, bounded supplied-session observations |
| `wording` | `references/review-rules.md`: concise wording, rationale, duplicates, meaningful exceptions |
| `environment` | `references/review-rules.md`: current source/configuration evidence and verified external claims |
| `proposals` | `scripts/reporting.py`, `references/review-rules.md`: source-bound judgments, concrete diffs, owner decisions, comparison |
| `recognition` | `scripts/recognition.py`, `references/recognition-probes.md`: bounded independent recognition and isolation evidence |
| `candidates` | `scripts/lint_candidates.py`, `assets/defaults.json`: only the selected heuristic branches |

`D-discovery`, `D-reference`, `D-lint`, `D-report`, and `D-recognition` mean
deterministic fixtures in, respectively, `tests/test_discovery.py`,
`tests/test_references.py`, `tests/test_lint_candidates.py`,
`tests/test_reporting.py`, and `tests/test_recognition.py`. `S-owner` means
explicit semantic owner review of the cited evidence and proposed wording;
it is not a deterministic quality oracle. A row naming both requires both
schema/arithmetic/behavior checks and that semantic review. Recognition validity
and declared-answer comparison are deterministic; interpretation, generalization
and migration acceptance remain bounded judgments.

## Scope and observation constraints

Audit AGENTS.md, loader-selected variants and their reachable related documents.
An existing SKILL.md edge is an excluded terminal boundary. Original ideas about
skill invocation/type separation apply here only to AGENTS conditional guidance
and placement recommendations; they do not create a SKILL auditor. Code/config
read for evidence is not prose to rewrite. No detection hit authorizes deletion.

Bounded observation ADDITION proposals may use only current user-supplied or
current-session evidence. Record the observation's provenance, the missing
information, why it is a reusable instruction candidate, a concrete addition
diff, and expected utility. Bind it to the existing AGENTS-linked migration
target set and current source hashes. A named new destination requires the
owner's specific decision before joining the write set. Keep personal context
and uncertainty visible. There is no session-history crawler, memory write,
automatic learning insertion, or assumption that one mistake merits a rule.

Subjective assessment uses the plan's six dimensions and original 100 total
weight, with explicit evidence and unassessed states. No universal quality score
or pass threshold is introduced. Requested structured before/after verdict
aggregates retain their unresolved owner contract; unrelated pending score
criteria do not become gates while that bounded decision is settled.

## Mapping

| ID | Implementation surface / rule group | Evidence / report field | Verification |
| --- | --- | --- | --- |
| AG01 | `durable`: recurring project information | Semantic finding: relevance and reuse evidence | S-owner: ongoing utility |
| AG02 | `placement`: global/repository/nested roles | Chains; placement proposal and scope alternatives | D-discovery: distinct regions; S-owner: placement |
| AG03 | `placement`: select effective guidance first | Ordered selected sources and settings provenance | D-discovery: separate global/project override, home-resolution and read-error fixtures |
| AG04 | `placement` + `burden`: overrides, fallbacks, linked paths | Selected sources; graph edge occurrences | D-discovery: empty override/fallback; D-reference: linked expansion |
| AG05 | `placement`: client-specific loader scenarios | LoaderSettings client/version, uncertainty | D-discovery: supplied/default scenario labels; S-owner: runtime limits |
| AG06 | `placement`: aggregate project byte budget | Original/charged/retained raw/decoded bytes | D-discovery: budget, whitespace, multibyte fixtures |
| AG07 | `placement`: clipping and omitted guidance | ChainReport clipping/omissions and modeled outcome | D-discovery: exhaustion and unreadable-source outcomes |
| AG08 | `placement` + `proposals`: separate global budget and scope moves | Original/trimmed global bytes and runtime-cache uncertainty; owner decision for move | D-discovery: global provider has no project cap, selection/errors; D-report: deferred proposal; S-owner: move |
| AG09 | `placement`: known budget warning | Warning state, limit and provenance | D-discovery: 90% integer boundary, equality, zero/unknown limits |
| AG10 | `burden` + `recognition`: conditional reads and recognizable triggers | Edge conditions; expected/observed selected sources | D-reference: conditions; D-recognition: case validity; S-owner: trigger utility |
| AG11 | `wording`: useful scope/rationale without incident history | Semantic finding; rationale-retention/rewrite proposal | S-owner: needed rationale versus needless history |
| AG12 | `environment`: delegate mechanical checks to actual tools | Tool-backed source evidence; command proposal | S-owner: appropriate enforcement; D-report: evidence bindings |
| AG13 | `environment`: obsolete model workarounds | Current official/web source provenance, uncertainty | S-owner: verified claim and bounded alternative |
| AG14 | `placement`: environment rule versus skill/plan | Destination recommendation and owner decision | S-owner: classification; D-report: destination bounds |
| AG15 | `environment` + `proposals`: permission/configuration alternatives | Current settings/source evidence; named alternative | S-owner: authority preserved and verified alternative |
| AG16 | `proposals`: identify stopping instruction | Finding source span, blocking consequence, unresolved decision | D-report: valid spans/dispositions; S-owner: actual cause |
| AG19 | `proposals`: explain false-positive alternatives | Rejected finding evidence, confidence, alternative wording | D-report: retained rejection; S-owner: causal judgment |
| AG20 | `placement` + `durable`: instructions versus memory/history/config | Placement rationale and history-removal candidate | S-owner: preserve useful instructions; no memory writes |
| AG22 | `proposals`: prepare minimal diff and reason | Replacement/addition diff, source hash, reason | D-report: stale hash and proposal validation; S-owner: minimality |
| AG23 | `proposals` + `recognition`: wording versus behavior evidence | Disposition, byte delta, separate recognition evidence | D-report: no inferred resolution; S-owner: evidence limit |
| C1 | `burden` + `recognition`: AGENTS what/when conditions only | Read condition and bounded selection case | D-recognition: validity/comparison; S-owner: applicability |
| C3 | `wording`: inputs/actions/outputs; candidate assistance | Semantic finding linked to candidate evidence | D-lint: world-fact candidate fixtures; S-owner: actionable wording |
| C4 | `wording`: excuses and failure narrative | Candidate spans; semantic rationale | D-lint: positive/exception fixtures; S-owner: needed context |
| C5 | `wording`: duplication and needless explanation | Related spans, duplicate intent, consolidation diff | S-owner: necessity; D-report: owner-deferred duplicate |
| C6 | `wording`: calm direct instructions | Density candidate and semantic finding | D-lint: line-count/minimum-body fixtures; S-owner: tone |
| C7 | `wording`: unnecessary forced steps | Workflow consequence and bounded replacement | S-owner: required versus needless sequence |
| C8 | `durable` + `environment`: stale dates/versions/models | Six body-candidate kinds; verified exception evidence | D-lint: each branch and protected identifier; S-owner: freshness |
| C9 | `burden`: all instructed file/folder reads, conditional detail | Graph occurrence conditions, route bytes, TOC candidate | D-reference: plain/directory paths; D-lint: reference TOC; S-owner: need |
| C10 | `wording`: positive action wording | Negation candidate; replacement preserving boundary | D-lint: occurrence-count fixtures; S-owner: safe meaning |
| C11 | `wording`: consumer language/context | Audience evidence and unresolved language judgment | S-owner: consumer fit; D-lint: Korean exceptions |
| C12 | `environment`: tools, types, identifiers and errors | Current source evidence, exact literals, exceptions | S-owner: technical correctness and preservation |
| C15 | `proposals`: contradictory instructions | Both spans, consequence, alternatives, owner decision | D-report: unresolved decision retained; S-owner: resolution |
| I01 | `placement`: location and scope | Selected chains, source roles and region provenance | D-discovery: roots/siblings/config regions; S-owner: scope |
| I02 | `environment`: compare guidance with current repository | Source/hash bindings and verified findings | D-report: stale source rejection; S-owner: match |
| I03 | `proposals`: six-dimension subjective rubric | Dimension score/evidence, unassessed state, complete total | D-report: weights/ranges/incomplete arithmetic; S-owner: assessment |
| I04 | `proposals`: baseline quality report | Before AuditReport, findings, coverage, assessment | D-report: baseline retained and unassessed handling; S-owner: findings |
| I05 | `proposals`: per-file diffs and reasons | Source-bound proposal, replacement and reason | D-report: proposal binding; S-owner: change rationale |
| I06 | `placement` + `proposals`: small linked-target migration | Current target set, diff, destination owner decision | D-reference: excluded skill boundary; D-report: write-set bounds; S-owner: minimality |
| I07 | `environment`: commands and workflow | Commands/workflows dimension evidence | S-owner: verify actual commands without executing audited instructions |
| I08 | `placement`: necessary structure facts | Structure dimension with repository evidence | S-owner: relevance and verified structure |
| I09 | `wording`: useful traps and exception rationale | Non-obvious-patterns dimension, retained exceptions | S-owner: reason and operational value |
| I10 | `wording`: reduce needless prose | Concision evidence and byte/replacement delta | D-report: byte comparison; S-owner: necessity |
| I11 | `environment`: current commands/paths/technology | Freshness evidence and unresolved claims | D-reference: missing/path states; S-owner: current-source verification |
| I12 | `wording` + `proposals`: actionable specifics | Actionability dimension, concrete diff | S-owner: executable meaning; D-report: complete proposal fields |
| I13 | `durable`: obsolete/copied facts | Candidate/source evidence, verification/rejection | D-lint: body candidates; S-owner: copied/stale judgment |
| I14 | `wording`: only needed template sections | Section relevance and removal proposal | S-owner: necessity with owner context |
| I15 | `placement`: repository-aligned locations | Scope alternatives, linked destination, incoming references | D-reference: incoming edges; S-owner: location decision |
| I16 | `environment`: verified project information | Source/provenance and confidence | D-report: source-bound evidence; S-owner: fact validity |
| I17 | `durable`: remove one-off records/generalities | Reuse rationale and bounded proposal | S-owner: durable value and preserved context |
| R01 | `durable` + `proposals`: bounded observation ADDITION | Current supplied/session provenance; missing information; concrete add diff | D-report: observation/source/target binding; S-owner: candidate utility |
| R03 | `durable`: retain reusable learning only | Observation reuse rationale, confidence and disposition | S-owner: recurring value versus one-off; D-report: provenance required |
| R04 | `proposals`: explicit learning addition diff/utility | Addition text, destination, expected utility, owner decision if new | D-report: existing target/new-destination hold; S-owner: actual addition |
| P03 | `proposals`: evidence-based deletion | Source span, reason, confidence and selectable diff | S-owner: concrete justification; D-report: complete proposal |
| P04 | `durable`: preserve owner-only context | Context uncertainty and deferred disposition | S-owner: missing context; D-report: unresolved retained |
| P05 | `proposals`: report low-confidence issues | Confidence, unresolved state, no accepted migration | D-report: deferrals visible; S-owner: confidence |
| P06 | `wording`: emphasis, reprimands and softeners | Candidate/semantic evidence and replacement | D-lint: softener fixtures; S-owner: tone and meaning |
| P07 | `wording`: over-prescribed judgment steps | Workflow evidence, consequence, alternative | S-owner: bounded sequence change |
| P08 | `environment` + `wording`: preserve fragile sequence | Protected workflow evidence and exception | S-owner: required ordering; D-report: explicit retained exception |
| P09 | `wording`: example anchoring | Example span, consequence, alternative proposal | S-owner: useful example versus harmful fixation |
| P10 | `wording`: repeated generalities/exception accumulation | Related spans, necessity and consolidation proposal | S-owner: concise preserved purpose |
| P11 | `environment`: old-model workarounds | Current verified web/source evidence and uncertainty | S-owner: claim and safe alternative |
| P12 | `durable`: avoid permanent rule from one error | Supplied observation, reuse rationale, rejected/deferred finding | S-owner: recurring value; D-report: provenance/disposition |
| P13 | `durable` + `wording`: current applicable rules | Scope/rationale and present-rule rewrite | S-owner: applicability and preserved meaning |
| P14 | `environment`: check volatile facts against code | Current source hashes, evidence spans, unresolved facts | D-report: stale bindings; S-owner: fact verification |
| P15 | `wording` + `proposals`: conflict versus intended exception | Both spans, exception evidence, owner decision | S-owner: actual conflict; D-report: deferred resolution |
| P16 | `environment`: preserve authority during freshness edits | Permission consequence and protected boundary | S-owner: authority comparison before acceptance |
| P17 | `wording` + `proposals`: intentional duplicates | Related spans, duplicate rationale, owner decision | S-owner: intent before consolidation; D-report: decision hold |
| P18 | `wording`: reason for prohibition | Source rationale, consequence, alternative | S-owner: necessary boundary versus needless negation |
| P19 | `wording`: numerical demands | Numeric span, purpose and exception evidence | S-owner: functional constraint versus arbitrary number |
| P20 | `proposals`: evidence/confidence for each finding | Rule ID, source spans/hashes, confidence, provenance | D-report: validation; S-owner: confidence grounded in evidence |
| P21 | `proposals`: separately selectable changes | Per-proposal diff, dependencies and decision state | D-report: discrete proposal records; S-owner: selection |
| P22 | `wording`: concise rewrite preserving purpose | Original/replacement spans and purpose rationale | S-owner: meaning preserved; D-report: source binding |
| P23 | `recognition`: fresh inexpensive recognition | Expected/observed answer, control, model, isolation | D-recognition: validity and comparison; S-owner: bounded inference |
| P24 | `proposals` + `recognition`: restore necessary rules on regression | Before/after mismatch, restoration proposal, disposition | D-report: no false resolution; D-recognition: valid regression; S-owner: restore |
| P25 | `environment`: exact-string consumers | Consumer/source evidence, protected literals | D-lint: protected commands/IDs; S-owner: dependent consumer check |
| AA1 | `wording`: authoring-dialog residue | Candidate spans and semantic finding | D-lint: carryover fixtures; S-owner: removal relevance |
| AA2 | `wording`: greetings, self-description, apologies | Candidate spans and replacement | D-lint: chat-padding fixtures; S-owner: functional context |
| AA3 | `wording`: direct phrasing | Softener candidate and concrete replacement | D-lint: positive/exception fixtures; S-owner: meaning |
| AA4 | `environment`: do not invent concrete facts | Verified source/web provenance, unresolved claims | S-owner: source supports claim; D-report: evidence binding |
| AA5 | `wording`: functional formatting | Decoration candidate and retained functional exception | D-lint: decoration fixtures; S-owner: readability/function |
| AA6 | `wording`: body matches consumer language | Audience evidence, language candidate, unresolved state | D-lint: Korean/context exceptions; S-owner: consumer fit |
| L-C8-BODY-DATE | `candidates`: body date branch in `lint_candidates.py` | Candidate rule ID/span/parameters/exceptions | D-lint: date positive/exception, CRLF offsets |
| L-C8-BODY-YEAR | `candidates`: temporal-context year branch in `lint_candidates.py` | Candidate rule ID/span/context/exceptions | D-lint: temporal year positive/exception |
| L-C8-BODY-SEMVER | `candidates`: three-part version branch in `lint_candidates.py` | Candidate rule ID/span/exceptions | D-lint: semver positive/protected-command exception |
| L-C8-BODY-TOOLVER | `candidates`: tool/runtime version branch in `lint_candidates.py` | Candidate rule ID/span/context/exceptions | D-lint: tool version positive/legitimate identifier |
| L-C8-BODY-MODEL | `candidates`: model/codename branch in `lint_candidates.py` | Candidate rule ID/span/exceptions | D-lint: model positive/exact CLI ID preserved |
| L-C8-BODY-RECENCY | `candidates`: release recency branch in `lint_candidates.py` | Candidate rule ID/span/language limits | D-lint: recency positive/exception |
| L-C6 | `candidates`: imperative density in `lint_candidates.py` | Candidate aggregate, all locations, threshold parameters | D-lint: line counts, >8/100, minimum 25 body lines |
| L-C4-EXCUSES | `candidates`: enumerated excuses in `lint_candidates.py` | Candidate rule ID/spans/exceptions | D-lint: enumerated excuse positive/exception |
| L-C4-NARRATIVE | `candidates`: failure narrative in `lint_candidates.py` | Candidate rule ID/spans/language limits | D-lint: narrative positive/needed-context exception |
| L-C10 | `candidates`: negation density in `lint_candidates.py` | Candidate aggregate, occurrence locations, parameters | D-lint: occurrence counts, >8/100, minimum 25 lines |
| L-C9-TOC | `candidates`: reference TOC in `lint_candidates.py` | Candidate kind, line count and TOC evidence | D-lint: Markdown reference only, >100 lines, exception |
| L-C3 | `candidates`: world-facts assistance in `lint_candidates.py` | Candidate spans and explicit assist status | D-lint: positive/exception; S-owner: instruction relevance |
| L-AA1 | `candidates`: conversation carryover in `lint_candidates.py` | Candidate spans/exceptions | D-lint: positive/exception fixtures |
| L-AA2 | `candidates`: chat-register padding in `lint_candidates.py` | Candidate spans/exceptions | D-lint: positive/exception fixtures |
| L-AA3 | `candidates`: sycophantic softeners in `lint_candidates.py` | Candidate spans/exceptions/language limits | D-lint: positive/exception fixtures |
| L-AA5 | `candidates`: decoration overload in `lint_candidates.py` | Candidate spans/functional exceptions | D-lint: positive/exception fixtures |
| L-AA6 | `candidates`: body-language heuristic in `lint_candidates.py` | Candidate spans/audience uncertainty/language limits | D-lint: positive/Korean-audience exception; S-owner: verdict |
| L-REPORT | `proposals`: candidate output and CLI receipt | Full JSON locations, summarized Markdown, exit code | D-report + D-lint: line offsets, full locations, exit precedence |
| L-SEMANTIC | `proposals`: separate heuristic and semantic classes | Finding class, provenance, assessment/unassessed state | D-report: no automatic semantic PASS; S-owner: quality judgment |
| L-SCORE-DELTA | `proposals`: structured before/after comparison | AuditDelta findings/bytes; requested verdict aggregates pending bounded owner contract | D-report: partial/incomparable/moved evidence; S-owner: aggregate contract before aggregate implementation |
| U01 | `placement`: AGENTS versus excluded SKILL boundary | Target kind, excluded_skill terminal, placement recommendation | D-reference: no skill expansion; S-owner: AGENTS conditional guidance only |
| U02 | `recognition` + `proposals`: static versus behavior evidence | Separate detector, semantic and valid-probe evidence | D-report: evidence classes; D-recognition: validity; S-owner: recognition limits |
| U03 | `recognition`: narrow low-cost recognition only | Case packet/control, exact resolved model/effort, isolation | D-recognition: invalidity/status fixtures; S-owner: stated limited scope |
| U04 | `recognition`: resolve wording by concrete evidence | Valid mismatch or new evidence, bounded revision, unresolved outcome | D-recognition: invalid probes cannot drive revision; S-owner: no unsupported debate |
| U05 | `environment`: preserve concrete environment/execution settings | Settings provenance, protected commands/IDs and exceptions | D-discovery: scenario provenance; D-lint: preservation; S-owner: correctness |
| U06 | `wording`: consolidate duplicates with related evidence | Related source spans, purpose, owner decision, diff | D-report: source bindings and deferred duplicate; S-owner: valid consolidation |

Coverage acceptance checks IDs and referenced groups. Report acceptance separately
checks source-bound evidence, unassessed or unresolved areas, proposed decisions
and applicable verification. A complete metadata catalog cannot substitute for
the owner's semantic review or a valid focused recognition receipt.
