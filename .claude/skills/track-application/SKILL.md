---
name: track-application
description: Records where each of the user's job applications stands, from submission through replies, interviews and the outcome, in the job folder's job.md, and rewrites the jobs/README.md tracker. Use when the user says they submitted a resume, heard back, have an interview or assessment, got rejected or an offer, withdrew, or asks where their applications stand.
---

# Track an application

Each `jobs/<folder>/job.md` carries its application's state in two places: the header lines under the title, and a `## Timeline`. `scripts/applications.py` reads every folder, prints what needs the user today, and writes `jobs/README.md`. The README is generated, so every change goes into `job.md`.

## The header

```markdown
- Submitted: 2026-01-14, commit abc1234
- Status: interviewing, second round
- Next: 2026-01-22, panel interview with the hiring team
```

- **Submitted** is the freeze line: the build skips any folder that has it. Write it once, when the user sends the resume, and leave it as written.
- **Status** is one word, and a short note may follow a comma:
  - `drafted`: built, not sent.
  - `submitted`: sent, no reply yet.
  - `screening`: a recruiter call or an online assessment.
  - `interviewing`: any round with the team.
  - `offer`, then `accepted` or `declined`.
  - `rejected`, `withdrawn` when the user pulls out, `ghosted` when they decide to stop waiting, `skipped` for a draft they never send.
- **Next** holds the one dated thing coming up, as `<YYYY-MM-DD>, <what>`: an interview, an assessment due, a follow-up they plan. Replace it when that thing happens.
- **Deadline**, on a draft whose post names one, is set by `tailor-resume`.

## The Timeline

`## Timeline` sits between the header and `## Post`. Add it at the first event after submitting. Each line is one event, oldest first, dated the day it happened:

```markdown
- 2026-01-16: Dana Lee, recruiter, emailed to set a phone screen
- 2026-01-20: phone screen with Dana, 30 min; asked about travel and a March start
```

Name the person and their role, the round, and anything the user will want before the next conversation: a question they were asked, a number they were given, what comes next. Log from the first event they report; history before that stays unwritten.

## Steps

### 1. Record the change

Find the folder by company and role. Then, by event:

- **They submitted.** Ask which version they sent if they do not say. Add `- Submitted: <YYYY-MM-DD>, commit <hash>` above Status and set Status to `submitted`, where the hash is the last commit that changed the PDF they sent: `git log -1 --format=%h -- jobs/<folder>/*.pdf`.
- **They heard back, or a round happened.** Add the Timeline line, move Status when the stage changed, and set or replace Next.
- **It ended.** Add the Timeline line, set the closing Status, and remove Next.
- **The script flags three quiet weeks.** Ask whether they followed up or want it marked `ghosted`; set `ghosted` only on their word.

Done when the header and Timeline say everything they told you, each line dated.

### 2. Rebuild the tracker

```bash
python3 scripts/applications.py
```

Fix every `FAIL` it prints in the `job.md` it names. Done when it exits 0.

### 3. Commit

Commit the `job.md` with `jobs/README.md`, with a message that says what happened. For a submission, then run `git tag submitted/<folder> <hash>` on the hash from step 1. Read the user the script's "Needs you" lines.

When they only ask where things stand, run step 2 and read them "Needs you" and the active list.

## What stays frozen

Once Submitted is set, the folder holds what the employer has: `resume.tex`, `keywords.txt`, the PDF, and every `job.md` section from `## Post` down. The header, Next and Timeline stay open for tracking. A resume change goes in a new folder through `tailor-resume`.
