# Report format

Two uses: (1) the shape each agent returns, and (2) the merged report you write.

## Severity levels

- **blocking** — must fix before merge: failing test, build break, security
  hole, a real bug.
- **warning** — should fix: risky pattern, missing error handling, meaningful
  code smell, missing coverage on changed logic.
- **nit** — optional polish: formatting, naming, minor duplication.

## What each agent returns

```
Summary: <one paragraph — did tests pass? overall health of this lane?>

Findings:   # defects only — something is wrong
- [blocking] path/to/file.ts:42 — <problem>. Fix: <concrete suggestion>.
- [warning]  path/to/other.py:88 — <problem>. Fix: <concrete suggestion>.
- [nit]      path/to/thing.jsx:12 — <problem>. Fix: <concrete suggestion>.

Enhancements:   # optional, ≤3 — nothing is broken, but here's a better way
- [impact:H effort:S] path/or/area — <enhancement>. Why: <concrete benefit>.
- [impact:M effort:M] path/or/area — <enhancement>. Why: <concrete benefit>.

Memory delta:
- <durable fact worth persisting — a convention, a working command, a recurring
  issue class. Omit transient run output. Empty is fine if nothing new.>

Improvements:
- <optional: a refinement to how THIS agent should work next time — see
  shared-rules.md rule 5. The coordinator files these under Agent learnings.>
```

**Findings vs Enhancements** are two different things: a *finding* is a defect
(something is wrong, severity-graded), an *enhancement* is a forward-looking
improvement (nothing is wrong, but here's a better way) — capped at 3 per agent,
tagged impact × effort, and kept out of the severity counts. The **Memory delta**
is how each agent feeds the shared memory without writing it directly; the
**Improvements** block feeds the self-improvement store. The coordinator collects
all of these, folds enhancements into the report's *Recommendations* section (and
the memory enhancement backlog), and consolidates deltas + improvements into
`.ac-code-skill/memory.md` (single writer — see `memory.md`). Keep them durable
and terse; per-run findings belong in the report, not in memory.

## The merged report (you write this)

**Deliver the report in two places, both times.** Save the full report to
`.ac-code-skill/log/<run-id>/report.md` **and** render the full report into the
chat — not just a summary. The file is the durable artefact; the chat copy is what
the user actually reads, and burying it behind a "see the file" link is a worse
experience. (For a very large report, lead the chat copy with the verdict + counts
so the top is skimmable, then the full grouped findings below.) Use this template
for both: 

```markdown
# AC Code Skill — Review Report

**Verdict:** <PASS / NEEDS WORK / BLOCKED>
**Counts:** N blocking · M warnings · K nits
**Scope:** <diff vs main | full repo> · **Agents:** <which ran>

## Blocking
_Every entry here was independently confirmed by a second agent (shared-rules
rule 1). Anything one agent found but another couldn't reproduce belongs in
Warnings, labelled "single-agent, unconfirmed"._
- **<short title>** — `file:line` (from: <agent>, confirmed by: <second agent>)
  <problem>. **Fix:** <suggestion>.

## Warnings
- **<short title>** — `file:line` (from: <agent>)
  <problem>. **Fix:** <suggestion>.

## Nits
- `file:line` — <problem>. Fix: <suggestion>.

## Test & tooling results
- frontend tests: <pass/fail + summary>
- backend tests: <pass/fail + summary>
- linters/type-checkers: <summary>

## Live product exercise   (from `tester` — what was actually clicked and watched)
_Omit only when there is no runnable UI. If no browser was available, say that here
instead of leaving the section out — a silent omission reads as "nothing to report"._
| Screen | Desktop 1440 | Mobile 375 | Controls tried | Dead/broken | Console | Network |
|---|---|---|---|---|---|---|
| <route> | ok / issue | ok / issue | <n> | <n> | <n err / n warn> | <n failed, n error-body> |
- **<screen> — <what broke>** — `<control or request>` (artefact: `log/<run-id>/screens/<file>`)

## Standards compliance
_From `data/standards.csv`, checked on every run that touches their surface.
List each standard as met / violated / not-applicable — a standard silently
skipped is indistinguishable from one that passed._
| Standard | Owner | Severity | Status | Evidence |
|---|---|---|---|---|
| <id> | <agent> | <blocking\|warning\|nit> | met / VIOLATED / n/a | <how it was verified> |

## Dependency & dead-code health
- Outdated / EOL / advisory deps: <summary + which agent found them>
- Confirmed-unused deps / dead code / dead files / dead folders: <summary>

## Suggested fix batches
1. <batch the user can approve as a unit, e.g. "auto-formatting only">
2. <e.g. "the 3 null-check bugs">
3. <e.g. "the 2 security fixes — behavioral, confirm each">

## Recommendations & enhancements   (forward-looking — NOT defects)
_Nothing below is broken; these are where investment would pay off. Ranked by
rough ROI (impact ÷ effort). Advisory — implementing one is approval-gated._
- **[impact:H · effort:S]** <area> — <enhancement>. Why: <concrete benefit>. (from: <agent>)
- **[impact:M · effort:M]** <area> — <enhancement>. Why: <concrete benefit>. (from: <agent>)
- <omit this whole section on a quick diff-check; include it on a full run / cycle>

## Docs
- Generated/updated as Word `.docx` at `.ac-code-skill/docs/`: <which docs>.
```

## Variant analysis — run it before you write the report

A verified defect is a **pattern**, and patterns repeat. Between confirming a
finding and writing it up, sweep the codebase for the same shape.

1. **Abstract the defect into a searchable construct.** Not "`total` is unchecked on
   line 42" but "a numeric parse whose `NaN` case is unhandled". Not "this route
   skips `requireAuth`" but "a router registration without an auth middleware".
2. **Grep the construct, across the whole tree** — not just the diff. Variants
   outside the scope still get reported (as `warning` at minimum): the user needs to
   know the fix is incomplete, even if this run won't touch them.
3. **Confirm each hit** the same way you confirmed the first. A grep hit is a
   candidate, not a finding.
4. **Report them together.** One entry, one root cause, every `file:line` listed:

   ```
   - **Unhandled NaN from user-supplied quantity** — 4 occurrences
     `cart/total.ts:42` · `checkout/summary.ts:88` · `api/order.ts:31` · `admin/bulk.ts:117`
     (from: backend, confirmed by: security · variant sweep: `parseInt(` + no `isNaN`)
     <problem>. **Fix:** <one fix that covers all four>.
   ```

5. **Record the sweep even when it finds nothing.** "Variant sweep: `parseInt(`
   across `src/` — this is the only unguarded occurrence" tells the reader the
   question was asked. Silence reads as *not checked*.

Why this is not optional: a fix applied to 1 of 5 occurrences closes the finding in
the report while leaving four live in the code. That is **worse than never having
found it**, because the report now certifies the problem as handled. When a variant
sweep is impractical (no grep-able construct, generated code), say so explicitly
instead of skipping it silently.

## Machine-readable output (SARIF) — optional, for CI

`scripts/to_sarif.py` converts the merged report's findings into SARIF 2.1.0 so they
can be uploaded to GitHub code scanning or gate a CI job:

```bash
python "{skill_dir}/scripts/to_sarif.py" --in .ac-code-skill/log/<run-id>/report.md \
    --out .ac-code-skill/log/<run-id>/findings.sarif
python "{skill_dir}/scripts/to_sarif.py" --in report.md --out findings.sarif --fail-on blocking
```

It parses the `- [severity] path:line — problem. Fix: …` finding lines (the shape
this file specifies), maps `blocking → error`, `warning → warning`, `nit → note`, and
`--fail-on` exits non-zero when a finding at or above that severity is present. The
markdown report stays the human deliverable; SARIF is an additional artefact, never a
replacement.

## The fix-verification report (Step 5, after the fixes land)

Each agent re-reviews **its own** fixes and returns a verdict per finding; you merge
them into one table, save it to `.ac-code-skill/log/<run-id>/fix-verification.md`,
and show it in chat. Deploy does not start with a `not fixed` or `regressed` row
outstanding.

```markdown
# Fix verification — run <run-id>
**Applied:** N fixes across M findings · **Verified:** X fixed · Y not fixed · Z regressed

| Finding | file:line | Fix applied | Verdict | Verified by | Evidence |
|---|---|---|---|---|---|
| <short title> | `path:42` | <what changed> | **fixed** | <agent> | <test/artefact> |
| <short title> | `path:88` | <what changed> | **not fixed** | <agent> | <how it still reproduces> |
| <short title> | `path:12` | <what changed> | **regressed** | <agent> | <the new problem + severity> |

## Next round   (only if anything is not fixed / regressed)
- <what needs re-fixing, and whether it needs the user's approval again>
```

A verdict is a *re-derivation from the current source*, not a re-reading of the
diff — the same rule that governs carried findings (shared-rules rule 1). "The patch
looks right" is not a verdict.

## The post-deploy verification report (Step 6, once)

```markdown
# Post-deploy verification — run <run-id>
**Verdict:** APPROVED / APPROVED WITH FINDINGS / NOT APPROVED
**Deployed:** <ref> to <environment> · **Verified against:** <deployed URL>
**Health:** <status> · **Rollback:** <not needed | performed, why>

## What was re-checked
- <agents re-run, and the live flows exercised against the deployed build>

## New findings on the deployed build
- **[severity] <title>** — `file:line` or `<endpoint>` — <problem>. **Fix:** <suggestion>.

## Recommendation
- <ship as-is | roll back, and why — the user decides; this pass changes nothing>
```

This pass runs **once**, is **read-only**, and never triggers another one. Fixing
what it finds means starting a fresh cycle.

**Merge — don't staple.** Lead with the verdict and counts; group findings by
severity, *not* by agent; deduplicate shared root causes into one entry that
lists the agents that saw it; keep `file:line` + a concrete fix on every line.
The point of the fleet is one coherent report, not a pile of per-agent outputs.

**Run the report through the privacy gate before saving it.** `python
{skill_dir}/scripts/redact.py --in report.md --strict` — a review artefact is a durable file
that gets shared, and it is exactly where a leaked credential or a real person's
address should not end up (see `memory.md`). Keep `file:line` paths and public
URLs; they're PASS-classed so findings stay reproducible.

**Keep enhancements out of the defect counts.** The verdict and blocking/warning/
nit counts are about *defects only* — an enhancement is never a `blocking`. Rank
the Recommendations by impact ÷ effort, dedupe against the memory enhancement
backlog (don't re-list something already done or declined), and cap the whole
section to the strongest ~8 so it stays a shortlist, not a wishlist.
