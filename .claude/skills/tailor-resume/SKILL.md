---
name: tailor-resume
description: Writes a one-page resume for one job post from the user's experience bank, choosing the bank bullets that best match the post's keywords. Use when the user pastes or links a job post, or asks for a resume aimed at a role or company.
---

# Tailor a resume

Every resume is a selection from `bank/`, reworded toward the post. The post decides what to show; the bank decides what is true.

A resume gets through a screen when three readers succeed: a parser files every field, a search finds each backed term in the post's spelling, and a grader finds each requirement proven. The build checks the first two and step 5 rehearses the third. A scanner's match percent measures none of them, so no term is repeated and no number dropped to raise one.

When `bank/profile.md` or `base/resume.tex` is missing, run the `start-bank` skill first. When `python3 scripts/build.py base` prints a `FAIL`, clear it there first, since a tailored copy inherits it.

## Steps

### 1. Open the job folder

Create `jobs/<YYYY-MM-DD>-<company>-<role>/` with today's date and short kebab-case names, for example `jobs/2026-01-12-northwind-data-engineer/`. Write `job.md` from the template below with the post text pasted verbatim, section headings included: they are how a reader, and the screen rehearsal, tell a required line from a preferred one. If the user gave only a link, fetch the page and paste its text. If they pasted the text alone, ask for the posting link, so the tracker can link the post and the apply page. When the post names an application deadline, write it as `- Deadline: <YYYY-MM-DD>, <what the post says>`.

Copy each application question the user shares into `## Form questions`, with the answer from `## Application answers` in `bank/profile.md`, or "ask the user".

Done when `job.md` holds the full post, its source link, the generator version, any deadline, and the form questions or "none shared".

### 2. Pull the keywords

Read the post and list every hard skill, tool, certification, domain term and the job title, in the post's own spelling. Each goes to one of three places:

- `keywords.txt`, when the bank backs it: a Backed row in `bank/skills.md`, a fact in a role or project file, or a license or certification in `bank/profile.md`.
- A Skills row and `## Gaps`, when `bank/skills.md` holds it only under Listed: print it in the post's spelling, and say under `## Gaps` that no logged work backs it.
- `## Gaps` alone, when nothing in the bank holds it.

Start each `## Gaps` line with the term in the post's spelling, then a colon and the reason. The build fails a bullet that prints a term from this list, or a Listed skill, unless that entry's Facts state it.

A term the post uses only in its company or benefits text stays out of all three.

Write `keywords.txt` one entry per line, in this format; a line starting with `#` is a comment:

- `title: <the post's job title>` once, at the top, without the team or place a post adds after a comma or a dash.
- `!` before a term from the basic, minimum or required qualifications that the bank backs. A `!` term not on the page in its exact form fails the build; a near form, an alias or half a pair is not enough. When the post requires a bachelor's degree, add `!Bachelor` and the major as the post writes it, such as `!Economics`. The Education row proves the degree lines and the Licenses and Certifications rows prove a credential; a bullet proves every other `!` term.
- A plain line for every other backed term, in the post's surface form: its spelling, singular or plural, and word order.
- `Long Form (ACR)` when the post spells both forms or the acronym means something else too, as `Key Performance Indicator (KPI)`. The page needs both.
- `Post Form | Bank Form` when the bank spells a backed term differently, as `Microsoft Excel | Excel`. The page should carry the post's form. A Skills row prints it only once `bank/skills.md` lists it as an alias in parentheses, as `Excel (Microsoft Excel)`, so ask the user before adding one.

List the 4 to 6 core terms first, required before preferred: the required ones, then the terms the post repeats. Leave out traits the post lists, such as communication, along with possessives and stopword-only terms such as IT. A requirement the post grades, such as managing people, is a term like any other. Shorthand the post never uses goes in only after the user approves printing it.

Every line is a term the post itself writes. The build compares the list with `## Post` and warns on a term the post never uses, and on a Backed skill the post names that the list skips.

Done when every required and preferred qualification in the post, other than a trait, sits in `keywords.txt` or `## Gaps`.

### 3. Write `resume.tex`

Copy `base/resume.tex` into the job folder and reshape it:

- **Bullets.** Read the role and project files whose tags or Facts match the post's keywords. A reworded bullet may change words, order and emphasis; every number, tool and outcome in it must appear in that entry's Facts. A bank bullet is a draft, so check each claim in one you copy against Facts too, ownership verbs such as developed, led and wrote first. The build fails wording an entry's `## Avoid` section rules out. Give the most relevant role the most bullets and the least relevant 2, as many as fill the page: about 20 from a deep bank, and what it holds from a thin one. Keep every role so the timeline has no holes; a role the bank holds no bullet for prints its line alone. When a long career cannot fit, print the roles of the last 10 to 15 years in full, each older one as its line alone, and ask the user before leaving any role out.
- **Evidence and spread.** Prove each `!` term in a bullet of a dated role whose Facts back it, the most recent first, and use a project bullet only when no role fact does; the degree and credential lines are proved by their own rows. Prove each core term in the most recent role whose Facts back it, and name it in one more such role when a line is free, once per bullet. When the post asks for a tool or a language, name it in the bullet where it did the work.
- **One claim per bullet.** Lead with the strongest number in Facts, such as scale, users, money, time or coverage, then name the tool and who it served. Put the measured result first where Facts give one, as "Saved \$<amount> a year by <what was done>". Let a bullet run one line where the claim fits, and two when the second line carries a tool, a number or an outcome. A bank bullet that joins two claims becomes two bullets, each with its own fact.
- **Verbs.** Open each bullet with the plain verb for what that bullet did: Cut, Grew, Launched, Replaced, Ran, Trained, Negotiated, Saved. The verb matches the user's part in Facts: Led only where they directed people or held the whole effort, Supplied or Added where someone else led. No verb opens more than two bullets.
- **Earn the line.** A bullet stays when it has a number, a named audience or a before and after, makes a claim no other bullet makes, says what changed and not what the thing is, and stands alone. Cut one that does not, and move a keyword it held to a Skills row. Fill the page with bullets that pass.
- **Titles and dates.** Write each role as `\job{org}{title}{location}{Mon YYYY - Mon YYYY}`, with every field copied from the bank file's front matter, and the location braces left empty when the file has none. Write each date as `Mar 2016 - Present`, the one form the build reads. Print months on both ends where the bank has them, and the year alone where it holds only a year; the build fails a month the bank does not back. Copy each project's name from its `# ` heading. Keep a title such as Intern as the bank has it, and keep projects under Projects. Write "N years of X" only when Facts state it.
- **Top of the page.** Keep the contact block as `base/` has it: the name, then the location, phone, email and profile addresses from `bank/profile.md` on one line, or two when they do not fit. The name prints alone: a credential such as RN or CPA goes in the Licenses or Certifications row, long form first, as "Registered Nurse (RN)". The first heading follows the contact details directly, with no headline or summary between. Write the degree level in words, as "Bachelor of Arts in History".
- **Links.** Wrap the first mention of each name an entry's Links give after `link:` in `\href{url}{name}`, as `\project{\href{<url>}{<Name>}}{...}{...}`. Link the name, never a printed URL, and leave a `(private)` link off the page. When a name is public but has no `link:`, add one to the bank first.
- **Projects.** Role bullets get the space first, and a project stays while the page has room for it. When a role bullet that earns its line needs the space, cut the project that holds no keyword and no award first. Use `\project{Name}{award or context}{date}`.
- **Skills.** Rewrite the labelled Skills rows to lead with the backed keywords from `keywords.txt`, each once in the post's spelling, then the next most relevant. Print every Listed skill the post names, in a row and never in a bullet. Every item is a term the bank holds: a Backed or Listed skill, an alias the inventory gives in parentheses, or a word in some entry's Facts. A row labelled Languages or Awards may also print what `bank/profile.md` lists under `## Languages` and `## Honors`. A required term also appears in a bullet. Relabel the rows when that reads better for the post.
- **Headings.** Keep the headings `base/` gives, each one plain topic, such as Education, Skills, Professional Experience and Projects. The build reads a section by its macros, so a heading may say what fits the user, as Clinical Experience, Volunteer Work or Research do. Licenses and Certifications are rows of the Skills section, each under its own label, and every item in them comes from `bank/profile.md`. Keep the order of sections `base/` gives.
- **Wording.** Verb first, past tense for finished roles, present tense for current ones. Spell an acronym out once where the post does. Write symbol terms literally, as C++ and A+. Escape `&`, `%`, `$`, `#` and `_`. Commas where a dash would go. Use only the class's macros, because `\textsc`, `\texttt`, tables, columns, images, colors and size commands change what a parser extracts.

Done when `resume.tex` holds every role with its bank dates, and each claim in each bullet traces to its entry's Facts.

### 4. Build until clean

```bash
python3 scripts/build.py jobs/<folder>
```

The build compiles the PDF and checks it the way a parser and a keyword search read it, and against the bank. Each `FAIL` and `warn` names its own fix. Loop on edits until the report shows no `FAIL` and every `warn` is fixed, or recorded under `## Build notes` in `job.md` with its reason: the bank cannot fix it, or the fix does not fit the page. When the page cannot hold every backed keyword, leave out the ones lowest in `keywords.txt`. To lose space, cut a project before a role bullet, then cut the weakest bullet. Add a bullet only when it earns its line. A `FAIL` is never recorded and left: when only a new fact can clear it, stop and tell the user which fact.

These need more than the message says:

- A figure the Facts do not state, a Skills row item the bank does not hold, or a word no list knows: the claim is not in the bank yet. Reword with what the bank holds, or ask the user and log it through `log-experience` first.
- A `keywords.txt` term the saved post never writes, when the term came from a call or the employer's own pages: it stays, under `## Build notes`.
- A job line that wraps before its dates: shorten the location to a true shorter form first, such as the city alone; it is the one field the build does not match to the bank. If it still wraps, ask the user for a short form of the org or title and log it in the bank.
- A job with no line that reaches its dates: extend one bullet with another detail of the same claim from that entry's Facts, such as the tool, the scale or who it served, until its first line passes where the dates begin. When Facts hold no such detail, change the first line to `\documentclass[inlinedates]{resume}`, which prints every date after a bar, and ask the user for the detail.
- Text past the right margin: reword the source lines the FAIL names so TeX can break the line. A long hyphenated or linked term is the usual cause.

An `info` line reports and needs no fix, except one that names an action, such as listing a shortfall in years under `## Gaps`.

Then open the PDF, look at the page, and check five things: one page, the contact details on one or two lines under the name, every role line ending in its dates, no text past the right margin, and no bullet ending on a stray word.

Done when the build prints no `FAIL`, every `warn` is fixed or under `## Build notes`, and the page passes those five checks.

### 5. Rehearse the screen

Follow [`references/screen.md`](references/screen.md). A fresh subagent that sees only the post and `.build/resume.raw.txt` parses the page into fields and grades each requirement met, unclear or not met. Fix what the bank can fix, rebuild, and record the grades under `## Requirements` in `job.md`.

Done when every requirement the bank backs is graded met or sits under `## Build notes` as not fitting the page, every other one sits under `## Gaps`, and the parsed fields name the same employers, titles, months and years, school and degree as the bank.

### 6. Draft the form answers

When the user asks for help with a free-text question, such as "Why <company>?":

- Write every answer in the user's voice. Ask what they want to say before drafting, unless their message already says, then build the answer from their points in the words they used: first person, short plain sentences, and only the tools a reader needs to follow it.
- Take every fact from the bank, as the resume does, and keep each claim in step with the page. A new fact the user gives for an answer goes into the bank first.
- Count the words with `wc -w` against the range the question gives.
- Save each answer under `## Form answers` in `job.md`, so a later correction can find the answers that repeat a claim.

Done when every answer sits in `job.md` in the user's phrasing, inside its word range, with each fact traced to a bank entry.

### 7. Report

Finish `## Fit` in `job.md`: the bank entries used and why, keyword coverage and experience months from the build, the rehearsal's count of requirements met, and questions whose answers would make the resume stronger. Then tell the user, as a short list:

- the PDF path
- the keywords found, the requirements met, and the gaps
- any floor of years the build says the dated roles miss
- the form answers that must agree with the page: location, graduation month, degree, grade and work authorization
- to check, field by field, any form that fills itself in from the uploaded resume
- to keep titles, employers and dates on their LinkedIn profile the same as the page
- any other application to the same employer in `jobs/README.md`, and a question: who do they know there who could refer them

Record their referral answer, or the date you asked, on the `Referral` line. Run `python3 scripts/applications.py` so the draft shows in `jobs/README.md`, and commit the folder.

Done when `## Fit` is complete, the `Referral` line is filled, `jobs/README.md` lists the draft, and the folder is committed.

## When the user submits

The `track-application` skill records the submission, freezes the folder, and tracks every reply after it.

## `job.md` template

```markdown
# <Company>, <Role>

- Source: <url of the post, or "pasted by the user">
- Saved: <YYYY-MM-DD>
- Generator: <the current version, the last row of `VERSIONS.md`>
- Apply: <url of the apply page, or "unknown">
- Deadline: <YYYY-MM-DD>, <what the post says>, only when the post names one
- Referral: <who the user knows there, or "none", with the date they answered; or "asked <YYYY-MM-DD>">
- Status: drafted

## Post

<verbatim post text>

## Fit

- Entries used: <bank ids, one reason each>
- Keywords: <covered>/<total> from the build
- Requirements: <met> met, <unclear> unclear, <not met> not met, from the rehearsal
- Experience: <months> months from the build

## Requirements

- <requirement in the post's words>: <met, unclear or not met>, <the resume line that decided it>

## Gaps

- <term from the post the bank does not back>: <what the bank holds in its place, or "nothing in the bank">

## Form questions

- <question>: <answer and its bank source, or "ask the user">

## Form answers

### <question>

<answer the user approved, with its word count>

## Build notes

- <warn that stays>: <why the bank cannot fix it>

## Open questions

- <a question whose answer would add a fact the post wants>
```
