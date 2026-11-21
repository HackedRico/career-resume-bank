# Experience bank

Everything true about the user's work, in one place. Tailored resumes draw every fact from here and nowhere else. `profile.md` holds contact details, education and certifications. `skills.md` holds the skill inventory. Each role is one file in `roles/`, each project one file in `projects/`. `sources/resumes/` keeps the text of old resumes as raw material: where a source and a role file disagree, the role file wins.

`examples/` shows each file filled in for two made-up people, in `data-engineer/bank/` and `nurse/bank/`.

## `profile.md`

```markdown
# Profile

## Contact
- Name: <full name, with no credentials after it>
- Phone: <number>
- Email: <address>
- LinkedIn: linkedin.com/in/<handle>
- GitHub: github.com/<handle>
- Portfolio: <url>
- <Site>: <address of any other profile a reader should open, such as Behance or Google Scholar>
- Location: <where the user lives, as a resume prints it, such as City, ST or City, Country>

## Education
- <School, City, ST or Country>
- <degree, diploma or certificate, and the subject>
- Graduated: <Mon YYYY>, or Expected graduation: <Mon YYYY>
- GPA: <0.0>, or Grade: <as the school states it, such as 2:1 or Upper Credit>

## Licenses
- <license, the state or body that issued it, its status>

## Certifications
Most relevant first.
- <issuer and name>

## Languages
- <language, level>

## Honors
- <award, year>

## Application answers
- Work authorization: <answer> (confirmed <YYYY-MM-DD>)
- Open to relocation: <answer>
- Earliest start date: <answer>
```

The build reads the Name, the Location, and whether Contact lists a LinkedIn or GitHub address. Leave out any line or section the user does not have, and write an answer nobody has given yet as `ask the user`. The Location line may end with a note in parentheses, such as `(confirmed 2026-01-05)`.

A resume prints `## Languages` and `## Honors` in Skills rows labelled `Languages` and `Awards`. The profile backs those rows, so neither needs a line in `skills.md`.

Credentials a person writes after their name, such as RN, CPA or PhD, go under Licenses, Certifications or Education and never on the Name line. The build names the PDF from that line, and a parser files it as the name.

## `skills.md`

```markdown
# Skills inventory

## Backed

| Skill | Evidence |
| --- | --- |
| <skill> | <entry id>, <entry id> |
| <skill> (<alias or parts>) | <entry id> |

## Listed

- <skill>, <skill>
```

A **Backed** skill has work behind it: the Evidence cell names the role or project files whose Facts show it. A **Listed** skill is one the user names with no work logged yet. A resume prints a Listed skill in a Skills row and never in a bullet: the build fails a bullet that names one, unless that entry's Facts state it. A term in parentheses, as in `Search engine optimization (SEO)`, counts as its own term.

## Role and project files

```markdown
---
id: <employer>-<title>
kind: role
org: <Employer>
title: <Job Title>
location: <City, ST or Country>
start: <YYYY-MM>
end: <YYYY-MM>
tags: [<tag>, <tag>]
---

# One-line heading

## Facts
Plain statements of what happened: numbers, tools, scope, outcomes, who used it.
The source of truth for every resume line.

## Bullets
- [<tag>] Resume-ready bullet, verb first, past tense for finished work.
- [<tag>] Another angle on the same work.

## Avoid
- `(?:led|managed) the launch` The reason, in the user's words, with the date they gave it.

## Notes
Context, open questions, things to confirm with the user.

## Links
- <url> (public) link: Name, Other Name
```

The front matter fields:

- `id` is the file name without `.md`.
- `kind` is `role` or `project`.
- `org` is the employer, or the event or client for a project.
- `title` is the job title, or the user's part in the project.
- `location` is where the work was done, in the form the user's resumes print it. Leave it out for a project, and for work with no one place, such as freelance work.
- `start` and `end` are `YYYY-MM`, or `YYYY` when the month is unknown. `end` is `present` for work still going.
- `tags` are focus tags from the list below.

A date holds only what the user knows. When they recall the year and not the month, write the year, and a resume prints the year alone until they give the month.

**Facts** carries every number and claim. **Bullets** are phrasings built only from Facts; write several angles on one piece of work so a tailored resume can pick the angle a job wants. A bullet's tags say which jobs it fits. Each bullet makes one claim inside the limits in `AGENTS.md`, and the newest sit first.

A project's name on a resume is its `# ` heading up to the first comma, as `Budget Tracker` from `# Budget Tracker, a household spending app`.

**Avoid** turns a correction into a check. Each line is a backticked regex, matched case-insensitively, then the reason. `scripts/build.py` fails a resume whose text for this entry matches a rule, and fails every build while one of the entry's own bullets matches. Write the pattern wide enough to catch the claim's other phrasings, such as `(?:led|managed|ran)`.

Write bullets as plain text. Escape `&`, `%`, `$`, `#` and `_` with a backslash when copying a bullet into `resume.tex`.

A link is anything a reader can open to check the work: a published article, a portfolio piece, a product page, a code repo. Mark each `(public)` or `(private)`; for a GitHub repo, `gh api repos/<owner>/<name> --jq .visibility` tells which. After `link:`, list the names a resume prints for that link, most specific first. Give `link:` to the one page a recruiter should land on, and leave it off a private link or a second link to the same work.

Mark a fact the user guessed, hedged or could not recall with `(unconfirmed)`, on its own Facts line. It stays off resumes until they confirm it, and the build counts no figure from that line. What the user's own resume states counts as confirmed.

## Focus tags

Tags name the kinds of work the user does, so a tailored resume can pull the bullets a post wants. `start-bank` writes the first list here from the user's roles. Add a tag to the table before using a new one, and keep the list short enough to choose from: about ten.

| Tag | Covers |
| --- | --- |
| `<tag>` | <the kind of work it marks> |
