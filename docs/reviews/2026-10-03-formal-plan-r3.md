# Formal plan review — round 3

Date: 2026-10-03. Review ID: `codex-md-plan-20261003-r3`.
Basis digest: `103aa371dcaf3cd57425666d63e7608d683eeff57b2ac88f8c212068750d05bc`.
Result: **BLOCKED; no admission**. All four legs completed and collection
validated the bound source/toolkit evidence. Custody was exported and the exact
managed temporary root was removed through the official lifecycle.

| Leg | Requested configuration | Result |
| --- | --- | --- |
| Claude | `claude-opus-5-5`, `xhigh` | MERGE WITH FIXES; 1 must-fix and 8 minor findings |
| Codex | native `gpt-6-astra`, `high`, no history fork | MERGE WITH FIXES; 1 must-fix finding |
| Google Pro | AGY `gemini-3.1-pro-high`, `high` | SAFE TO MERGE; no findings |
| Google Flash | AGY `gemini-3.8-flash-high`, `high` | SAFE TO MERGE; no findings |

Web was authorized for every leg. R3 preflight observed AGY 1.2.16 and Claude
2.1.288; these are observations, not new equality requirements. Requested models
and efforts do not attest hidden runtime values. Previous approvals do not transfer.

## Accepted defects and bounded corrections

- **Scenario identity:** two sibling cwds can share the same loader record while
  resolving a cwd-relative link differently. Preserve every member cwd/scenario
  through graph expansion and terminal reporting, including equal physical
  targets. Add distinct-target and shared-target sibling fixtures. A separate
  Sol check confirmed the correction provided scenario membership survives into
  terminal rows. Plain paths also retain a distinct cwd-relative candidate.
- **Global versus project loading:** the old unqualified empty-override rule was
  wrong for global guidance. Independent primary-source verification found the
  [global provider](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/codex-home/src/instructions/mod.rs#L36-L102)
  and [home resolver](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/utils/home-dir/src/lib.rs#L12-L57)
  at the same pinned commit. The plan now separates selection, trim/decoding,
  warning-and-continue errors, cached-refresh uncertainty and the absence of a
  cap in that provider from project-loader semantics. Add dedicated global/home
  fixtures and link them to AG03/AG08. No session-cache emulator is introduced.
- **Filename selection:** match filesystem metadata lookup and pinned fallback
  filtering, with measured filesystem case behavior. The pinned project's
  [candidate selection](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs#L226-L279)
  supports this correction; macOS alone does not prove case insensitivity.
- **Cross-run resolution:** define stable anchors and explicit before-hash/finding
  references with after-side evidence. Validate cross-run references when both
  reports are available to compare. Test actual successful resolution as well
  as disappearance without evidence; no new history database is needed.
- **Coverage wiring:** derive expected IDs from the independent checked-in owner
  ledger and verify tags beside shipped conditional rules. This catches omitted
  wiring while retaining the distinction from semantic assessment quality.
- **Resource interruption:** expose the previously promised opt-in route cap,
  keep incomplete manifests and flushed route prefixes, and distinguish catchable
  interruption from an uncatchable kill. No default traversal cap is introduced.
- **Completion details:** supplement the real older-interpreter smoke with a 3.9
  parse check, and carry the unresolved aggregate input/workflow contract into
  the release checklist. The current Apple bundled-version claim was not adopted
  from secondary search summaries.

## Narrowed suggestion

The credential-excerpt concern is handled through explicit metadata-only frontiers
for known credential/authentication/private-key sources and a no-secret-excerpt
rule. Do not add a generic secret scanner, claim that other content is secret-free,
or silently replace the approved external-reference scope with a new allowlist.
These frontiers remain visible as partial coverage instead of disappearing.

## Remaining execution dependencies

The structured aggregate-output choice and exact dedicated behavior-executor
availability remain unresolved. They are not waived by a review verdict. Product
code, behavior RED/GREEN, public publication and installation are still absent.
The corrected complete plan needs a fresh full-roster review.
