---
name: log-experience
description: Records the user's roles, projects, metrics and corrections into the experience bank as facts and tagged resume bullets. Use when the user describes work they did, gives a number or detail, answers a bank question, or corrects a fact.
---

# Log experience into the bank

The bank is only as strong as its facts. Capture every detail the user gives, in their words where they carry meaning, so a later resume can use it without asking again. Format and focus tags: `bank/README.md`.

When `bank/profile.md` does not exist, run the `start-bank` skill first.

## Steps

### 1. Find or create the entry

Match the work to an existing file in `bank/roles/` or `bank/projects/` by org, title and dates. When none fits, create one from the format in `bank/README.md`, named after its `id`.

Done when one file is open for the work, with its front matter complete.

### 2. Record the facts

Add every concrete detail to `## Facts`: numbers, tools, scope, who used it, what changed because of it, the user's own part on a team project. Context that is not a fact goes in `## Notes`.

Record ownership on every team effort: who led it, who reviewed it, and the part the user owned. Ask before a fact says they developed, led or wrote something a team shared. When they narrow their credit, ask what they did own before you rewrite, and record both halves. Mark anything the user guessed or hedged with `(unconfirmed)`. Add each repo to `## Links` marked `(public)` or `(private)`; `gh api repos/<owner>/<name> --jq .visibility` tells which. Give a public one `link:` and the names a resume prints for it, as `bank/README.md` shows.

Done when every detail in the user's message sits in Facts or Notes of some entry.

### 3. Refresh the bullets

Write or rewrite 2 to 4 bullets in `## Bullets` from the Facts alone, each tagged, each one claim a different job might want. Lead with the strongest number the Facts hold, name the tool, and stop inside the limits of the One claim per bullet rule in `AGENTS.md`. Put new bullets first in the section.

Each claim in a bullet comes from one Fact. A bullet that joins two facts states how they connect only when a Fact does.

Done when every new Fact that earns a line has a bullet, and every figure in a bullet is in Facts.

### 4. Update the skill inventory

For each tool or skill in the new facts, add the entry id to its row under Backed in `bank/skills.md`. Move a skill from Listed to Backed when this entry is its first evidence.

Done when every tool and skill the new Facts name has this entry in its Evidence cell.

### 5. Close the loop

- Delete each open question in `## Notes` that the message answered.
- When the user corrects a claim, add a `## Avoid` rule for the wording they ruled out, in the format `bank/README.md` gives. Then grep the bank's bullets, `base/`, every job folder and the form answers in each `job.md` for the same claim. Fix the bank and `base/`, rebuild with `python3 scripts/build.py base` until it prints no `FAIL`, and tell the user which job folders and sent answers still carry the claim. Edit a job folder only when they name it.
- Ask one to three questions that would add a number or an outcome the entry still lacks: scale, time or money saved, people served, result.

Done when no answered question is left in Notes, every correction has its `## Avoid` rule, and the user has the next questions.
