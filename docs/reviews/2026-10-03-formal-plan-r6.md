# Formal plan review — round 6

Date: 2026-10-03. Review ID: `codex-md-plan-20261003-r6`.
Reviewed plan commit: `c536a3a`.
Basis digest: `41485e911ebb8728a98d97c3821b22b8caf2567164c4bbbe686acbe25b36dde5`.
Result: **BLOCKED; no admission**. All four writers completed, with intact bound
state, no missing leg and no selection deviation. Raw custody was exported to
the private run archive and the exact managed temporary root was cleaned.
No provider log belongs in the public skill package.

| Leg | Requested configuration | Result |
| --- | --- | --- |
| Claude | `claude-opus-5-5`, `xhigh` | MERGE WITH FIXES; 1 must-fix and 6 Minor |
| Codex | native `gpt-6-astra`, `high`, no history fork | SAFE TO MERGE; no findings |
| Google Pro | AGY `gemini-3.1-pro-high`, `high` | SAFE TO MERGE; no findings |
| Google Flash | AGY `gemini-3.8-flash-high`, `high` | SAFE TO MERGE; no findings |

All reviewers had web authorization. Requested identities do not attest hidden
runtime settings. This review approves neither the plan nor future product code.

## Next blocking correction: default observed trust scenario

The plan says to provide a stated-default hypothetical scenario, but also turns
all unobserved upstream layers into unknown effective trust and then unknown
included bytes. In a normal no-settings scan of a repository trusted in the
observed config, this can hide inclusion/clipping for every inventoried cwd.
Supplied trust currently requires an exact-cwd fact rather than allowing one
real repository lookup-key entry to govern applicable subdirectories.

**Accepted; not yet implemented.** Separate the observed-plus-defaults
hypothesis from live-runtime attestation. Compute the former using observed
configuration and disclosed assumptions; retain missing live-layer attestation
as provenance. Unreadable/unvalidatable or explicitly unknown required inputs
remain unresolved. Accept supplied trust at actual lookup keys using cwd-first
and validated Git fallback, without arbitrary ancestor-prefix inheritance.
Keep explicitly unknown group-effective fields unresolved. Add a default CLI
fixture covering a trusted repository and multiple subdirectory scenarios.

The source rules are the already checked
[cwd-first lookup](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/config/src/project_trust.rs#L41-L95)
and [trust predicates](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/config/src/config_toml.rs#L596-L607).
They do not establish the active Desktop session's unobserved configuration.

## Minor findings and dispositions

| Finding | Disposition |
| --- | --- |
| A restricted later environment can fail the whole group load | Accept a bounded contract/fixture clarification. Earlier member and seeded global delivery must remain conditional when the permission context is unknown. The [source error branches](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs#L90-L103) substantiate it. |
| Python/native canonical case spelling on macOS may differ | Unverified implementation concern. The reviewer disclosed reliance on memory for Python behavior. Check a focused native-host fixture or primary source before selecting a correction; do not add ctypes merely from this suggestion. |
| Exclude all .env patterns and whole .ssh/.gnupg trees | Not adopted. This broadens the explicit closed exclusion scope and can exclude ordinary related files. Preserve disclosed limits; any broader scope needs a separate owner decision. |
| Compress repeated cwd-independent routes | Retain the closed R4 disposition. The reviewer labels this optional; full per-scenario rows and their cost are explicit. No new failure of the declared contract was shown. |
| Make executor-run task steps explicit | Accept an execution memo mapping each task's focused cases to fresh exact-executor RED, leader edits and separate fresh GREEN. Existing global prerequisites still control; leader-run tests do not replace them. |
| Add ledger publication to the owner-decision table | Accept a tracking correction for the already required public-ledger or independent-ID-fixture decision. No new gate is introduced. |

The owner requested a prepared new-session transition. Preserve the reviewed
plan, close this round and resume with the bounded correction above; do not
restart broad research or claim prior approvals carry forward. R7 has not been
started. No product implementation, product tests, publication or installation
has occurred.
