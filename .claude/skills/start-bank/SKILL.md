---
name: start-bank
description: Fills an empty experience bank from the user's existing resume or an interview, then builds their first base resume. Use when `bank/profile.md` does not exist, when the user shares a resume to import, or when they ask to start or set up their bank.
---

# Start the bank

The bank starts from what the user already has: a resume, a LinkedIn export, or their own account of their work. Every fact in it comes from the user. Format: `bank/README.md`. `examples/` shows each file filled in for two made-up people; read the one nearer the user's field for format, and take no fact from either.

## Steps

### 1. Collect the sources

Ask the user for every resume they have, as a PDF, a document or pasted text, and for their LinkedIn profile text if it holds more. Read a PDF with `pdftotext -layout <file> -`, and ask for pasted text when a file is in a format you cannot read. Save each one's text as `bank/sources/resumes/<YYYY-MM>-<label>.txt`, with a label such as `resume` or `linkedin`, dated the month the user wrote it, or the month they shared it when it carries no date. With no resume, interview them: each job with its employer, title, city and months, then each project.

Done when every source the user offered is saved, or the interview has covered every role they named.

### 2. Write the profile

Write `bank/profile.md` in the format `bank/README.md` gives. Copy the name, phone, email, links, education, licenses, certifications, languages and honors from the newest source. Credentials after the name, such as RN or CPA, go under Licenses or Certifications and stay off the Name line. Ask for each of these the sources lack: where they live now, as a resume in their country prints it, the graduation month, and the form answers under `## Application answers`. Leave out a line they do not have, such as a GPA or a portfolio, and write a form answer nobody has given as `ask the user`.

Done when every Contact line is the user's own, each from a source or their answer.

### 3. Write one file per role and project

For each role and project in the sources, write a file in `bank/roles/` or `bank/projects/`:

- Front matter from the source: org, title, location, and months as `YYYY-MM`. Where the source gives only a year, write the year and ask for the month.
- `## Facts`: split each source bullet into plain statements, one number or claim each. Copy every number as written; what the user's own resume states is confirmed. Mark `(unconfirmed)`, on its own line, only what the user hedges or cannot recall.
- `## Bullets`: one for each Fact that earns a line, each one claim built from Facts, inside the limits of the One claim per bullet rule in `AGENTS.md`.
- `tags:` in the front matter and a tag on each bullet, naming the kind of work in a word or two. Reuse a tag before coining one.
- `## Links`: each page the source names where a reader can check the work, marked `(public)` or `(private)`.

A role the source lists with no bullets still gets its file, with front matter and no bullets.

Record who led each team effort and the part the user owned. Ask before a fact says they led or built something a team shared.

Then replace the placeholder row under `## Focus tags` in `bank/README.md` with the tags these entries use, each with what it covers.

Done when every role and project in the sources has a file, and every bullet in the sources traces to a Fact.

### 4. Write the skill inventory

Write `bank/skills.md`. A skill goes under Backed when a role or project fact shows it, with those entry ids as its evidence, whether or not the source lists it as a skill. A skill the sources list with no fact behind it goes under Listed.

Done when every skill the sources name sits in one of the two sections.

### 5. Ask for the numbers

A source resume leaves out most of what makes a bullet strong. For each role, ask the one to three questions whose answers would add scale or outcome: how many people, customers, records or dollars, how long it took before and after, who it served. Ask one role at a time, newest first. Log each answer into Facts, then refresh that entry's bullets. An entry the user has no numbers for keeps its facts as they are, with the open questions under `## Notes`.

Done when each role has been asked about once and every answer is in its Facts.

### 6. Build the base resume

Copy `template/blank.tex` to `base/resume.tex`, replace every placeholder with the bank's facts, and delete any line or section the bank has nothing for, such as GitHub or Projects: the contact line from the profile, Education, Skills rows drawn from `bank/skills.md`, the Licenses, Certifications and Languages rows from the profile, each role as a `\job` line with its strongest bullets, newest first, then projects. Put Education after Professional Experience unless the user is a student or a recent graduate. A user with no paid roles yet gets Education, Skills and Projects, and no empty section. Apply the Rules in `AGENTS.md`. Then build:

```bash
python3 scripts/build.py base
```

Each `FAIL` and `warn` names its fix. Loop until the report shows no `FAIL`, and no `warn` but one only a new fact can fix. For a job with no line that reaches its dates, extend one bullet with another detail of the same claim from that entry's Facts; when Facts hold none, change the first line to `\documentclass[inlinedates]{resume}`, which prints every date after a bar. When the page stays under full because the bank is thin, tell the user which roles need more facts and stop there; the page fills as they log more. Open the PDF, look at the page, and check it: one page, the contact details on one or two lines under the name, every role line ending in its dates.

Done when `base` builds with no `FAIL`, or the one left needs a fact only the user has and they have been asked for it, and every `warn` left is one only a new fact can fix.

### 7. Report and commit

Tell the user, as a short list: the PDF path, how many roles, projects and skills the bank holds, each `(unconfirmed)` fact waiting on them, and the open questions per role. Then commit `bank/` and `base/`, after the privacy check under The bank is private in `AGENTS.md`.

Done when the bank and the base resume are committed, or the user has been told why they are not.
