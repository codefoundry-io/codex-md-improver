# Formal plan review — round 5

Date: 2026-10-03. Review ID: `codex-md-plan-20261003-r5`.
Basis digest: `279dc792b8a4ac25a55274f4d440e3b191ab6f7ab617e02eb2249e08ba539fab`.
Result: **BLOCKED; no admission**. All four writers completed; collection
verified bound integrity, no missing leg and no selection deviations. Full raw
custody and leader dispositions were exported before official temporary cleanup.

| Leg | Requested configuration | Result |
| --- | --- | --- |
| Claude | `claude-opus-5-5`, `xhigh` | SAFE TO MERGE; 9 Minor findings |
| Codex | native `gpt-6-astra`, `high`, no history fork | MERGE WITH FIXES; 1 must-fix |
| Google Pro | AGY `gemini-3.1-pro-high`, `high` | SAFE TO MERGE; no findings |
| Google Flash | AGY `gemini-3.8-flash-high`, `high` | SAFE TO MERGE; no findings |

Every leg had web authorization. Requested identities are not hidden runtime
attestation. No approval transfers to the amended plan.

## Verified blocking correction

Astra identified a real simultaneous-environment contract gap. Independent
hypothetical starts may resolve different configurations, but the
[pinned loader](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs#L53-L85)
uses one active-project trust gate and one Config for an ordered environment
group. The plan now requires a group-effective record instead of merging member
settings. Unknown dependent values remain unresolved; known untrusted gating or
zero budget still establishes zero project inclusion. An independent Sol check
found that last boundary case before the amendment. CLI fixtures cover conflicting
local budgets/fallbacks, shared trust and the zero/unknown combinations.

## Non-blocking corrections and narrowed claims

1. **Trust identity:** accept the distinction from loader marker roots, but
   narrow the reviewer's Git-root-only suggestion. Official source checks cwd
   first and validated Git/main-root fallback second, canonical then original
   spelling. An existing cwd entry with unset trust stops fallback. Confirmed
   unset does not equal unknown or explicit untrusted. Unknown layers/metadata
   remain uncertainty. This was checked independently against
   [lookup](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/config/src/project_trust.rs#L41-L95),
   [Git validation](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/git-utils/src/trust.rs#L71-L223)
   and [predicates](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/config/src/config_toml.rs#L596-L607).
   A third-party changelog was not used as conformance evidence.
2. **Missed references:** permit semantic resolutions to introduce an occurrence
   bound to source hash/span/text, without requiring a lexer match.
3. **Comparison scope:** compare requested roots/cwd/home/settings; changes to
   discovered chains or regions are deltas, not automatically incomparable.
4. **Implicit Git administration:** record it as a boundary during normal linked
   directory recursion. Explicit storage dependencies retain limited coverage.
5. **Code/config evidence:** ordinary string paths do not become instructions;
   an explicit source-bound read decision can add an edge.
6. **Directory aliases:** another selected project can supply target scope;
   unresolved outside-scope inventory frontiers produce partial coverage/exit 3.
7. **Executor status:** the project role is prepared but unavailable in this
   active catalog. Correct stale wording and apply the managed exact-source
   sequence to bundled script behavior as well as the later entrypoint.
8. **Public ledger:** remove the incorrect paraphrase claim. Verbatim owner text
   needs an explicit public allowlist decision; an excluded ledger requires an
   approved independent ID fixture before public CI depends on its contents.
9. **Sensitive paths:** enumerate the bounded configured path set and test its
   aliases. Incidental-value non-disclosure is a semantic/prompt obligation;
   this does not introduce or claim generic secret detection.

These are static contract corrections and planned tests, not executed product
verification. The aggregate-output choice and exact executor remain unresolved.
No product implementation, publication or installation is claimed. A new complete
round must judge the amended plan.
