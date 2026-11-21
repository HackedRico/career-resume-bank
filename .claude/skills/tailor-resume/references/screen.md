# Screen rehearsal

Step 5 of the tailor-resume skill sends a fresh reader the page and the post, and nothing else. The author knows what each bullet was meant to prove, so the author cannot tell which bullets prove it on their own. The reader stands in for the two readers the build cannot be: a parser that turns the text into fields, and a screening model that grades each requirement against the page.

## Run it

1. Build the folder, so `.build/resume.raw.txt` holds the text in the order the PDF stores it.
2. Start a subagent with no other context. Give it the brief below, then the `## Post` text from `job.md`, then the contents of `.build/resume.raw.txt`. Give it no bank file, no `keywords.txt`, no notes and no hint of what the resume is meant to show. A subagent in this repo still loads `AGENTS.md`, so the brief tells it to open no file.
3. Read its answer against the bank, as "Read the result" says.

With no subagent tool, do the brief yourself from the two inputs alone, and grade as a stranger would: credit a requirement only when you can quote the line that shows it.

## The brief

```text
You are screening one resume for one job post. You have only the post and the resume text below. Open no file and search nothing. Judge what the text says, and credit nothing it does not say.

1. Parse the resume into fields. Copy each value exactly as printed, and write "not found" where the text gives none:
   name, location, phone, email, each web address, school, degree, major, graduation date, grade, each license and certification, and for every position its employer, title, location, start and end.

2. List every requirement in the post, one per line, in the post's own words. Take each basic, minimum or required qualification first, then each preferred one. Split a line that asks for two things. Where the post joins alternatives with "or", keep them on one line and grade it met when any alternative is met. Leave out travel, physical and benefits lines.

3. Grade each requirement against the resume:
   met: a line shows the thing done, naming the tool or skill beside what was done with it.
   unclear: the skill is named but no line shows it used, or the evidence is a near miss.
   not met: nothing on the page supports it.
   Quote the one resume line that decided each grade.

4. Among the requirements you graded met, name the three with the thinnest evidence, and say what the line lacks: a number, the tool's name, who used the result, or how recent it is.

Answer with the parsed fields as a list, then one table with the columns requirement, required or preferred, grade and deciding line, then the three thin ones.
```

## Read the result

- **Fields.** Compare each parsed value with `bank/profile.md` and the front matter of each role file. A wrong or missing employer, title, date, school, degree or graduation date is a layout fault, not a content one: stop and tell the user which field broke, since the same fault reaches a real parser. A degree spelled out where the bank abbreviates it, or a date printed as a month name, is no fault.
- **Unclear, and the bank backs the requirement.** Rewrite the deciding bullet so it names the tool beside the action and gives the scale, or add a bullet from the entry whose Facts back it.
- **Not met, and the bank backs it.** The page is missing a bullet. Add it from Facts, cutting a project or the weakest bullet for space.
- **Unclear or not met, and nothing in the bank backs it.** It belongs under `## Gaps`. Add it there if it is missing.
- **Thin evidence.** Strengthen a thin bullet only with a fact its entry holds.

Rebuild after any change, and run the rehearsal once more when a required qualification changed grade. Record the last run under `## Requirements` in `job.md`, one line per requirement: the requirement, its grade, and the deciding line.

Done when every requirement the bank backs is graded met or sits under `## Build notes` as not fitting the page, every other one sits under `## Gaps`, and the parsed fields name the same employers, titles, months and years, school and degree as the bank.
