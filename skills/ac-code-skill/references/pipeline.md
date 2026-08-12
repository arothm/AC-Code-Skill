# The pipeline — Steps 0 through 6

The operating manual for a run. `SKILL.md` indexes these phases; this file is what
you actually follow. Every `{skill_dir}` below is the resolved absolute path to the
skill directory (see `SKILL.md` §Resolve the skill directory first) — substitute the
real value before you run a command or send a dispatch.

---

## Step 0 — Memory & docs

Check for `.ac-code-skill/memory.md`. If it exists, read it and the contents of
`.ac-code-skill/docs/` — together they are the project briefing every agent
inherits. If not, create `.ac-code-skill/` (git-ignored — add it to `.gitignore` if
absent) and seed `memory.md` after Step 1's detection pass.

`references/memory.md` has the layout, the single-writer rule, the *Agent
learnings* store, the privacy gate, and the template.

---

## Step 1 — Detect stack and scope (or enter greenfield)

**First check whether there is anything to review.** No source beyond a
README/LICENSE, or the user says they want to start from scratch → **greenfield**
(below), not detection.

Otherwise detect the stack language-agnostically from what is actually in the repo.
`references/stack-detection.md` covers signal files, frontend vs. backend, pulling
the *real* test/lint/build/e2e commands out of config, the dependency inventory
(manifests, lockfiles, the ecosystem's update/audit tooling), and scope selection
(working diff vs. whole tree — default to the diff for pre-commit/pre-merge asks).
It also flags **AI/LLM signals**, which decides whether `ai-engineer` runs.

Record verified stack + commands + dependency inventory + whether the repo has AI
features into memory, so no later agent re-derives them.

**On the first run, ask the two pre-review preferences — don't guess them**
(`stack-detection.md` §0b), batched into one short prompt:

- **private/internal or commercial/public** — drives the noindex vs. privacy-policy
  standards, and is passed to every agent as `standards.py --context <value>`.
- **should the fleet own DevOps** — only if a server may be in scope; SSH-key only,
  see the `devops` brief.

Record both in *Project preferences* and honour them thereafter without re-asking.
**Which docs the user wants is asked in Step 4**, not here.

---

## Step 2 — Select the agents and confirm

Match agents to the repo and the request. Launching all seven when three are
relevant burns tokens for no gain (rule 2). State your selection in a line or two
and let the user add or drop before you launch. A one-prompt full run auto-selects
every agent the stack supports.

---

## Step 3 — Review phase (parallel, read-only)

Launch every selected review agent **in a single turn** so they run concurrently —
this is the point of the fleet. Prefer the shipped agent definitions
(`ac-frontend`, `ac-backend`, `ac-security`, `ac-tester`, `ac-ai-engineer`), whose
tool lists enforce read-only by construction; fall back to a general-purpose
subagent with the rule stated in the prompt.

**Each agent reviews only the surface it owns.** Overlapping territory is what
makes a fleet cost more than one agent and find less.

### Assembling a dispatch

Every dispatch is:

1. `references/shared-rules.md` — the five rules, verbatim
2. the agent's block from `references/agent-roles.md`
3. its standards: `python "{skill_dir}/scripts/standards.py" --agent <role> --context <ctx>`
4. the detected `{scope}` and `{commands}`
5. the resolved `{skill_dir}`
6. this opening instruction:
   `python "{skill_dir}/scripts/recall.py" "<the agent's task>" --root .ac-code-skill --role <role>`
7. `references/testing-harness.md` for any agent that runs tests, a browser, or
   scanners — `tester` in full, `frontend` for the browser/viewport part, `security`
   for the scanner part, `ai-engineer` for evals

### `tester` runs the product, not just its suite

On any repo with a runnable UI, `tester` brings the app up
(`python "{skill_dir}/scripts/with_server.py" --help`) and drives it through an
**isolated browser MCP** — in-app/sandboxed first, Playwright second, *never* the
user's real logged-in Chrome unless they ask this run. Per primary screen:

- **Both viewports** — render and screenshot at **desktop 1440×900** and **mobile
  375×812**; judge the rendering, not just the DOM.
- **Every clickable element** — enumerate the interactive controls and click them.
  Report dead, misrouted, silently-failing, and keyboard-unreachable ones.
  Destructive controls only against disposable data.
- **Console + network on every action, including page load** — errors and warnings,
  4xx/5xx and never-resolving requests, and the **response bodies** (a `200`
  carrying `{"error": …}` is the failure a status check misses).
- **Evidence or it didn't happen** — screenshots, console dumps and the
  request/response log to `.ac-code-skill/log/<run-id>/screens/`; every claim cites
  its artefact.

No isolated browser MCP available → say so, fall back to the project's own e2e
suite, and label everything visual or flow-based **"unverified (no browser)"**. The
missing browser is itself a finding. Full protocol: `testing-harness.md` §Policy 3b.

### The sweeps that run here

`security` reports outdated/EOL/advisory dependencies alongside its audit;
`frontend`/`backend` report unused/stale dependencies plus dead code, dead files and
dead folders for their side of the tree. *Applying* dependency upgrades is `devops`,
approval-gated.

### Merging — don't staple

Format in `references/report-format.md`. Lead with a verdict and severity counts,
group by severity (not by agent), deduplicate shared root causes, keep `file:line`
and a concrete fix on every line.

- **Before promoting anything to `blocking`, a second agent already in the run must
  independently re-derive it from source.** Unreproduced findings ship as warnings
  labelled "single-agent, unconfirmed" — a blocking finding stops merges and
  deploys, so it carries the highest cost of being wrong.
- **Run variant analysis on every confirmed finding before you write the report.**
  A bug is rarely alone; see `report-format.md` §Variant analysis.
- Run the merged report through
  `python "{skill_dir}/scripts/redact.py" --in report.md --strict` and save it to
  `.ac-code-skill/log/<run-id>/report.md` — but **hold the chat copy until Step 4**
  delivers both together.
- Optionally emit machine-readable findings for CI:
  `python "{skill_dir}/scripts/to_sarif.py" --in report.md --out findings.sarif`.
- Consolidate Memory deltas into `memory.md` through the same privacy gate, and file
  *Improvements* under *Agent learnings*.

### Enhancements

Each agent returns up to **3** forward-looking enhancements (not defects). On a full
run, compile them into the report's *Recommendations & enhancements* section, ranked
by impact ÷ effort, deduped against the memory *Enhancement backlog*, and kept out
of the defect counts. On a **quick diff-check**, tell agents to skip enhancements and
omit the section — there the user wants defects only, not a roadmap.

**Do not hand the report to the user yet.**

---

## Step 4 — Ask which docs, generate them, then deliver the report

**Ask first.** Present the menu — **PRD** (product requirements), **BRD** (business
requirements), **FDD** (functional design), **TDD** (technical design), **ADRs**
(decision records) — one line each, and ask which the user wants. Record it in
*Project preferences* as `docs-types`. On every later run generate exactly that set
without re-asking; the user can change it any time, and "none" is a valid answer
that skips the phase. Ask here because the review has just established what the
project actually is.

**Then generate.** Dispatch `docs` to build or refresh the chosen set into
`.ac-code-skill/docs/` from memory + the merged report + the code, verified against
the source rather than invented. Deliverables are **Word `.docx`** via
`python "{skill_dir}/scripts/md_to_docx.py" --in-dir <staging> --out-dir .ac-code-skill/docs`,
with markdown sources staged under `log/<run-id>/docs-src/`.

**Then deliver the report — both places, in full.** Saved at
`.ac-code-skill/log/<run-id>/report.md` **and** rendered whole into the chat (not a
summary behind a file link), pointing at the refreshed `.docx` docs at the end.

---

## Step 5 — Fix phase (approval-gated), then re-review

Report first, then fix. Every fix traces to a finding in the merged report.

Offer fixes in **approve-able batches** ("all auto-formatting", "the 3 null-check
bugs", "the 2 security fixes", "remove the 4 confirmed-dead files/deps") rather than
one yes/no. Safe mechanical fixes first; behavioural changes (logic, test
expectations, security semantics, dependency removals/upgrades) need explicit
per-item confirmation.

Apply through the `ac-fix` agent (or yourself) **sequentially** — writes must be
ordered. Never touch anything the user didn't approve. Coverage gaps and AI/LLM
fixes are write actions too, and are gated the same way.

### Then every owning agent re-reviews its own fixes

Re-dispatch the agents whose findings were fixed — **read-only, in parallel**, scoped
to the fix diff, each carrying the findings it raised. Each returns a verdict per
finding:

- **fixed** — re-derived from current source, confirmed resolved
- **not fixed** — still reproduces (say how)
- **regressed** — the fix introduced a new problem (report at its own severity)

A verdict is a *re-derivation from the current source*, not a re-reading of the
diff. "The patch looks right" is not a verdict.

`tester` re-runs the suites **and** re-exercises the affected screens in the browser
— a UI fix confirmed only by a green unit test is not confirmed. Anything `not
fixed` or `regressed` goes to a second, smaller fix round. **Do not advance to
deploy with a failed verdict outstanding.**

Report the verdict table (`report-format.md` §fix-verification), then consolidate it
into memory — a finding confirmed `fixed` is no longer "present", so reconcile its
status everywhere it appears.

**Once the re-review passes**, regenerate the docs (same chosen set) so they reflect
the fixed, verified code. Tell the user which docs changed.

---

## Step 6 — Deploy (approved, with rollback), then verify by re-running

**Server ownership is consent-gated.** Check *Project preferences* →
`devops-consent`. `no` → no server work (in-repo pipeline/IaC review still happens).
`unasked` and a server may be in scope → ask once. On **yes**, take access **by SSH
key, never a password** (host + user + key *path*, verified with `ssh -v`, recorded
as pointers only). See `references/vps-operations.md`.

**Server operations.** `devops` audits **read-only first**
(`python "{skill_dir}/scripts/server_audit.py" --script`, run over SSH, output
captured and triaged with `--parse`) across access, network exposure, patching, TLS,
resources, services, containers, logging and backups — then proposes changes and
performs routine maintenance. Reversible routine operations proceed; anything
destructive, irreversible, or capable of severing access stops and asks. It never
weakens a security control to make something work.

**Deploy.** Per `references/deploy.md`: verify every precondition (security gate,
migration gate, rollback path), deploy via the project's own mechanism, health-check
the running version, and **roll back automatically** if it doesn't come up healthy.
This phase changes state, so it runs alone — never concurrent with the read-only
agents. Consolidate the *Infra & deploy* delta into memory afterwards.

### Post-deploy verification — one re-run to approve the shipped state

A green health check proves the app came up, not that the fixes work in production.
Once the deploy is healthy, run **Steps 1–3 again** against the deployed tree:
re-detect (the deploy may have changed versions or config), re-select the same
agents, re-review — with `tester` exercising the live flows against the **deployed
URL**, not localhost.

Produce `log/<run-id>/post-deploy-report.md` plus a chat copy, with one verdict:
**approved**, **approved with findings** (new non-blocking issues, listed), or **not
approved** (a blocking finding on the deployed build — say plainly whether a
rollback is warranted and let the user decide).

Three guards, because a pipeline that re-runs itself must terminate:

1. **Exactly once per deploy.** Its own output never triggers another pass.
2. **Read-only.** No fixes, no docs regeneration, no second deploy. New findings are
   reported; fixing them means the user starting a fresh cycle.
3. **Skipped when there is nothing to verify against** — no reachable deployed
   environment, or a deploy that rolled back (report the rollback instead).

---

## Greenfield bootstrap

Empty/near-empty repo + intent to start a project → **interview first, then
scaffold.**

Pool the intake questions from every role (end of `references/agent-roles.md`) and
ask them in **batched, prioritized rounds** so you learn as much as possible up
front and get the first build right: what and for whom, scope vs. non-goals,
frontend/backend shape, data model, auth & compliance, testing bar, deploy target.
Record the answers in memory's *Requirements & product*. Then:

1. Generate the initial docs (PRD/BRD/FDD/TDD, seed ADRs) into
   `.ac-code-skill/docs/` from the interview.
2. Propose a concrete stack + scaffold plan and confirm it. On an **aesthetic**
   brief ("premium minimal", "editorial", "make it feel expensive"), `frontend` runs
   `python "{skill_dir}/scripts/design_system.py" "<brief>" --persist -o .ac-code-skill`
   to compose a verified design system — pattern, style, colour tokens with
   **measured** WCAG ratios, typography with the correct import, anti-patterns,
   checklist — into `.ac-code-skill/design-system/MASTER.md`, with `--page <name>`
   overrides inheriting from it. Then apply `references/design-inspiration.md` for
   taste calibration, implemented originally in the project's own tokens and stack
   (learn principles, never clone). Record the direction in memory.
3. On approval, scaffold the project (structure, tooling, CI, a running skeleton)
   and seed `memory.md` with the chosen stack and commands.

From there the normal pipeline applies as the code grows.
