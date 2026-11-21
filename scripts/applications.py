#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JOBS_DIR = REPO / "jobs"
PROFILE = REPO / "bank" / "profile.md"
# What a session opens with while the repo holds nobody's facts yet.
NO_BANK = "No experience bank yet. Say \"start my bank\" and share a resume, or describe your work, to fill `bank/`."
JOB_NAME = "job.md"
TRACKER_NAME = "README.md"

# The Status words a job.md may use, by where the application stands. A note may follow a comma.
DRAFT = ("drafted",)
ACTIVE = ("submitted", "screening", "interviewing", "offer")
CLOSED = ("accepted", "declined", "rejected", "withdrawn", "ghosted", "skipped")
STATUSES = DRAFT + ACTIVE + CLOSED

# A deadline or Next date this many days out, or already past, needs the user.
DUE_SOON_DAYS = 7
# Three weeks with no word is the point to follow up or close the application as ghosted.
QUIET_DAYS = 21
# A draft this old with no deadline should be sent or marked skipped.
STALE_DRAFT_DAYS = 14

# The generator version of a folder whose job.md has no Generator line.
FIRST_GENERATOR = "v1"

TITLE = re.compile(r"^# (.+)$", re.MULTILINE)
# A header line above the first `## ` heading: "- Status: interviewing, onsite round".
HEADER_LINE = re.compile(r"^- (\w+): *(.*)$", re.MULTILINE)
# A dated line under `## Timeline`: "- 2026-11-02: recruiter emailed to set a phone screen".
TIMELINE_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}): *(.*)$", re.MULTILINE)
# A value that opens with a date: "2026-03-01, rolling review".
LEADING_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})\b,? *(.*)$")
URL = re.compile(r"https?://[^\s,)]+")


class TrackerError(Exception):
    """A job.md the tracker cannot read; the message says what to fix."""


@dataclass(frozen=True)
class Application:
    folder: str
    company: str
    role: str
    status: str
    note: str
    saved: date | None
    deadline: date | None
    submitted: date | None
    next_date: date | None
    next_step: str
    timeline: tuple[tuple[date, str], ...]
    post_url: str | None
    apply_url: str | None
    # the version of the rules, layout and checks that built the resume; `VERSIONS.md` says what each one changed
    generator: str = FIRST_GENERATOR

    @property
    def latest(self) -> tuple[date, str] | None:
        """The newest Timeline entry, or None before anything is logged."""
        return max(self.timeline, key=lambda entry: entry[0]) if self.timeline else None

    @property
    def last_word(self) -> date | None:
        """The last day anything happened after submitting."""
        days = [day for day, _ in self.timeline] + ([self.submitted] if self.submitted else [])
        return max(days) if days else None


def leading_date(value: str) -> tuple[date | None, str]:
    """Split "2026-03-01, rolling review" into its date and the rest."""
    match = LEADING_DATE.match(value.strip())
    if match is None:
        return None, value.strip()
    return date.fromisoformat(match.group(1)), match.group(2)


def first_url(value: str) -> str | None:
    match = URL.search(value)
    return match.group(0).rstrip(".;:") if match else None


def section(text: str, heading: str) -> str:
    """Return the body under `## heading`, or "" when job.md has no such section."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def parse_application(folder: str, text: str) -> Application:
    """Read one job.md: its title, the header lines above the first section, and its Timeline."""
    title = TITLE.search(text)
    if title is None:
        raise TrackerError("no `# <Company>, <Role>` title")
    company, _, role = title.group(1).partition(", ")
    # Only the header counts, so a "- Status:" line inside the pasted post never does.
    header = dict(HEADER_LINE.findall(text.split("\n## ", 1)[0]))
    status, _, note = header.get("Status", "").partition(",")
    status = status.strip()
    if status not in STATUSES:
        raise TrackerError(f"Status is {status or 'missing'}; use one of {', '.join(STATUSES)}")
    submitted, _ = leading_date(header.get("Submitted", ""))
    # The build freezes a folder on its Submitted line, so a status past drafted without one leaves a sent resume open.
    if status in ACTIVE and submitted is None:
        raise TrackerError(f"Status is {status} but there is no `- Submitted: <date>, commit <hash>` line")
    if status in DRAFT and submitted is not None:
        raise TrackerError("has a Submitted line but Status is drafted")
    next_date, next_step = leading_date(header.get("Next", ""))
    timeline = tuple((date.fromisoformat(day), what) for day, what in TIMELINE_LINE.findall(section(text, "Timeline")))
    return Application(
        folder=folder,
        company=company,
        role=role,
        status=status,
        note=note.strip(),
        saved=leading_date(header.get("Saved", ""))[0],
        deadline=leading_date(header.get("Deadline", ""))[0],
        submitted=submitted,
        next_date=next_date,
        next_step=next_step,
        timeline=timeline,
        post_url=first_url(header.get("Source", "")),
        apply_url=first_url(header.get("Apply", "")),
        generator=header.get("Generator", "").strip() or FIRST_GENERATOR,
    )


def when(day: date, today: date) -> str:
    """Say a date with how far off it is: "2026-10-30, in 2 days"."""
    days = (day - today).days
    if days == 0:
        return f"{day}, today"
    if days == 1:
        return f"{day}, tomorrow"
    if days == -1:
        return f"{day}, yesterday"
    return f"{day}, in {days} days" if days > 0 else f"{day}, {-days} days ago"


def needs_you(app: Application, today: date) -> list[str]:
    """Return why this application needs the user today, or nothing."""
    if app.status in CLOSED:
        return []
    reasons = []
    if app.status in DRAFT:
        if app.deadline is not None and (app.deadline - today).days <= DUE_SOON_DAYS:
            reasons.append(f"draft due {when(app.deadline, today)}")
        elif app.deadline is None and app.saved is not None and (today - app.saved).days >= STALE_DRAFT_DAYS:
            reasons.append(f"draft saved {app.saved}, send it or mark it skipped")
    if app.next_date is not None and (app.next_date - today).days <= DUE_SOON_DAYS:
        reasons.append(f"{app.next_step or 'next step'}, {when(app.next_date, today)}")
    if app.status in ACTIVE and app.next_date is None and app.last_word is not None:
        quiet = (today - app.last_word).days
        if quiet >= QUIET_DAYS:
            reasons.append(f"no word in {quiet} days, follow up or mark it ghosted")
    return reasons


def summary(apps: list[Application], today: date, brief: bool = False) -> str:
    """What needs the user today, then each active application and when it last moved; brief leaves out the active list."""
    flagged = [(app, reasons) for app in apps if (reasons := needs_you(app, today))]
    lines = ["Needs you" if flagged else "Nothing needs you today"]
    for app, reasons in flagged:
        lines.append(f"  {app.company}, {app.role}: {'; '.join(reasons)}")
        if not brief:
            lines.append(f"    jobs/{app.folder}")
    active = sorted((app for app in apps if app.status in ACTIVE), key=lambda app: app.last_word or date.min, reverse=True)
    if active and not brief:
        lines += ["", "Active"]
        for app in active:
            if app.latest:
                moved = f"latest {when(app.latest[0], today)}: {app.latest[1]}"
            else:
                moved = f"sent {when(app.submitted, today)}, no word yet"
            lines.append(f"  {app.company}, {app.role}: {app.status}, {moved}")
    counts = {stage: sum(app.status in stage for app in apps) for stage in (DRAFT, ACTIVE, CLOSED)}
    lines += ["", f"{counts[DRAFT]} drafted, {counts[ACTIVE]} active, {counts[CLOSED]} closed"]
    return "\n".join(lines)


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def company_link(app: Application) -> str:
    return f"[{cell(app.company)}]({app.folder}/{JOB_NAME})"


def links(app: Application) -> str:
    parts = [f"[post]({app.post_url})"] if app.post_url else []
    if app.apply_url and app.apply_url != app.post_url:
        parts.append(f"[apply]({app.apply_url})")
    return ", ".join(parts)


def status_text(app: Application) -> str:
    return cell(f"{app.status}, {app.note}" if app.note else app.status)


def latest_text(app: Application, empty: str = "no word yet") -> str:
    return cell(f"{app.latest[0]}: {app.latest[1]}") if app.latest else empty


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["None."]
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    return lines + ["| " + " | ".join(row) + " |" for row in rows]


def render(apps: list[Application]) -> str:
    """Write the tracker page from job.md data alone, so it changes only when an application does."""
    coming = [(app.deadline, app, "application deadline") for app in apps if app.status in DRAFT and app.deadline]
    coming += [(app.next_date, app, app.next_step) for app in apps if app.status not in CLOSED and app.next_date]
    coming.sort(key=lambda item: (item[0], item[1].folder))
    active = sorted((app for app in apps if app.status in ACTIVE), key=lambda app: (app.submitted, app.folder), reverse=True)
    drafts = sorted((app for app in apps if app.status in DRAFT), key=lambda app: (app.deadline or date.max, app.folder))
    closed = sorted((app for app in apps if app.status in CLOSED), key=lambda app: (app.last_word or app.saved or date.min, app.folder), reverse=True)

    lines = [
        "# Applications",
        "",
        f"`python3 scripts/applications.py` writes this page from the header and Timeline of each `{JOB_NAME}`. "
        f"Change the `{JOB_NAME}` and rerun the script; edits made here get overwritten. "
        "Gen is the generator version that built each resume, and `VERSIONS.md` says what each one changed.",
        "",
        "## Coming up",
        "",
        *table(["Date", "Company", "Role", "What"], [[str(day), company_link(app), cell(app.role), cell(what)] for day, app, what in coming]),
        "",
        "## Active",
        "",
        *table(
            ["Company", "Role", "Gen", "Status", "Submitted", "Latest", "Next", "Links"],
            [
                [company_link(app), cell(app.role), app.generator, status_text(app), str(app.submitted), latest_text(app),
                 cell(f"{app.next_date}: {app.next_step}" if app.next_date else app.next_step), links(app)]
                for app in active
            ],
        ),
        "",
        "## Drafts",
        "",
        *table(
            ["Company", "Role", "Gen", "Saved", "Deadline", "Links"],
            [[company_link(app), cell(app.role), app.generator, str(app.saved or ""), str(app.deadline or ""), links(app)] for app in drafts],
        ),
        "",
        "## Closed",
        "",
        *table(
            ["Company", "Role", "Gen", "Status", "Submitted", "Latest", "Links"],
            [
                [company_link(app), cell(app.role), app.generator, status_text(app), str(app.submitted or ""), latest_text(app, ""), links(app)]
                for app in closed
            ],
        ),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    """Write jobs/README.md and print what needs the user; return 1 if any job.md could not be read."""
    parser = argparse.ArgumentParser(description="Show where each application stands and write jobs/README.md.")
    parser.add_argument("--hook", action="store_true", help="print the Claude Code session start note as JSON and write nothing")
    args = parser.parse_args()
    apps, problems = [], []
    # A clone whose owner emptied it has no jobs folder until the next application.
    for folder in sorted(path for path in JOBS_DIR.glob("*") if path.is_dir()):
        job = folder / JOB_NAME
        if not job.is_file():
            problems.append(f"jobs/{folder.name}: no {JOB_NAME}")
            continue
        try:
            apps.append(parse_application(folder.name, job.read_text(encoding="utf-8")))
        except (TrackerError, ValueError) as error:
            problems.append(f"jobs/{folder.name}/{JOB_NAME}: {error}")
    tracker = JOBS_DIR / TRACKER_NAME
    page = render(apps)
    if args.hook:
        lines = ["Job applications", summary(apps, date.today(), brief=True)] if PROFILE.is_file() else [NO_BANK]
        if not tracker.is_file() or tracker.read_text(encoding="utf-8") != page:
            lines.append(f"{tracker.relative_to(REPO)} is out of date; run python3 scripts/applications.py")
        lines += [f"FAIL  {problem}" for problem in problems]
        note = "\n".join(lines)
        # systemMessage shows the note to the user; additionalContext hands the same note to the session's model.
        print(json.dumps({"systemMessage": note, "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": note}}))
        return 0
    JOBS_DIR.mkdir(exist_ok=True)
    tracker.write_text(page, encoding="utf-8")
    print(summary(apps, date.today()))
    print(f"wrote {tracker.relative_to(REPO)}")
    for problem in problems:
        print(f"FAIL  {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
