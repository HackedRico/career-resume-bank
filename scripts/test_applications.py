#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

# Importing applications.py from its own folder; keep the repo free of __pycache__.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import applications  # noqa: E402
from applications import TrackerError  # noqa: E402

# =============================================================================
# Module Overview
# =============================================================================
# Tests for `applications.py`: reading a job.md header and Timeline, the
# "needs you" rules, and the tracker page. They run on hand-written job.md
# text. Run with `python3 scripts/test_applications.py`.

TODAY = date(2026, 11, 1)


def job(*header: str, timeline: tuple[str, ...] = (), post: str = "We want Python.") -> str:
    lines = ["# Acme, Data Engineer, New Grad", "", *header, ""]
    if timeline:
        lines += ["## Timeline", "", *timeline, ""]
    return "\n".join(lines + ["## Post", "", post, ""])


def parse(*header: str, **sections: object) -> applications.Application:
    return applications.parse_application("2026-10-20-acme-data-engineer", job(*header, **sections))


SENT = ("- Source: https://example.com/jobs/1", "- Saved: 2026-10-20", "- Submitted: 2026-10-21, commit abc1234")


class ParseTest(unittest.TestCase):
    def test_reads_header_and_timeline(self) -> None:
        app = parse(
            *SENT,
            "- Apply: https://jobs.example.com/acme/1.",
            "- Status: interviewing, onsite round",
            "- Next: 2026-11-05, panel interview with the hiring team",
            timeline=("- 2026-10-28: recruiter emailed", "- 2026-10-30: phone screen went well"),
        )
        self.assertEqual((app.company, app.role), ("Acme", "Data Engineer, New Grad"))
        self.assertEqual((app.status, app.note), ("interviewing", "onsite round"))
        self.assertEqual(app.submitted, date(2026, 10, 21))
        self.assertEqual((app.next_date, app.next_step), (date(2026, 11, 5), "panel interview with the hiring team"))
        self.assertEqual(app.latest, (date(2026, 10, 30), "phone screen went well"))
        self.assertEqual(app.apply_url, "https://jobs.example.com/acme/1")

    def test_status_line_inside_the_post_does_not_count(self) -> None:
        app = parse("- Saved: 2026-10-20", "- Status: drafted", post="- Status: rejected")
        self.assertEqual(app.status, "drafted")

    def test_unknown_status_is_refused(self) -> None:
        with self.assertRaisesRegex(TrackerError, "use one of"):
            parse(*SENT, "- Status: pending")

    def test_active_status_needs_a_submitted_line(self) -> None:
        # Without it the build would still rebuild a resume the user already sent.
        with self.assertRaisesRegex(TrackerError, "Submitted"):
            parse("- Saved: 2026-10-20", "- Status: screening")

    def test_draft_with_a_submitted_line_is_refused(self) -> None:
        with self.assertRaisesRegex(TrackerError, "drafted"):
            parse(*SENT, "- Status: drafted")


class NeedsYouTest(unittest.TestCase):
    def reasons(self, *header: str, **sections: object) -> list[str]:
        return applications.needs_you(parse(*header, **sections), TODAY)

    def test_draft_due_within_a_week(self) -> None:
        self.assertEqual(self.reasons("- Saved: 2026-10-30", "- Deadline: 2026-11-03", "- Status: drafted"), ["draft due 2026-11-03, in 2 days"])

    def test_draft_due_later_waits(self) -> None:
        self.assertEqual(self.reasons("- Saved: 2026-10-30", "- Deadline: 2026-11-20", "- Status: drafted"), [])

    def test_old_draft_without_deadline(self) -> None:
        self.assertEqual(self.reasons("- Saved: 2026-10-01", "- Status: drafted"), ["draft saved 2026-10-01, send it or mark it skipped"])

    def test_next_step_due(self) -> None:
        reasons = self.reasons(*SENT, "- Status: screening", "- Next: 2026-11-02, phone screen with the recruiter")
        self.assertEqual(reasons, ["phone screen with the recruiter, 2026-11-02, tomorrow"])

    def test_three_quiet_weeks(self) -> None:
        app = applications.parse_application("f", job(*SENT, "- Status: submitted"))
        self.assertEqual(applications.needs_you(app, date(2026, 11, 11)), ["no word in 21 days, follow up or mark it ghosted"])

    def test_timeline_entry_resets_the_quiet_count(self) -> None:
        app = applications.parse_application("f", job(*SENT, "- Status: screening", timeline=("- 2026-11-05: recruiter replied",)))
        self.assertEqual(applications.needs_you(app, date(2026, 11, 11)), [])

    def test_closed_application_never_needs_you(self) -> None:
        self.assertEqual(self.reasons(*SENT, "- Status: rejected", "- Next: 2026-10-25, follow up"), [])


class SummaryTest(unittest.TestCase):
    def test_brief_summary_leaves_out_the_active_list(self) -> None:
        apps = [applications.parse_application("2026-10-20-acme-a", job(*SENT, "- Status: submitted"))]
        self.assertIn("Active", applications.summary(apps, TODAY))
        self.assertNotIn("Active", applications.summary(apps, TODAY, brief=True))


class RenderTest(unittest.TestCase):
    def test_each_application_lands_in_its_section(self) -> None:
        page = applications.render([
            applications.parse_application("2026-10-20-acme-a", job(*SENT, "- Status: submitted")),
            applications.parse_application("2026-10-22-acme-b", job("- Saved: 2026-10-22", "- Deadline: 2026-11-03", "- Status: drafted")),
            applications.parse_application("2026-10-19-acme-c", job("- Saved: 2026-10-19", "- Status: skipped, sent a newer copy")),
        ])
        coming, active, drafts, closed = (page.split(f"## {name}\n")[1].split("\n## ")[0] for name in ("Coming up", "Active", "Drafts", "Closed"))
        self.assertIn("| 2026-11-03 | [Acme](2026-10-22-acme-b/job.md) |", coming)
        self.assertIn("[Acme](2026-10-20-acme-a/job.md)", active)
        self.assertIn("no word yet", active)
        self.assertIn("[Acme](2026-10-22-acme-b/job.md)", drafts)
        self.assertIn("skipped, sent a newer copy", closed)

    def test_each_row_shows_the_generator_that_built_it(self) -> None:
        old = applications.parse_application("2026-10-20-acme-a", job(*SENT, "- Status: submitted"))
        new = applications.parse_application("2026-11-20-acme-b", job("- Saved: 2026-11-20", "- Generator: v2", "- Status: drafted"))
        self.assertEqual((old.generator, new.generator), ("v1", "v2"))
        page = applications.render([old, new])
        self.assertIn("| v1 | submitted |", page)
        self.assertIn("| v2 | 2026-11-20 |", page)

    def test_page_does_not_depend_on_today(self) -> None:
        apps = [applications.parse_application("2026-10-20-acme-a", job(*SENT, "- Status: submitted"))]
        self.assertNotIn("days", applications.render(apps))


if __name__ == "__main__":
    unittest.main()
