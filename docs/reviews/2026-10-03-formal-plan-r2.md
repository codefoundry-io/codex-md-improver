# Formal plan review — round 2

Date: 2026-10-03. Review ID: `codex-md-plan-20261003-r2`.
Basis digest: `2655e51181e07b38b064a00a1c372b6480f7261905a86fa59f727ef1f6f7e891`.
Result: **BLOCKED; no admission**. All four legs completed, bound integrity
passed, and no leg was missing. Custody was exported before official cleanup of
the exact managed temporary root. Raw provider records remain private.

| Leg | Requested configuration | Result |
| --- | --- | --- |
| Claude | `claude-opus-5-5`, `xhigh` | MERGE WITH FIXES; 2 must-fix findings and 12 minor findings |
| Codex | native `gpt-6-astra`, `high`, no history fork | SAFE TO MERGE; 2 minor findings |
| Google Pro | AGY `gemini-3.1-pro-high`, `high` | SAFE TO MERGE; no findings |
| Google Flash | AGY `gemini-3.8-flash-high`, `high` | SAFE TO MERGE; 1 hardening suggestion |

Every leg had web authorization. Requested settings do not attest hidden runtime
settings. The three approvals cannot substitute for the fourth or transfer to a
changed candidate. These protocol verdicts concern the plan, not product merging.

## Verified corrections

1. **Scenario-dependent references:** the old interface accepted seed paths and
   absolute bases without scenario context. One global instruction could not
   express two project-relative targets correctly. The graph now takes chains,
   preserves base kinds and resolves each occurrence per scenario. A two-project
   fixture must show distinct 10 KiB/50 KiB targets while caching source text once.
2. **Selected-rule coverage:** the owner ledger retained 107 included IDs, but the
   plan did not map each to a runtime surface. The new criteria map covers each ID
   once; shipped metadata and a set/uniqueness test will preserve that mapping.
   R01/R03/R04 now require bounded current-session/supplied-observation addition
   proposals with evidence, utility and an exact diff. No history crawler or
   automatic memory update is added. Semantic validity remains an owner judgment.
3. **User configuration and ancestor roots:** explicitly read relevant Codex-home
   configuration, record supplied override precedence and unresolved upstream
   layers, and include applicable loader ancestors above a selected subdirectory
   without expanding the recursive inventory arbitrarily.
4. **Skill-directory exclusion:** directory enumeration stops at a skill frontier.
   An explicit AGENTS link to a non-SKILL support file remains an allowed related
   target. It does not authorize reviewing the surrounding skill.
5. **Probe identity and execution:** requested, resolved and exposed effective
   identities are separate; hidden values remain unexposed. Audited instructions
   are data for semantic workers and probes. An embedded-command fixture checks
   that behavior; the report distinguishes prompt constraints from host controls.
6. **Report exits and probe schema:** define open/deferred findings for `report`,
   retained as well as new findings for `compare`, and resolved-only success.
   Add the previously described `revision_eligible` field to the result interface.
7. **Runtime and installation verification:** test the setup guard with actual
   Python 3.10, separately from the 3.11/3.12 support matrix. A disposable tagged
   installation must be discovered from its own temporary repository in a fresh
   session, with installed-path/hash evidence rather than a source alias.
8. **Pending selected output:** the aggregate-output choice blocks only that
   subrecord, but full selected-output completion or a reduced release contract
   cannot be claimed before the owner chooses. The other 52 pending criteria do
   not become release gates.
9. **Unicode loader conformance:** Rust's White_Space and Python's bidi-based
   whitespace tests differ. Add U+001C–U+001F fixtures and avoid Python default
   stripping as the loader oracle. The definitions were independently checked in
   [Rust documentation](https://doc.rust-lang.org/std/primitive.char.html#method.is_whitespace)
   and [Python documentation](https://docs.python.org/3/library/stdtypes.html#str.isspace).
10. **Execution handoff:** mark completed Git initialization and MIT selection,
    distinguish initial public-source publication from merge/release, state the
    canonical prefix for task file lists, and provide separate whole-plan core,
    tests, skill, metadata, CI and documentation estimates.

The selected-subdirectory finding's root-selection issue is accepted; its example
does not establish clipping merely from an approximate combined 32 KB size.
Actual clipping remains governed by exact retained-byte conformance fixtures.
All corrections preserve the approved AGENTS-only scope.

## Transport and remaining prerequisites

The minimal producer-schema repair kept the canonical verdict contract unchanged.
Targeted regressions: 92 passed, 4 skipped. The first full toolkit run inside the
sandbox recorded 1,831 passes, 4 skips and two `ps` permission failures. The exact
authorized command outside the sandbox then passed: **1,833 passed, 4 skipped**.
An independent Sol review approved the bounded patch. Both Google routes completed
live in R2, confirming backend acceptance. This is local toolkit evidence, not a
toolkit merge, installed-cache update or release claim.

The aggregate-output owner choice and exact dedicated behavior-executor availability
remain unresolved. They are not waived by this plan review. No product implementation,
behavioral RED/GREEN, public publication or installation is claimed. A fresh complete
round must assess the corrected plan.
