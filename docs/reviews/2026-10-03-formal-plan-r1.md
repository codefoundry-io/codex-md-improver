# Formal plan review — round 1

Date: 2026-10-03. Review ID: `codex-md-plan-20261003-r1`.
Basis digest: `56840ac831f08ea5b0eda4b8fe7c41a99a6c29e07728b019f23d7e5b08d7700e`.
Result: **INCOMPLETE; no admission**. All launched writers terminated; collection
validated the bound evidence. The complete custody was exported before managed
temporary-root cleanup. Local raw custody is excluded from public commits.

| Leg | Requested configuration | Result |
| --- | --- | --- |
| Claude | `claude-opus-5-5`, `xhigh` | Complete; MERGE WITH FIXES |
| Codex | native `gpt-6-astra`, `high`, no history fork | Complete; MERGE WITH FIXES |
| Google Pro | AGY `gemini-3.1-pro-high`, `high` | FAILED_TO_RUN; HTTP 400 schema rejection |
| Google Flash | AGY `gemini-3.8-flash-high`, `high` | FAILED_TO_RUN; same schema rejection |

Every leg had explicit web authorization. Requested settings are not hidden
runtime attestations. Read-only constraints were applied by the respective
routes; fingerprints establish unchanged bound source, not arbitrary host isolation.

## Accepted corrections

1. Root-marker precedence is field-specific: the pinned Codex loader excludes
   project configuration layers when selecting discovery markers. Custom
   non-project markers can exclude Git boundaries; no marker means cwd-only.
2. Original file volume and loader budget consumption differ for whitespace-only
   content. Preserve the owner-defined 90% physical-volume warning while
   reporting actual clipping, filtering and omissions separately.
3. Give semantic findings, rubric values, proposals and owner dispositions a
   validated, source-hash-bound input into a new enriched report. The scan alone
   cannot invent them; missing judgments are unassessed.
4. Name the pure recognition evaluator and its deterministic test module. Keep
   invalid delivery/control/schema results distinct from recognition failures.
5. Make publication/CI ordering feasible: local checks, concrete publication
   authorization, public remote/push, native GitHub macOS/Ubuntu CI, pre-merge
   review, final merge authorization, then authorized tag/release/installation.
6. Test Python 3.11 and 3.12 and the pre-import version guard. Define settings
   transport, partial/incomparable exit codes and readable external-link scope.
7. Default generated output outside targets; explicit opt-in is required for an
   output directory inside a target. Preserve existing inputs in either case.
8. Record target-guidance exposure and use synthetic probe identifiers without
   claiming they establish memory or inherited-instruction isolation.

Corrections 1–2 were checked against the [pinned official loader](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs).
The other corrections close concrete interface/ordering gaps in the reviewed plan.

## Rejected or narrowed proposals

- **800-line hard ceiling / L-class declaration:** rejected. The current applicable
  workspace cadence policy explicitly calls 500 net/300 novel-core lines planning
  guides, not hard limits. It permits justified growth and rejects arbitrary
  splitting or new approval solely because of line count. The review imported an
  older host rule outside the bound packet. The next packet will carry the current
  policy so this claim can be checked directly.
- **Private repository as the necessary CI solution:** not adopted. The owner
  requested a public repository. Explicit publication authorization before remote
  creation/push resolves ordering; pending authorization leaves dependent CI pending.
- **Range-level modeled reread total:** removed as unnecessary implementation
  detail. Full physical terminal-route totals, unique shared totals and separate
  loader counters remain required.

## Transport recovery and execution prerequisites

Both Google failures arose before a verdict: the provider-facing bound schema
retained `route.enum=["agy","gemini",null]` even with `const="agy"`. Google rejected
the null enum member. Diagnosis identifies a small producer-schema specialization;
canonical validation and the shared contract remain unchanged. A regression-tested
toolkit correction and a fresh four-leg basis are required before another admission
attempt. Successful siblings supply findings, not transferred approval.

The dedicated skill executor has a local exact-SOT definition and a workspace
registration. TOML/path validation passed, but the running native catalog rejected
the new role with `unknown agent_type`. This is not behavioral RED. The owner was
offered a one-task fresh-agent exception or continuation in a fresh session with
the dedicated role; no answer has yet been applied. The pass/fail aggregate-output
decision is also pending. These holds do not authorize silent substitutions.

MIT is selected. Product implementation, remote publication, merge, tagged release
and owner installation have not occurred. The plan has been corrected; another
formal round must judge its complete current content.
