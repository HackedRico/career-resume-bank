# Generator versions

The generator is the rules in `AGENTS.md`, the layout in `template/resume.cls`, the skills, and the checks in `scripts/build.py`. A change to any of them that alters how a resume looks, or what the build accepts, is a new version: raise `GENERATOR` in `scripts/build.py` and add a row here.

Each job folder records the version that built it on the `Generator` line of its `job.md`. A later version is never applied to an earlier folder.

| Version | What it set |
| --- | --- |
| v1 | One page in Times at 10.5pt. Each role on one line with its employer, title and location, dates at the right margin. Education inline. Bullets of one claim, at most two lines and 32 words, no verb opening more than two. Every figure on the page checked against the bank's Facts, every Skills row item against the bank, and no bullet naming a Listed skill or a `## Gaps` term. |
