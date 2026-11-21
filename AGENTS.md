# career-resume-bank

A resume generator for one person, the **user**: whoever owns this clone. The **bank** in `bank/` holds every true fact about the user's work. For each job post, an agent writes a one-page `resume.tex` from the bank, aimed at the post's keywords, and `scripts/build.py` compiles and checks it.

## Layout

| Path | Holds |
| --- | --- |
| `bank/` | The source of truth: `profile.md`, `skills.md`, `roles/`, `projects/`, and old resumes as text in `sources/resumes/`. Format and tags in `bank/README.md`. It holds only that README until `start-bank` fills it. |
| `template/` | `resume.cls`, the layout, and `blank.tex`, the shape of a resume with no facts in it. Change the class only when the user asks for a format change, then rebuild `base/`. |
| `base/` | The user's general-purpose resume, and the starting point for every tailored one. `start-bank` writes it. |
| `jobs/<YYYY-MM-DD>-<company>-<role>/` | One application: `job.md`, `keywords.txt`, `resume.tex` and the PDF, named `<First>_<Last>_Resume.pdf` from the profile. |
| `jobs/README.md` | The application tracker. `scripts/applications.py` writes it from every `job.md`, so it is never edited by hand. |
| `examples/` | One folder per made-up person, each with a bank, a base resume and one application. They show the format and hold nobody's facts. |
| `scripts/build.py` | Compiles each named folder and checks the PDF the way a parser and a keyword search read it, and the page against the nearest bank and the post saved in `job.md`. Its report names every check and the fix for each one that fails. |
| `scripts/test_build.py`, `scripts/test_applications.py` | Unit tests. Run the one beside the script you changed. |
| `scripts/applications.py` | Reads each `job.md` header and Timeline, prints what needs the user today, and rewrites `jobs/README.md`. |
| `VERSIONS.md` | The generator versions: what each one changed in the rules, the layout and the checks. |
| `.claude/settings.json` | A session start hook that runs `scripts/applications.py --hook` and shows the user what needs them. |

## Rules

- **Facts come from the bank.** Every number, tool, scope and outcome on a resume appears in a bank entry's Facts. When a post wants something the bank lacks, list it as a gap and ask the user; a fact they give goes into the bank first, then onto the resume.
- **The examples are format only.** Read `examples/` to see what a filled bank and a finished resume look like. Take every fact from the user's own `bank/`; the build fails a resume that prints an example person's name, employers, projects or contact details, and a bank that repeats one of their Facts.
- **The bank is private.** It holds a phone number, an address and a work history. Before the first commit that adds bank or job files, run `gh repo view --json visibility`. When the repo is public, tell the user and wait for their word. A clone with no remote publishes nothing, so commit. When the check cannot tell, ask the user.
- **Ship only a clean build.** One page, and `python3 scripts/build.py <folder>` prints no `FAIL`.
- **One claim per bullet.** Each bullet makes one claim and leads with what changed and how much: the number, the scale, who used it. It runs one line where the claim fits and two when the second line carries a tool, a number or an outcome, and never passes 32 words. Split a bullet that makes two claims, and cut one that wraps for a few words. Every bullet earns its line: it has a number, a named audience or a before and after, and makes a claim no other bullet makes. Fill the page with bullets that do. Open each with the plain verb for what the user did, and let no verb open more than two.
- **Every role prints its employer.** Write each role as `\job{Employer}{Title}{Location}{Dates}`, one line that names its own employer and location, so no parser has to carry one down from a row above. `\entry` is for Education.
- **Link public work.** Wrap the first mention of each name a bank Links line gives after `link:` in `\href{url}{name}`, so a reader can check the work in one click. Leave a `(private)` link off the page. The build warns on public work that is named and unlinked, and fails a link to a private repo.
- **Tailor in place.** Each job gets its own folder; edit `base/` only to change the general-purpose resume. A change to `base/` or the bank never reaches `jobs/`; edit a job folder only when the user names it.
- **A submitted resume is frozen.** When the user says they sent one, the `track-application` skill records it, and the build skips that folder from then on. A resend with changes gets a new folder.
- **A resume keeps its generator version.** A new folder records the current version on the `Generator` line of its `job.md`. A later version is never applied to an earlier folder, so read an old folder for its facts and its post, never as a pattern for layout, bullets or keywords.
- **Write plainly.** Commas where a dash would go, straight quotes, plain words, and verb-first bullets: past tense for finished work, present tense for work still going.

## Workflows

- An empty bank, or a first resume to import: the `start-bank` skill, `.claude/skills/start-bank/SKILL.md`.
- A job post, or a request for a resume for a role: the `tailor-resume` skill, `.claude/skills/tailor-resume/SKILL.md`.
- New experience, a number or a correction: the `log-experience` skill, `.claude/skills/log-experience/SKILL.md`.
- A submission, a reply, an interview, an outcome, or "where do my applications stand": the `track-application` skill, `.claude/skills/track-application/SKILL.md`.

## Tooling

`pdflatex` from MacTeX, BasicTeX or TeX Live, and `pdftotext`, `pdfinfo`, `pdffonts`, `pdfimages` and `pdftoppm` from poppler. The build names any that are missing and how to install them. `gh`, the GitHub CLI, tells a public repo from a private one.
