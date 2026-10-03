# Pre-implementation web research review

Date: 2026-10-03. Status at research completion: implementation paused at the owner's request. The owner subsequently resumed plan review, implementation and pre-merge review; accepted amendments are now reflected in the implementation plan. This research report itself is not formal review admission or implementation evidence.

## Scope and basis

The product audits **AGENTS.md, its loader-selected variants, and related linked files only**. Existing SKILL.md files remain excluded boundaries. Delivering the product as a Codex skill does not expand its audit targets.

All reviewers received the same complete plan and owner-decision record, plus the three latest approved clarifications: repository discovery through a symlink to the canonical source, analyzer resolution from the installed skill location, and default whole-selected-project scope with explicit current-cwd narrowing. These clarifications were part of the review basis even though not yet incorporated into the plan text.

Input hashes:

| Input | SHA-256 |
| --- | --- |
| Implementation plan | `8e45d67431c064e51851041ff4e7a26360cb2a66fbf02702e96690ed38d1dd35` |
| Owner decisions | `110b1bb511940b2057ab13fd197e6ffaec513910a83d30cd97f75fb6a8051b3b` |
| Common research prompt | `3bc13a8e70edd2475562333ddbf0f1a105d4dd5dac621c96efcc487991a402fc` |

The originals and packet copies matched these hashes after every reviewer terminated. Packet inventory was unchanged. Product implementation, Git initialization, installation, remote publication and target migration were not performed.

## Reviewers and evidence

| Reviewer | Requested configuration | Outcome and useful contribution |
| --- | --- | --- |
| Opus | `claude-opus-5-5`, `xhigh`, raw Claude research wrapper | Exit 0; 514.65 seconds. Independently identified configuration regions; useful directory-burden, loader-error and probe-validity refinements. Several broader alternatives need rejection or owner choice. |
| Google Pro | AGY `gemini-3.1-pro-high`, `high` | Exit 0; 158.60 seconds. Mostly repeated approved clarifications. Suggested model substitution without supporting evidence. |
| Google Flash | AGY `gemini-3.8-flash-high`, `high` | Exit 0; 208.78 seconds. Useful route-volume concern; several findings were already addressed, overstated, or contradicted source/owner choices. |
| Astra | Native `gpt-6-astra`, `high`, `fork_turns=none` | Completed. Identified configuration-region defect; useful loader, reference-occurrence and installable-notice refinements. |

All four had explicit web search/fetch authorization. Codex additionally had explicit OpenAI Docs access. Reviewers were instructed to inspect read-only, avoid candidate execution, avoid sibling results and exclude Claude-host implementation. This was the TRIAD raw investigation route, not a formal four-leg admission. Requested settings are not hidden-runtime attestations. AGY exposed the requested model identities; authoritative effective Opus/Astra settings were not exposed.

Opus's task-specific session contained 25 completed WebSearch/WebFetch tool-result pairs with no tool-level error flags; that does not guarantee every page extraction succeeded. Google reported fetched pages, but successful wrapper audit logs retained only truncated event-stream heads. Full Google page-fetch custody is therefore **UNSURE**. The leader independently fetched the primary sources needed for retained conclusions. No missing telemetry is counted as proof of a successful fetch.

Local evidence is retained under the infrastructure run ID `20261003-codex-md-plan-web`: input manifest, common packet, four review reports, original wrapper captures, terminal metadata, source-fetch receipts and Opus web-event metadata. These raw operational files are not public-release content.

## Conclusion

Retain the read-only analyzer plus short semantic-review skill. The strongest new correctness finding is that **effective relevant settings must participate in scope partitioning**. Several smaller amendments improve measurement and operational clarity without broadening the product.

The latest OpenAI guidance supports task-conditioned reference reading and revisiting accumulated instructions. It does not establish that every shorter file produces better task performance, or that instructions useful to one model should be deleted for all models. Keep exact environmental facts and owner-controlled boundaries. [OpenAI guidance, published 2026-09-11](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).

## Recommended amendments

### R1. Partition by configuration as well as instruction files — material correction

Both Astra and Opus found this independently. Plan §2.1 currently merges directories with identical selected chains; Task 1 exposes one `LoaderSettings` record per request.

Counterexample: root AGENTS.md is 20,000 bytes. Two subfolders select it, but one trusted subfolder has a 16,384-byte budget. Merging them hides clipping or assigns the wrong utilization. Trusted project configuration follows root-to-cwd layering, with nearer settings taking precedence. [Official configuration precedence](https://learn.chatgpt.com/docs/config-file/config-basic#configuration-precedence).

Resolve the relevant settings per hypothetical cwd/scenario. A region identity must include ordered selected sources, effective relevant values, trust and unresolved provenance. Configuration boundaries can create regions even without a new AGENTS.md. Explicit simultaneous-environment groups retain their session settings and environment ordering. Cache common prefixes; do not recreate the complete Codex configuration engine.

### R2. Refine loader-error and byte fixtures — existing requirement made precise

Keep the analyzer's accessible-area policy. Separately report what the modeled loader would do. A readable subset is a lower bound on inspected file volume, not automatically a lower bound on instructions Codex includes.

At the pinned source, a non-NotFound read error propagates out of the environment loader; the caller may omit that environment's project instructions or fail the load, depending on its sandbox context. Selection occurs before empty-content filtering. Clipping operates on raw bytes before lossy decoding; within-environment and outer-environment accounting use different lengths. Record retained source bytes, decoded content bytes and loader outcome distinctly where necessary. [Pinned loader source](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs).

Task 1 already asks for empty, decoding and read-failure fixtures. This is a refinement of those tests, not three new missing features. Analyzer permissions do not establish the client's actual permissions; unknown runtime facts remain unknown.

### R3. Add a directory-read total alongside terminal rows

Opus identified a useful reporting gap. If an instruction says to read a folder containing 200 distinct 5 KiB documents, showing 200 separate small leaf routes can obscure the approximately 1,000 KiB instruction burden.

Retain every terminal route. Additionally summarize each directory-read dependency's known unique descendant text bytes, file count, conditions and unresolved frontiers. Include the common AGENTS prefix once in a scenario total. This is a file-volume summary, not an assertion that the agent actually read every byte or that the project loader consumes those references.

### R4. Preserve reference occurrences and a bounded resolution follow-up

Astra's alias observation and Opus's uncertain-edge observation concern the same separation: file identity is not reference meaning.

Cache physical content once, but retain each referring path/base, source span and read condition. When semantic review resolves a previously uncertain edge, allow the verified decision to feed a subsequent scoped graph expansion. Keep unresolved branches partial until resolved. Do not automatically traverse both interpretations of every ambiguous path: that can expand beyond the selected graph and conceal uncertainty. A small explicit decision input is sufficient; no general workflow engine is needed.

### R5. Distinguish invalid probes from failed recognition

Add a simple positive control and validate case identity/output shape before scoring candidate recognition. Missing tools, task-delivery failure, wrong case or unavailable model yields `invalid_probe`, not a wording failure. Record client version and the existing history/memory exposure labels.

An upstream no-fork delivery issue concerns older alpha versions; it is a reason to check validity, not proof of a current defect. A merged upstream change documents inherited user-instruction snapshots. Neither `fork_turns=none` nor a prompt prohibition establishes memory isolation. Keep these probes narrow and avoid revising wording on invalid evidence. [Reported delivery issue](https://github.com/openai/codex/issues/25458), [instruction-provider change](https://github.com/openai/codex/pull/27101).

### R6. Keep runtime prerequisites and installed payload explicit

- Retain Python 3.11+. Check interpreter capability before analyzer imports and return a clear setup error when unsupported. Do not lower the floor or build a replacement TOML parser merely to accommodate an older system executable. Python documents `tomllib` as added in 3.11. [Python documentation](https://docs.python.org/3/library/tomllib.html).
- Keep required notices in the installable skill subtree, or define and test their installation mapping. The fetched official installer copies the selected skill directory; root-only notices do not automatically follow it. This is an artifact-consistency issue, not a legal conclusion. [Installer source](https://github.com/openai/skills/blob/main/skills/.system/skill-installer/scripts/install-skill-from-github.py).
- Incorporate the already-approved discovery link, installed-script resolution and explicit cwd selection into the plan. `agents/openai.yaml` provides metadata/policy; it is not an arbitrary-folder discovery registration. [Official skill discovery](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills).

## Route growth: keep the requirement, improve operational reporting

Opus, Flash and Astra correctly raised combinatorial output growth. A graph can have few unique files and many distinct simple routes; streaming reduces memory but not output volume. [Primary algorithm documentation](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.simple_paths.all_simple_paths.html).

Keep the owner's every-accessible-route contract. Use immutable chain/node records and streamed route records, stable ordering, progress counts and a partial receipt on interruption or an explicitly selected resource cap. The plan already allows user-imposed caps with partial status. Do not silently add Flash's arbitrary 2,000-route/32-depth defaults.

Opus proposes replacing literal routes with strongly connected component aggregates and samples. That changes the agreed output. Also, summing every component member does not preserve each original simple path's byte total; collapsing cycles does not eliminate the possibility of many paths in the remaining DAG. The proposed claim that this preserves all original route information in linear time is not established. Aggregated views can supplement the full route data; replacing it requires an owner decision.

## Findings not adopted as new defects

| Reviewer proposal | Adjudication |
| --- | --- |
| Pro/Flash: missing discovery link, installed-script resolution, cwd narrowing | Already supplied as approved clarifications in the review basis. Incorporate them into text; do not count them as newly discovered design defects. |
| Pro: override and ordinary AGENTS might both be counted | Plan already specifies selected chains, active/shadowed variants and override/fallback fixtures. Make fixture selection explicit; no evidence that the approved design sums both. |
| Pro: replace Luna with Flash or GPT-4o-mini | Rejected. Unsupported substitution of the owner's configurable family choice. Current official subagent guidance explicitly recognizes GPT-6 Luna for light work. [Official guidance](https://learn.chatgpt.com/docs/agent-configuration/subagents#model-choice). |
| Flash: change the default-budget citation from line 74 to line 82 | Refuted. Direct download of the pinned raw file places `DEFAULT_PROJECT_DOC_MAX_BYTES` at line 74, matching the plan. Raw SHA-256: `05b6d259c8882322d33a997d69c0898f7ca3693552bf9ec5f4a8f1c60457bb1e`. Rendered/extracted page line numbers are not source line numbers. |
| Flash: replace the dedicated host behavior executor with fixture mocks/API cases | Rejected as a substitute for required host behavior evidence. The plan already separates host-owned executor validation from the portable analyzer and ordinary CI. Mocks cannot prove actual skill behavior. |
| Flash: remove synthetic quality scores | The owner explicitly included the subjective I03 rubric. Keep its limits and evidence. Pending pass-rate semantics are a different question already held in §8. |
| Flash: adopt a Markdown AST dependency and published schema now | Optional, not established requirements. Show a concrete unsupported case before expanding the standard-library design. Versioned structured output is already planned. |
| Opus: replace archive distribution with only a tagged tree | Optional scope tradeoff. Keep one canonical tree and a derived archive with equality checks; the owner requested distribution planning. Avoid two independently maintained payloads. |
| Opus: Desktop requires a plugin wrapper | Unproven for the current client. The cited issue reports an older app version. Keep fresh client discovery verification; do not preemptively add a plugin/marketplace project. [Historical issue](https://github.com/openai/codex/issues/28505). |
| Opus: apply its host's global rule against committed symlinks | Outside the supplied project review basis. Do not import another reviewer's host governance into this project's requirements. Resolve repository policy from this project's applicable instructions. |
| Absolute paths are inherently bad | Not adopted. The owner explicitly requires absolute paths. Portability advice must distinguish personal/global instructions from shared repository guidance. |

## Do not build in this scope

- A standalone SKILL.md/CLAUDE.md auditor, universal prompt optimizer or disconnected filesystem/web crawler.
- A full configuration/trust/managed-policy emulator or persistent context service.
- Automatic instruction deletion, global/project moves, conflict resolution or blanket deduplication.
- Hard quality gates from negation density, dates, byte reduction or subjective rubric totals.
- Broad agent-performance experiments, a provider SDK or global memory-setting changes for narrow recognition checks.
- A route-summary replacement that silently removes the promised terminal-route evidence.
- Pending legacy score parsers/tallies or an assumed pass-rate contract.
- A plugin marketplace extension or duplicate canonical skill tree merely to solve local discovery.

## Research interpretation limits

The September 29 revision of *Evaluating AGENTS.md* still evaluates older model configurations including GPT-5.2 and Sonnet 4.5; its revision date does not make it direct evidence for current Astra/Opus behavior. [Paper v3](https://arxiv.org/html/2602.11988v3).

The July study includes GPT-5.5 and Sonnet 4.6 across three repositories, but reports no detectable correctness advantage in its tested conditions and notes delivery-channel/corpus confounds. It supports caution about performance promises, not universal removal of instructions. [Paper v1](https://arxiv.org/html/2607.27250v1).

This product should claim measured byte/reference changes and evidenced findings. It should not claim improved defect detection, coding success or token consumption without a separate appropriate experiment.

## Decisions and next step

The existing score-denominator choice and license choice remain explicit pending decisions; they do not block unrelated analyzer design. Preserve the accepted owner-control and partial-access boundaries.

Recommended next action: amend the plan with R1–R6 and the approved three clarifications, retain full terminal-route reporting, then resume implementation under the existing verification policy when the owner resumes it. No source or plan mutation is performed by this research report. Formal plan admission, implementation review, release approval and actual installation remain separate claims.
