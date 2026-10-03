# Formal plan review — round 4

Date: 2026-10-03. Review ID: `codex-md-plan-20261003-r4`.
Basis digest: `a0666dfaca40a2649a008c606143e09fd21e5812bf81372ca02cb1ad2cde89d5`.
Result: **BLOCKED; no admission**. All four writers completed; collection verified
bound integrity and no missing leg. Custody was exported before official cleanup.

| Leg | Requested configuration | Result |
| --- | --- | --- |
| Claude | `claude-opus-5-5`, `xhigh` | MERGE WITH FIXES; 2 must-fix and 7 minor findings |
| Codex | native `gpt-6-astra`, `high`, no history fork | SAFE TO MERGE; no findings |
| Google Pro | AGY `gemini-3.1-pro-high`, `high` | SAFE TO MERGE; no findings |
| Google Flash | AGY `gemini-3.8-flash-high`, `high` | SAFE TO MERGE; no findings |

Every leg had web authorization. No prior approval transfers to changed source.

## Accepted corrections

- Add a source-hash/span-bound occurrence classification decision to reference
  resolutions, not only a base/target decision. A verified informational/example/
  output classification can close uncertainty while retaining the occurrence
  inventory. CLI tests cover completion after dismissal and stale-input refusal.
- Distinguish hypothetical cwd inventory from reference traversal: Git management
  directories are not ordinary member cwds; an explicit read dependency into Git
  storage still has a visible reference-coverage limit. State directory alias and
  outside-scope frontier handling; ignored/vendored ordinary directories remain.
- Define untrusted/unknown project inclusion and metadata-probe failure behavior.
  Keep a positive-budget environment's full discovery before read-budget accounting.
  Initial zero budget and exhausted outer environment budget skip discovery.
- Derive the known authentication source from the resolved Codex home, including
  nondefault homes and physical aliases.
- Specify the output flag in the CLI and the output creation/progress lifecycle.
  Run-owned files cannot become input. Late overlap with a linked input directory
  has explicit opt-in/refusal behavior; existing earlier reports remain inputs.
- Permit an evidence-bound local resolution despite an unrelated denied branch;
  disappearance in an uncovered area remains insufficient and the overall result
  remains partial. Define the scenario root as marker root or cwd fallback.
- Give the skill an eligible host-permitted temporary output path and state its
  retention limits. An unavailable output path never authorizes broader target reads.

## Rejected or narrowed proposals

**Prune ordinary ignored/vendored directories or require fewer terminal rows:**
not adopted. The selected task asks for complete accessible instruction scopes
and terminal-route reporting. Directory-count multiplication is an explicit output
cost, handled by streaming and owner-selected caps; the plan does not promise
bounded total runtime/output. The actual Git-inventory ambiguity is corrected
separately. Scope pruning or lossless route-set compression could be a later
optimization, but neither is necessary to restore the stated output contract.
The prior cwd fix must continue preserving every scenario and its routes.

**Do not probe files after read-budget exhaustion:** only partly accepted. The
[pinned source](https://github.com/openai/codex/blob/ff6aec96948b70d94983af2641a6b67c94faeff5/codex-rs/core/src/agents_md.rs#L124-L166)
discovers candidate paths before reading when the initial environment budget is
positive. Later reads can be skipped even though metadata was already probed.
Fixtures now preserve that order; the reviewer's broader suggested short-circuit
would itself diverge from the source.

The fixes are static contract corrections, not product test results. The selected
aggregate-output and exact behavior-executor choices remain unresolved. No product
implementation, publication or installation is claimed. A new full-roster round
must judge this corrected basis.
