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

**Accepted; applied in the resumed plan revision.** Separate the observed-plus-defaults
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
| Python/native canonical case spelling on macOS may differ | Substantiated in a bounded resumed-session native fixture; see evidence below. Require native-conformant canonical trust-key spelling and its fixture without mandating ctypes. |
| Exclude all .env patterns and whole .ssh/.gnupg trees | Not adopted. This broadens the explicit closed exclusion scope and can exclude ordinary related files. Preserve disclosed limits; any broader scope needs a separate owner decision. |
| Compress repeated cwd-independent routes | Retain the closed R4 disposition. The reviewer labels this optional; full per-scenario rows and their cost are explicit. No new failure of the declared contract was shown. |
| Make executor-run task steps explicit | Accept an execution memo mapping each task's focused cases to fresh exact-executor RED, leader edits and separate fresh GREEN. Existing global prerequisites still control; leader-run tests do not replace them. |
| Add ledger publication to the owner-decision table | Accept a tracking correction for the already required public-ledger or independent-ID-fixture decision. No new gate is introduced. |

## Resumed correction evidence

The current plan separates declared `observed_plus_defaults` calculations from
unseen live layers, accepts supplied trust at the actual cwd/Git fallback keys,
retains unresolved required facts and group-effective unknowns, and requires
the no-settings CLI fixture. Group delivery, exact-executor task mapping and
the existing ledger-publication decision are explicit. No broader exclusion
scope or route compression was adopted.

A fresh Sol investigation measured a mixed-case directory on a case-insensitive
macOS 26.6.2 volume using Python 3.12.13. Its lowercase alias existed and had the
same device/inode. Python `Path.resolve` and `os.path.realpath` retained the alias
case; native libc `realpath` returned stored mixed-case spelling. The exact
disposable fixture was removed. The pinned
[normalizer](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/utils/path-utils/src/lib.rs#L18-L21)
calls Rust canonicalization, whose Unix implementation corresponds to
[realpath](https://doc.rust-lang.org/std/fs/fn.canonicalize.html). Native equivalence
is source-backed inference; this did not execute the pinned Codex binary,
Ubuntu or product tests. It substantiates the contract correction, not a chosen
production FFI implementation.

The resumed native tool accepted the exact fresh behavior-executor role and
its child confirmed the configured SOT path. This is capability-only evidence;
behavioral RED/GREEN still requires actual source and scenarios. No prior
approval transfers to the corrected plan. Product implementation, product tests,
publication and installation have not occurred.
