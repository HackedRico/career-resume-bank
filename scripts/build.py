#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO / "template"
BANK_DIR_NAME = "bank"
# A `start` or `end` in a bank file's front matter: "2023-06", or "2023" when the month is unknown.
BANK_DATE = re.compile(r"^\d{4}(?:-\d{2})?$")
UNCONFIRMED = "(unconfirmed)"
PROFILE_NAME = "profile.md"
# One folder per made-up person, each with a bank, a base resume and a job folder, there to show the format.
# A resume outside a person's folder never prints what is theirs.
EXAMPLES_DIR = REPO / "examples"
BUILD_DIR_NAME = ".build"
KEYWORDS_NAME = "keywords.txt"
JOB_NAME = "job.md"
# The version of the rules, layout and checks a resume is built with. Raise it, and add a row to `VERSIONS.md`,
# whenever a change alters how a resume looks or what this build accepts.
GENERATOR = "v1"
GENERATOR_LINE = re.compile(r"^- Generator: *(.*)$", re.MULTILINE)

# Keep in sync with `geometry` in template/resume.cls.
BOTTOM_MARGIN_PT = 0.4 * 72
# Baseline-to-baseline distance of body text, from `\fontsize` in template/resume.cls.
LINE_HEIGHT_PT = 12.4
# Below this the page looks thin. The number is a chosen default, as the bullet limits are.
PAGE_MIN_FILL = 0.93
# One verb may open this many bullets. Past it the page reads as a list of the same act.
LEAD_VERB_MAX = 2
# One claim per bullet. A line holds about 19 words, so this cap lets a bullet run most of two lines.
BULLET_MAX_WORDS = 32
# A second line shorter than this share of the widest bullet line is a few stray words that a cut would save.
BULLET_MIN_WRAP = 0.25
# A reader skims a resume in seconds, and a short bullet survives the skim where a long block does not.
BULLET_MAX_LINES = 2
# A gap this many text heights wide, between two words on one line, reads as a column break to some extractors.
COLUMN_GAP_HEIGHTS = 2.0
# Some applicant tracking systems skip parsing above 2.5 MB.
MAX_PDF_BYTES = 2_500_000
# A text layer that holds under this share of the letters and digits its source prints is mostly gone.
MIN_TEXT_SHARE = 0.5
# The ink check renders the page at this resolution, enough to resolve the smallest legitimate text.
INK_DPI = 150
MIN_WORD_HEIGHT_PT = 6.0
# A word box whose darkest pixel is lighter than this gray level has no visible ink, as with white text.
INK_MAX_GRAY = 200
# TeX logs every line wider than its 0.1pt `\hfuzz`; under 1pt, about 2 pixels at INK_DPI, nobody sees the overrun.
OVERFULL_MAX_PT = 1.0
# "Overfull \hbox (18.4789pt too wide) in paragraph at lines 41--42", or "... detected at line 12" outside a paragraph.
OVERFULL = re.compile(r"^Overfull \\hbox \(([\d.]+)pt too wide\) .*?\blines? (\d+)(?:--(\d+))?", re.MULTILINE)
POPPLER = "`brew install poppler`, or `apt install poppler-utils`"
REQUIRED_TOOLS = {
    "pdflatex": "install MacTeX, BasicTeX or TeX Live",
    "pdftotext": POPPLER,
    "pdfinfo": POPPLER,
    "pdffonts": POPPLER,
    "pdfimages": POPPLER,
    "pdftoppm": POPPLER,
}

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_MONTH = "|".join(MONTHS)
_DATE = rf"(?:(?:{_MONTH}) )?\d{{4}}"
# Parsers read "Mon YYYY - Mon YYYY"; a year alone is stored as January, which skews tenure math.
ROW_DATE = re.compile(rf"^{_DATE}(?: - (?:{_DATE}|Present))?$")
TRAILING_DATE = re.compile(rf"^(.*?\S)(?:\s+\|)?\s+({_DATE}(?: - (?:{_DATE}|Present))?)$")
# A date in a form people write and the checks cannot read: "March 2016 - Present", "03/2016", "2016-2023", "Mar 2016 to Current".
_LOOSE_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
_LOOSE_DATE = rf"(?:(?:{_LOOSE_MONTH}|\d{{1,2}})[\s/.,-]*)?(?:19|20)\d{{2}}"
_LOOSE_RANGE = rf"{_LOOSE_DATE}(?:\s*(?:-+|\u2013|\u2014|to|until)\s*(?:{_LOOSE_DATE}|present|current|now|ongoing|today))?"
LOOSE_DATE = re.compile(rf"^{_LOOSE_RANGE}$", re.IGNORECASE)
LOOSE_TRAILING_DATE = re.compile(rf"^(.*?\S)(?:\s+\|)?\s+({_LOOSE_RANGE})$", re.IGNORECASE)
MONTH_RANGE = re.compile(rf"^(?:{_MONTH}) \d{{4}}(?: - (?:(?:{_MONTH}) \d{{4}}|Present))?$")
EXPECTED_DATE = re.compile(rf"^Expected (?:{_MONTH}) \d{{4}}$")
GRADUATION = re.compile(rf"^(Expected )?((?:{_MONTH}) \d{{4}})$")
# pdftotext -layout puts three or more spaces between a left field and a field at the right margin.
FIELD_GAP = re.compile(r"\s{3,}")
SKILL_LABEL = re.compile(r"^([A-Z][A-Za-z0-9 &/+()-]*):\s")
# Skills rows that list credentials. The profile backs them, where the skill inventory backs every other row.
CREDENTIAL_LABELS = frozenset({"Certifications", "Licenses", "Credentials"})
# Skills rows the profile may back as well as the inventory, from its `## Languages` and `## Honors` sections.
PROFILE_LABELS = frozenset({"Languages", "Honors", "Awards"})
QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})

# A figure: "6,300+", "85%", "$240K", "3x", and "24/7" or "9-12" as two. Digits after a letter, as in B2B and HL7,
# are part of a name. A magnitude letter stays with its number, so "$250k" is not backed by a Fact of 250.
FIGURE = re.compile(r"(?<![A-Za-z0-9.])(\d+(?:,\d{3})*(?:\.\d+)?)(?!\d)(?:(k|mm|m|bn|b)(?![A-Za-z]))?", re.IGNORECASE)
MAGNITUDES = {"k": "k", "m": "m", "mm": "m", "b": "b", "bn": "b"}
# A date a Fact was logged on, "2026-11-17", holds no figure: its 17 is not the "17%" of a bullet.
ISO_DATE = re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b")
# Some candidate searches drop these words, so a term made only of them, such as IT, is never searched.
STOPWORDS = frozenset(
    "a an and are as at be but by for if in into is it no not of on or such that the their then there these they"
    " this to was will with".split()
)
# A literal search for "Bachelor" misses a page that prints only the abbreviation, with its periods or without:
# "B.S." and "BSc". Four need their periods, since the bare letters are a state code a school line prints.
_DEGREES = "A.A B.S B.Sc B.A B.F.A B.B.A B.S.N B.Eng B.Ed LL.B LL.M M.Sc M.B.A M.F.A M.Eng M.Ed M.P.H M.S.N J.D Ph.D Ed.D D.N.P Pharm.D"
_DEGREES_DOTTED = "A.S M.A M.S M.D"
DEGREE_ABBREVIATION = re.compile(
    r"(?<![A-Za-z.])(?:"
    + "|".join(
        [r"\.?".join(map(re.escape, degree.split("."))) + r"\.?" for degree in _DEGREES.split()]
        + [r"\.".join(map(re.escape, degree.split("."))) + r"\." for degree in _DEGREES_DOTTED.split()]
    )
    + r")(?![A-Za-z])"
)
DEGREE_WORD = re.compile(r"\b(?:Associate|Bachelor|Master|Doctor)")
# How a profile may write each degree level the page spells out: "B.S.", "BSN", "MBA", "Ph.D.".
DEGREE_FORMS = {
    "Associate": r"\bassociate|\ba\.?[as]\b",
    "Bachelor": r"\bbachelor|\bb\.?(?:s|a|sc|eng|ed|f\.?a|b\.?a|s\.?n)\b|\bll\.?b\b",
    "Master": r"\bmaster|\bm\.?(?:s|a|sc|eng|ed|f\.?a|b\.?a|p\.?h|s\.?n)\b|\bll\.?m\b",
    "Doctor": r"\bdoctor|\bph\.?d|\b(?:j|m|ed|pharm)\.?d\b|\bd\.?n\.?p\b",
}
# Words every Education row may print: the level and the words that join a degree to its major.
EDUCATION_WORDS = frozenset("associate bachelor bachelors master masters doctor doctorate science arts expected with".split())
# Shorter words in an Education row are joining words such as "of" and "in", or a state code.
EDUCATION_WORD_MIN = 4
# The `keywords.txt` line for a required degree, as the tailor-resume skill writes it: `!Bachelor`.
DEGREE_LEVEL = re.compile(r"(?:Associate|Bachelor|Master|Doctor)(?:'s|ate)?")
# Some parsers store a stated duration such as "3 years of Python" as skill experience at face value.
DURATION = re.compile(r"\b\d+(?:\.\d+)?\+?\s*(?:years?|yrs?)\b(?:\s+(?:of|with|in)\b)?", re.IGNORECASE)
TRAINEE_TITLE = re.compile(r"\b(?:Intern(?:ship)?|Co-?op|Trainee|Student)\b", re.IGNORECASE)
# "5+ years of experience", "3-5 years of relevant work experience": the first number is the floor a screener holds
# the dated roles to. Only a phrase that reaches the word experience counts, so "vests over 4 years" does not.
YEARS_ASKED = re.compile(
    r"(?<![\d.$])(\d{1,2})\+?(?:\s*(?:-|to)\s*\d{1,2})?\+?\s*(?:years?|yrs?)\b'?(?=\s+(?:[\w-]+\s+){0,4}?experience\b)",
    re.IGNORECASE,
)
# The system word list on macOS and most Linux installs; without it the spelling check is skipped.
WORD_LIST = Path("/usr/share/dict/words")
WORD = re.compile(r"[A-Za-z][A-Za-z']*")
# One ending comes off a word before a word list is searched, so "debugged" finds "debug".
WORD_ENDINGS = ("'s", "s", "es", "ed", "d", "ing", "ly", "er", "ers", "ies", "ied")
# Text addressed to a screening model. It reaches every parsed view a recruiter opens.
INJECTION = re.compile(
    r"\b(?:ignore|disregard|forget)\s+(?:all\s+|any\s+)?(?:the\s+)?(?:previous|prior|above|earlier|preceding)\s+"
    r"(?:instructions|prompts?|directions)\b"
    r"|\b(?:if|when)\s+you\s+are\s+an?\s+(?:ai|llm|language model|assistant|bot)\b",
    re.IGNORECASE,
)
# Phrases that can address a screening model and can also describe honest work, such as ranking applicants.
INJECTION_SOFT = re.compile(
    r"\b(?:note|message|instructions?)\s+(?:to|for)\s+(?:the\s+)?(?:ai|llm|model|screener)\b"
    r"|\brank\s+(?:this|me)\s+(?:candidate|applicant|resume)\b"
    r"|\bthis\s+candidate\s+is\s+(?:the\s+)?(?:best|ideal|perfect|most qualified)\b",
    re.IGNORECASE,
)
# Spelled-out symbol terms that no literal search for the real term will match.
SYMBOL_SPELLINGS = (
    (re.compile(r"\bC\s+Sharp\b", re.IGNORECASE), "C#"),
    (re.compile(r"\bC\s+Plus\s+Plus\b", re.IGNORECASE), "C++"),
    (re.compile(r"\bSecurity\s+Plus\b", re.IGNORECASE), "Security+"),
    (re.compile(r"\bNetwork\s+Plus\b", re.IGNORECASE), "Network+"),
    (re.compile(r"\bCompTIA\s+A\s+Plus\b", re.IGNORECASE), "A+"),
)
# pdfTeX draws the spaces `\pdfinterwordspaceon` adds from a font of this name.
SPACE_FONT = "PdfTeX-Space"
WORD_BOX = re.compile(r'<word xMin="([-\d.]+)" yMin="([-\d.]+)" xMax="([-\d.]+)" yMax="([-\d.]+)">([^<]*)</word>')
PAGE_BOX = re.compile(r'<page width="([\d.]+)" height="([\d.]+)"')
# job.md's line once the user sends the resume: "- Submitted: 2026-01-14, commit abc1234". It stays when Status moves on.
SUBMITTED = re.compile(r"^- Submitted: *(.*)$", re.MULTILINE)
PAIR_ENTRY = re.compile(r"^(.+?) \(([^()]+)\)$")
# A bank Links line: "- <url> (public) link: Trailhead Maps, Trailhead"; the note after public or private is free text.
BANK_LINK = re.compile(r"^- (\S+)(?: \((public|private)\b[^)]*\))?(?: link: (.+))?$")
# A bank Avoid line: "- `ran (?:the )?audit` The finance lead ran it."
BANK_AVOID = re.compile(r"^- `([^`]+)`\s*(.*)$")
HREF = re.compile(r"\\href\{([^}]*)\}")
# A web address as the contact block prints it: "github.com/jordan-example", "jordan-example.dev".
WEB_ADDRESS = re.compile(r"\b[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}")
# The name, then at most two lines of contact details.
CONTACT_MAX_LINES = 3
# Contact links that may print a label in place of their address. A person reads "Portfolio" faster than a
# site's address, and the LinkedIn and GitHub addresses a parser files stay printed.
CONTACT_LABELS = frozenset({"Portfolio"})
HREF_TEXT = re.compile(r"\\href\{([^}]*)\}\{([^}]*)\}")
# A heading that joins two topics, as SKILLS AND CERTIFICATIONS does. A parser files a section under one type.
JOINED_HEADING = re.compile(r"\s(?:AND|&)\s|[,/]")
# The bar between the fields of a role or project line, as `\job` and `\project` print it.
ROW_SEP = re.compile(r"\s+\|\s+")
GITHUB_REPO = re.compile(r"^https://github\.com/[^/]+/[^/]+$")
# The profile sites a parser files from the contact block. The block prints each one the bank's profile lists.
PROFILE_SITES = ("linkedin.com/in/", "github.com/")

# =============================================================================
# Module Overview
# =============================================================================
# Compiles one or more `resume.tex` files with pdflatex and checks the PDF the
# way an ATS, a recruiter and a screening model will read it: the text layer,
# fonts and hidden text, lines past the margin, headings, contact and dates,
# dates, figures, skills and `## Avoid` wording against `bank/`, spelling, and the
# job's `keywords.txt`, both on the page and against the post saved in `job.md`.
# Exits non-zero when a resume must not ship.


class BuildError(Exception):
    """A resume that failed to compile, or an input file that could not be read."""


@dataclass
class Report:
    """Outcome of building one resume: the files written and every check result."""

    tex: Path
    # where the PDF lands once the build is clean
    pdf: Path
    text_file: Path
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)


# =============================================================================
# Compile
# =============================================================================


def compile_pdf(tex: Path) -> Path:
    """Run pdflatex on `tex` inside its `.build` folder and return the PDF path."""
    build_dir = tex.parent / BUILD_DIR_NAME
    build_dir.mkdir(exist_ok=True)
    # The resume's own folder comes first, so no file in `template/` can stand in for it.
    # Trailing separator keeps TeX's default search path after ours.
    env = {**os.environ, "TEXINPUTS": f".{os.pathsep}{TEMPLATE_DIR}{os.pathsep}"}
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={build_dir}", tex.name],
        cwd=tex.parent,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise BuildError(f"{tex}: pdflatex failed\n{latex_errors(result.stdout)}")
    return build_dir / f"{tex.stem}.pdf"


def latex_errors(log: str) -> str:
    """Pull the `!` error lines and their `l.N` source line out of a pdflatex log."""
    lines = log.splitlines()
    picked = [line for line in lines if line.startswith("!") or re.match(r"l\.\d+", line)]
    # A small TeX install, such as BasicTeX, lacks some packages the class loads.
    missing = re.search(r"File `([\w-]+)\.sty' not found", log)
    if missing:
        picked.append(f"install the package with `sudo tlmgr install {missing.group(1)}`, then build again")
    return "\n".join(f"  {line}" for line in picked) or log[-2000:]


def run_tool(*args: str) -> str:
    """Run a poppler tool and return its stdout."""
    result = subprocess.run(list(args), capture_output=True, text=True)
    if result.returncode != 0:
        raise BuildError(f"`{args[0]}` failed: {result.stderr.strip()}")
    return result.stdout


def markdown_section(text: str, title: str) -> str:
    """Return the body under the `## title` heading, up to the next `## ` heading, or "" when the heading is absent."""
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def flatten(text: str) -> str:
    """Fold `text` to ASCII and single spaces, so a term matches across a line wrap."""
    return re.sub(r"\s+", " ", fold(text)).strip()


def section_titles(source: str) -> list[str]:
    """Return each `\\section{...}` title as the class prints it: upper case, `\\&` as `&`, macros dropped."""
    # A section commented out to save space must not count as a heading the page lacks.
    uncommented = re.sub(r"(?<!\\)%.*", "", source)
    titles = re.findall(r"\\section\{((?:[^{}]|\{[^{}]*\})*)\}", uncommented)
    return [re.sub(r"\\[A-Za-z]+\s*|[{}]", "", title).replace("\\&", "&").upper() for title in titles]


# =============================================================================
# Page model
# =============================================================================
# One parse of the -layout text into the pieces an ATS files separately, so
# every check below reads the same rows, bullets and fields.


class Section(Enum):
    """What a section holds, told by the macros under its heading and not by the words in it."""

    ROLES = "experience"
    PROJECTS = "projects"
    EDUCATION = "education"
    SKILLS = "skills"
    OTHER = "other"


# The macro that marks each kind of section, first match first: one `\\job` line makes a section hold roles.
SECTION_MACROS = (("job", Section.ROLES), ("project", Section.PROJECTS), ("entry", Section.EDUCATION), ("skillrow", Section.SKILLS))
# The usual words for each kind, for text with no source beside it.
SECTION_WORDS = (("EXPERIENCE", Section.ROLES), ("PROJECT", Section.PROJECTS), ("EDUCATION", Section.EDUCATION), ("SKILL", Section.SKILLS))


def section_kinds(source: str) -> dict[str, Section]:
    """Return what each section of a `resume.tex` holds, so "Volunteer Work" with `\\job` lines is read as roles."""
    uncommented = re.sub(r"(?<!\\)%.*", "", source)
    bodies = re.split(r"\\section\{(?:[^{}]|\{[^{}]*\})*\}", uncommented)[1:]
    kinds = {}
    for title, body in zip(section_titles(source), bodies):
        kinds[title] = next((kind for macro, kind in SECTION_MACROS if re.search(rf"\\{macro}\b", body)), Section.OTHER)
    return kinds


def usual_kind(title: str) -> Section:
    """Guess what a section holds from its heading, as a reader with no source would."""
    return next((kind for word, kind in SECTION_WORDS if word in title), Section.OTHER)


class Kind(Enum):
    """What a stretch of extracted text is, which decides where a parser files it."""

    EMPLOYER = "employer row"
    ROLE = "role title line"
    PROJECT = "project line"
    BULLET = "bullet"
    SKILL = "Skills row"
    CREDENTIAL = "credential row"
    EDUCATION = "education row"
    DATE = "date"
    LOCATION = "location"
    OTHER = "other line"


@dataclass(frozen=True)
class Segment:
    """One stretch of body text a keyword can match inside: a bullet, one field of a row, or one Skills row."""

    section: str
    kind: Kind
    lines: tuple[str, ...]
    text: str
    # index into `Page.entries` of the role or project this text belongs to
    entry: int | None
    # what the section this text sits in holds
    where: Section = Section.OTHER


@dataclass(frozen=True)
class Entry:
    """A dated role or project line, with the employer it sits under."""

    section: str
    org: str
    name: str
    date: str
    # the row prints no employer of its own, so a parser has to carry one down from a row above
    employerless: bool = False
    # a dated role, where a project is the other kind of entry
    role: bool = False


@dataclass(frozen=True)
class Page:
    """The extracted page split into the contact block, headings, text segments, dated entries and two-field rows."""

    head: tuple[str, ...]
    headings: tuple[str, ...]
    segments: tuple[Segment, ...]
    entries: tuple[Entry, ...]
    # (section, left field, right field) for every row with a right-aligned field
    rows: tuple[tuple[str, str, str], ...]
    # what each section holds, by heading
    kinds: dict[str, Section] = field(default_factory=dict)
    # (line, date) for each role or project line whose date is in a form the build cannot read
    bad_dates: tuple[tuple[str, str], ...] = ()

    def kind(self, section: str) -> Section:
        """Return what `section` holds."""
        return self.kinds.get(section) or usual_kind(section)


def fold(text: str) -> str:
    """Fold ligatures, no-break spaces and curly quotes to the ASCII a recruiter types into a search box."""
    return unicodedata.normalize("NFKC", text).translate(QUOTES)


def join_lines(lines: tuple[str, ...]) -> str:
    """Join wrapped lines into one single-spaced string; a line-final hyphen is real since the class never hyphenates."""
    text = lines[0]
    for line in lines[1:]:
        text += line if text.endswith("-") else f" {line}"
    return re.sub(r"\s+", " ", fold(text))


def area(segment: Segment) -> str:
    """Name where a segment sits the way a parser files it: experience, projects, skills, credentials or education."""
    if segment.kind is Kind.CREDENTIAL:
        return "credentials"
    if segment.kind is Kind.SKILL:
        return "skills"
    where = segment.where if segment.where is not Section.OTHER else usual_kind(segment.section)
    return where.value if where is not Section.SKILLS else "other"


def label_names(label: str) -> list[str]:
    """Split a Skills row label into the topics it joins, as "Licenses and Certifications" into two."""
    return re.split(r"\s+(?:and|&)\s+|\s*/\s*", label)


class _PageBuilder:
    """Walks -layout lines top to bottom and collects a `Page`."""

    def __init__(self, head: tuple[str, ...], titles: set[str], kinds: dict[str, Section]) -> None:
        self._head = head
        self._titles = titles
        self._kinds = kinds
        self._where = Section.OTHER
        self._bad_dates: list[tuple[str, str]] = []
        self._headings: list[str] = []
        self._segments: list[Segment] = []
        self._entries: list[Entry] = []
        self._rows: list[tuple[str, str, str]] = []
        self._section = ""
        self._org = ""
        self._entry: int | None = None
        # a bullet or labelled Skills row still collecting its wrapped lines
        self._open: tuple[Kind, list[str]] | None = None

    def add(self, raw: str) -> None:
        """Feed one -layout line."""
        line = raw.strip()
        if not line:
            self._close()
        elif line in self._titles:
            self._close()
            self._section, self._org, self._entry = line, "", None
            self._where = self._kinds.get(line) or usual_kind(line)
            self._headings.append(line)
        elif line.startswith("•"):
            self._close()
            self._open = (Kind.BULLET, [line.lstrip("• ")])
        # pdftotext indents a bullet's wrapped lines; headings and role lines sit at column 0.
        elif self._open and self._open[0] is Kind.BULLET and raw.startswith(" "):
            self._open[1].append(line)
        elif self._where is Section.SKILLS:
            self._add_skill_line(line)
        else:
            self._close()
            self._add_row(line)

    def build(self) -> Page:
        """Return the finished page."""
        self._close()
        kinds = {title: self._kinds.get(title) or usual_kind(title) for title in self._headings}
        return Page(
            self._head, tuple(self._headings), tuple(self._segments), tuple(self._entries), tuple(self._rows), kinds, tuple(self._bad_dates)
        )

    def _add_skill_line(self, line: str) -> None:
        label = SKILL_LABEL.match(line)
        if label:
            self._close()
            # "Licenses and Certifications" is a credential row as much as either word alone.
            kind = Kind.CREDENTIAL if all(name in CREDENTIAL_LABELS for name in label_names(label.group(1))) else Kind.SKILL
            self._open = (kind, [line])
        elif self._open:
            self._open[1].append(line)
        else:
            # An unlabelled list is still a Skills row to a parser.
            self._open = (Kind.SKILL, [line])

    def _add_row(self, line: str) -> None:
        roles, education = self._where is Section.ROLES, self._where is Section.EDUCATION
        dated = roles or self._where is Section.PROJECTS
        parts = FIELD_GAP.split(line)
        if len(parts) == 1 and dated:
            # A long title leaves pdftotext fewer than three spaces before its date; a longer one wraps the date.
            if ROW_DATE.match(line):
                self._rows.append((self._section, "", line))
                self._segment(Kind.DATE, line)
                return
            if trailing := TRAILING_DATE.match(line) or LOOSE_TRAILING_DATE.match(line):
                parts = list(trailing.groups())
        if len(parts) == 2 and dated and not ROW_DATE.match(parts[1]) and LOOSE_DATE.match(parts[1]):
            # "March 2016 - Present" is a date in a form no check below can read. The line is set aside with no
            # entry, so its bullets are held to no bank file until the date is rewritten.
            self._bad_dates.append((parts[0], parts[1]))
            self._entry = None
            self._segment(Kind.OTHER, parts[0])
            self._segment(Kind.DATE, parts[1])
            return
        if len(parts) == 1 and education:
            # "School | Expected May 2027": the last bar parts the field a parser dates or scores from its line.
            fields = ROW_SEP.split(line)
            if len(fields) > 1:
                parts = [" | ".join(fields[:-1]), fields[-1]]
        if len(parts) == 1 and roles:
            self._set_employer(line)
            return
        if len(parts) != 2:
            self._segment(Kind.EDUCATION if education else Kind.OTHER, line)
            return
        left, right = parts
        self._rows.append((self._section, left, right))
        if education:
            self._segment(Kind.EDUCATION, left)
            self._segment(Kind.EDUCATION, right)
        elif dated and ROW_DATE.match(right):
            self._add_entry(left, right)
        else:
            self._set_employer(left)
            self._segment(Kind.LOCATION, right)

    def _set_employer(self, org: str) -> None:
        self._org, self._entry = org, None
        self._segment(Kind.EMPLOYER, org)

    def _add_entry(self, left: str, date: str) -> None:
        fields = ROW_SEP.split(left)
        if self._where is not Section.ROLES:
            entry, parts = Entry(self._section, "", fields[0], date), [(Kind.PROJECT, left)]
        elif len(fields) == 1:
            # A bare title belongs to the employer row above, which no parser documents carrying down.
            entry, parts = Entry(self._section, self._org, left, date, employerless=True, role=True), [(Kind.ROLE, left)]
        else:
            # "Employer | Title | Location", the line `\job` prints, names its own employer.
            self._org = fields[0]
            entry = Entry(self._section, fields[0], fields[1], date, role=True)
            parts = [(Kind.EMPLOYER, fields[0]), (Kind.ROLE, fields[1]), *((Kind.LOCATION, field) for field in fields[2:])]
        self._entries.append(entry)
        self._entry = len(self._entries) - 1
        for kind, text in (*parts, (Kind.DATE, date)):
            self._segment(kind, text)

    def _segment(self, kind: Kind, *lines: str) -> None:
        self._segments.append(Segment(self._section, kind, lines, join_lines(lines), self._entry, self._where))

    def _close(self) -> None:
        if self._open is not None:
            kind, lines = self._open
            self._open = None
            self._segment(kind, *lines)


def parse_page(layout_text: str, titles: list[str], kinds: dict[str, Section] | None = None) -> Page:
    """Split `pdftotext -layout` output into a `Page`; `titles` finds the headings and `kinds` says what each holds."""
    lines = layout_text.replace("\f", "").splitlines()
    title_set = set(titles)
    start = next((i for i, line in enumerate(lines) if line.strip() in title_set), len(lines))
    head = tuple(line.strip() for line in lines[:start] if line.strip())
    builder = _PageBuilder(head, title_set, kinds or {})
    for raw in lines[start:]:
        builder.add(raw)
    return builder.build()


# =============================================================================
# Bank
# =============================================================================


@dataclass(frozen=True)
class BankEntry:
    """The front matter of one `bank/roles` or `bank/projects` file, plus the name its heading gives it."""

    id: str
    kind: str
    org: str
    title: str
    start: str
    end: str
    name: str
    # the `## Facts` section, folded and single-spaced for keyword matching
    facts: str
    # the `## Avoid` rules: wording a resume must not print about this entry, and the reason the user gave
    avoid: tuple[tuple[re.Pattern[str], str], ...] = ()


@dataclass(frozen=True)
class BankLink:
    """One `## Links` line: its URL, whether it is public, and the names a resume links to it."""

    url: str
    # None when the line marks neither, such as a demo video
    public: bool | None
    names: tuple[str, ...]


@dataclass(frozen=True)
class Bank:
    """What the checks compare a resume against: the profile's name and location, and every role, project, link and skill."""

    entries: tuple[BankEntry, ...]
    # the profile's `- Name:` line, which names the PDF
    name: str
    links: tuple[BankLink, ...] = ()
    # bank bullets that print wording their own entry's `## Avoid` section rules out
    conflicts: tuple[str, ...] = ()
    # every term in the `## Backed` table of `skills.md`, the skills a role or project fact stands behind
    skills: tuple[str, ...] = ()
    # every term on the `- ` lines under `## Listed` in `skills.md`: skills the user lists with no work logged behind them
    listed: tuple[str, ...] = ()
    # word stems from the profile, the skills and every role and project file, which a resume may print as spelled
    vocabulary: frozenset[str] = frozenset()
    # the place on the profile's Location line, such as "City, ST", which every contact block prints
    location: str = ""
    # the profile sites, of LinkedIn and GitHub, that the profile's Contact section lists and a contact block prints
    profile_links: tuple[str, ...] = ()
    # the profile's text, folded and single-spaced, which backs Education and each license and certification
    profile: str = ""
    # the profile's Phone and Email values, which the contact block prints as written; "" when the profile has none
    phone: str = ""
    email: str = ""


def find_bank(folder: Path) -> Path:
    """Return the `bank` folder nearest `folder`: its own, or the first one a folder above it holds."""
    for parent in (folder, *folder.parents):
        candidate = parent / BANK_DIR_NAME
        if (candidate / PROFILE_NAME).is_file():
            return candidate
    raise BuildError(
        f"{folder}: no `{BANK_DIR_NAME}/{PROFILE_NAME}` in this folder or any above it; the `start-bank` skill writes one"
    )


def read_bank_file(path: Path) -> str:
    """Read one bank file as UTF-8, or say what is wrong with it."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise BuildError(f"{path}: missing; `bank/README.md` gives its format") from None
    except UnicodeDecodeError:
        raise BuildError(f"{path}: not UTF-8 text; save it as UTF-8") from None


def front_matter(text: str, path: Path) -> dict[str, str]:
    """Return a role or project file's front matter, or say which field is missing or malformed."""
    blocks = text.split("---")
    if len(blocks) < 3:
        raise BuildError(f"{path}: no front matter between two `---` lines, see `bank/README.md`")
    fields = {key: value.strip() for key, value in re.findall(r"^(\w+): (.*)$", blocks[1], re.MULTILINE)}
    missing = [key for key in ("id", "kind", "org", "title", "start", "end") if not fields.get(key)]
    if missing:
        raise BuildError(f"{path}: front matter lacks {', '.join(missing)}, see `bank/README.md`")
    if fields["kind"] not in ("role", "project"):
        raise BuildError(f"{path}: kind is `{fields['kind']}`; write `role` or `project`")
    for key in ("start", "end"):
        if not BANK_DATE.match(fields[key]) and not (key == "end" and fields[key] == "present"):
            ends = ", or `present`" if key == "end" else ""
            raise BuildError(f"{path}: {key} is `{fields[key]}`; write YYYY-MM, or YYYY when the month is unknown{ends}")
    return fields


def load_bank(bank_dir: Path) -> Bank:
    """Read `profile.md`, every role and project file, and the skills in `skills.md`."""
    entries, links, conflicts, texts = [], [], [], []
    for path in sorted((bank_dir / "roles").glob("*.md")) + sorted((bank_dir / "projects").glob("*.md")):
        text = read_bank_file(path)
        texts.append(text)
        fields = front_matter(text, path)
        heading = re.search(r"^# (.+)$", text, re.MULTILINE)
        # A heading reads "Trailhead Maps, offline trail planner"; the name a resume prints is the part before the comma.
        name = heading.group(1).split(",")[0].strip() if heading else fields["id"]
        # A Fact marked (unconfirmed) backs nothing on a resume until the user confirms it.
        facts_text = flatten("\n".join(line for line in markdown_section(text, "Facts").splitlines() if UNCONFIRMED not in line))
        avoid = read_avoid(text, path)
        entries.append(
            BankEntry(*(fields[key] for key in ("id", "kind", "org", "title", "start", "end")), name, facts_text, avoid)
        )
        # A tailored resume copies bank bullets, so a bullet that breaks its own entry's rule is caught here first.
        bullets = fold(markdown_section(text, "Bullets"))
        for pattern, reason in avoid:
            for match in pattern.finditer(bullets):
                conflicts.append(f'bank/{path.parent.name}/{path.name} has a bullet with "{match.group(0)}": {reason}')
        for line in markdown_section(text, "Links").splitlines():
            match = BANK_LINK.match(line.strip())
            if match:
                url, visibility, names = match.groups()
                public = None if visibility is None else visibility == "public"
                parts = tuple(part.strip() for part in names.split(",")) if names else ()
                links.append(BankLink(normalize_url(url), public, parts))

    profile = read_bank_file(bank_dir / PROFILE_NAME)
    named = re.search(r"^- Name: *(\S.*?) *$", profile, re.MULTILINE)
    if named is None:
        raise BuildError(f"{bank_dir / PROFILE_NAME}: needs a `- Name:` line, see `bank/README.md`")
    contact = markdown_section(profile, "Contact")
    skills_md = read_bank_file(bank_dir / "skills.md")
    # `sources/resumes/` stays out: those are old resumes as sent, typos and all.
    known = vocabulary("\n".join([*texts, profile, skills_md]))
    # "- Location: Portland, OR (confirmed 2026-01-05)." gives the part before the note.
    located = re.search(r"^- Location: *([^(\n]+?) *(?:\(|$)", profile, re.MULTILINE)
    location = located.group(1) if located else ""
    return Bank(
        entries=tuple(entries),
        name=named.group(1),
        links=tuple(links),
        conflicts=tuple(conflicts),
        skills=backed_skills(skills_md),
        listed=listed_skills(skills_md),
        vocabulary=known,
        location=location,
        profile_links=tuple(site for site in PROFILE_SITES if site in contact),
        profile=fold(flatten(profile)),
        phone=contact_value(contact, "Phone"),
        email=contact_value(contact, "Email"),
    )


def contact_value(contact: str, key: str) -> str:
    """Return the value of one `- Key: value` line of the profile's Contact section, without a note in parentheses."""
    found = re.search(rf"^- {key}: *(\S.*?)(?: +\([^()]*\))?\.? *$", contact, re.MULTILINE)
    return found.group(1) if found else ""


# Latin letters that Unicode does not split into a plain letter and an accent.
LATIN_LETTERS = str.maketrans({"ø": "o", "Ø": "O", "ł": "l", "Ł": "L", "ß": "ss", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "đ": "d", "Đ": "D", "ð": "d", "þ": "th", "ı": "i"})


def pdf_name(bank: Bank) -> str:
    """Name the PDF after its owner, as "Jordan_Example_Resume.pdf", so a recruiter's downloads folder says whose it is."""
    # Upload forms mangle accents and symbols in a file name, so the name keeps its plain letters.
    plain = unicodedata.normalize("NFKD", bank.name.translate(LATIN_LETTERS)).encode("ascii", "ignore").decode()
    stem = re.sub(r"[^A-Za-z0-9]+", "_", plain).strip("_")
    return f"{stem}_Resume.pdf" if stem else "Resume.pdf"


def example_banks(bank_dir: Path) -> list[Path]:
    """Return the bank of every made-up person in `examples/`, leaving out `bank_dir` itself."""
    banks = sorted(EXAMPLES_DIR.glob(f"*/{BANK_DIR_NAME}"))
    return [bank for bank in banks if bank != bank_dir and (bank / PROFILE_NAME).is_file()]


def example_names(bank_dir: Path) -> tuple[str, ...]:
    """Return what marks a page as copied from `examples/`: each person's name, employers, projects, email and phone."""
    found: list[str] = []
    for example_dir in example_banks(bank_dir):
        example = load_bank(example_dir)
        profile = (example_dir / PROFILE_NAME).read_text(encoding="utf-8")
        # A project's org can be a plain phrase, such as "Open source", that a real resume may print.
        names = [entry.org if entry.kind == "role" else entry.name for entry in example.entries]
        found += [example.name, *names, *EMAIL.findall(profile), *PHONE.findall(profile)]
    return tuple(dict.fromkeys(found))


def backed_skills(skills_md: str) -> tuple[str, ...]:
    """Return each skill the `## Backed` table of `bank/skills.md` names, a parenthesized alias as its own term."""
    terms = []
    for row in markdown_section(skills_md, "Backed").splitlines():
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        # The header row and the rule under it name no skill.
        if len(cells) < 2 or cells[0] == "Skill" or not cells[0].strip("-: "):
            continue
        terms.extend(part.strip() for part in re.split(r"[,()]", cells[0]) if part.strip())
    return tuple(dict.fromkeys(terms))


def listed_skills(skills_md: str) -> tuple[str, ...]:
    """Return each skill on the `- ` lines under `## Listed` in `bank/skills.md`, a parenthesized alias as its own term."""
    lines = [line[2:] for line in markdown_section(skills_md, "Listed").splitlines() if line.startswith("- ")]
    return tuple(dict.fromkeys(part.strip() for line in lines for part in re.split(r"[,()]", line) if part.strip()))


def read_avoid(text: str, path: Path) -> tuple[tuple[re.Pattern[str], str], ...]:
    """Compile a bank file's `## Avoid` lines, each a backticked pattern and the reason for it."""
    rules = []
    for line in markdown_section(text, "Avoid").splitlines():
        match = BANK_AVOID.match(line.strip())
        if not match:
            continue
        try:
            rules.append((re.compile(match.group(1), re.IGNORECASE), match.group(2)))
        except re.error as error:
            raise BuildError(f"{path}: `## Avoid` pattern `{match.group(1)}` is not a valid regex: {error}") from error
    return tuple(rules)


def normalize_url(url: str) -> str:
    """Drop a trailing slash so "https://example.org/" and "https://example.org" compare equal."""
    return url.rstrip("/")


def bank_dates(date: str) -> tuple[str, str]:
    """Turn "Feb 2019 - Nov 2020", "Jul 2021 - Present" or "Sep 2020" into bank-style ("2019-02", "2020-11")."""
    ends = []
    for part in date.split(" - "):
        if part == "Present":
            ends.append("present")
            continue
        month, _, year = part.rpartition(" ")
        ends.append(f"{year}-{MONTHS.index(month) + 1:02d}" if month else year)
    return ends[0], ends[-1]


def same_date(bank: str, page: str) -> bool:
    """Compare a bank date with a page date; a page may print the year alone, and never a month the bank lacks."""
    if len(bank) == 4:
        # A bank year with no month backs no month, so "Jan 2017" against a bank "2017" is an invented month.
        return page == bank
    return bank[:4] == page if len(page) == 4 else bank == page


def bank_candidates(entry: Entry, bank: Bank) -> list[BankEntry]:
    """Return the bank entries a page row names: roles by org and title, projects by file id or heading name."""
    if entry.role:
        return [b for b in bank.entries if b.kind == "role" and b.org == entry.org and b.title == entry.name]
    slug = re.sub(r"[^a-z0-9]+", "-", entry.name.lower()).strip("-")
    return [b for b in bank.entries if b.kind == "project" and (b.id == slug or b.name.lower() == entry.name.lower())]


def bank_entry(entry: Entry, bank: Bank) -> BankEntry | None:
    """Return the bank entry whose name and dates both match a page row, or None."""
    start, end = bank_dates(entry.date)
    return next(
        (b for b in bank_candidates(entry, bank) if same_date(b.start, start) and same_date(b.end, end)), None
    )


# =============================================================================
# Keywords
# =============================================================================


class Mode(Enum):
    """How the forms on one `keywords.txt` line combine."""

    PLAIN = "plain"
    # "Key Performance Indicator (KPI)": a literal search for either needs both on the page
    PAIR = "pair"
    # "Golang | Go": the first form is the post's spelling; another form counts only as a near miss
    ALIAS = "alias"


class Status(Enum):
    """Where a keyword stands on the page."""

    FOUND = "found"
    PARTIAL = "partial"
    NEAR = "near"
    MISSING = "missing"


@dataclass(frozen=True)
class Keyword:
    """One `keywords.txt` entry."""

    line: str
    required: bool
    mode: Mode
    forms: tuple[str, ...]


@dataclass(frozen=True)
class KeywordList:
    """A parsed `keywords.txt`: the post's title line, if any, and its entries in file order."""

    title: str | None
    keywords: tuple[Keyword, ...]


@dataclass(frozen=True)
class KeywordMatch:
    """Where one keyword landed on the page."""

    keyword: Keyword
    status: Status
    hits: tuple[Segment, ...]
    note: str = ""


def read_keywords(path: Path) -> KeywordList:
    """Read and parse a `keywords.txt` file."""
    return parse_keywords(path.read_text(encoding="utf-8"), str(path))


def parse_keywords(text: str, name: str) -> KeywordList:
    """Parse `keywords.txt`: `#` comments, one `title:` line, `!` for required, `A | B` aliases, `Long (ACR)` pairs."""
    title: str | None = None
    keywords = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("title:"):
            if title is not None:
                raise BuildError(f"{name}:{number}: second `title:` line, keep one")
            title = line[len("title:"):].strip()
            if not title:
                raise BuildError(f"{name}:{number}: `title:` needs the post's job title")
            continue
        required = line.startswith("!")
        entry = line[1:].strip() if required else line
        if "|" in entry:
            mode, forms = Mode.ALIAS, tuple(fold(form.strip()) for form in entry.split("|"))
        elif pair := PAIR_ENTRY.match(entry):
            mode, forms = Mode.PAIR, tuple(map(fold, pair.groups()))
        else:
            mode, forms = Mode.PLAIN, (fold(entry),)
        if not all(forms):
            raise BuildError(f"{name}:{number}: empty term in `{line}`")
        keywords.append(Keyword(line, required, mode, forms))
    return KeywordList(title, tuple(keywords))


def _number_variants(word: str) -> str:
    """Regex for `word` as singular or plural, so "agent" and "agents" are near forms of each other."""
    # An acronym's final S is a letter, not a plural: IDS is not the plural of ID.
    if word.isupper():
        return re.escape(word) + "s?"
    lower = word.lower()
    if lower.endswith("ies"):
        return re.escape(word[:-3]) + "(?:y|ies)"
    if re.search(r"[^aeiou]y$", lower):
        return re.escape(word[:-1]) + "(?:y|ies)"
    if re.search(r"(?:ss|sh|ch|x|z)es$", lower):
        return re.escape(word[:-2]) + "(?:es)?"
    if re.search(r"(?:ss|sh|ch|x|z)$", lower):
        return re.escape(word) + "(?:es)?"
    if lower.endswith("s"):
        return re.escape(word[:-1]) + "s?"
    return re.escape(word) + "s?"


@lru_cache(maxsize=None)
def form_pattern(form: str, near: bool = False) -> re.Pattern[str]:
    """Compile a keyword form the way a literal ATS search reads it, or with `near`, its plural and hyphen variants."""
    letters = [char for char in form if char.isalpha()]
    # Short capitalized forms such as Go, CI and IT match case-sensitively so "go" and "it" in prose do not count.
    flags = 0 if len(letters) <= 3 and any(char.isupper() for char in letters) else re.IGNORECASE
    if near:
        words = re.split(r"[ -]+", form)
        body = "[ -]".join([*map(re.escape, words[:-1]), _number_variants(words[-1])])
    else:
        body = " ".join(map(re.escape, form.split()))
    # +, # and & are part of a term: C is not in C++, Security is not in Security+, R is not in R&D.
    return re.compile(rf"(?<![A-Za-z0-9&]){body}(?![A-Za-z0-9+#&])", flags)


def find_form(form: str, segments: tuple[Segment, ...], near: bool = False) -> tuple[Segment, ...]:
    """Return the segments that contain `form`."""
    pattern = form_pattern(form, near)
    return tuple(segment for segment in segments if pattern.search(segment.text))


def near_text(form: str, segments: tuple[Segment, ...]) -> str:
    """Return the first near form of `form` on the page, as printed."""
    pattern = form_pattern(form, near=True)
    return next(match.group(0) for segment in segments if (match := pattern.search(segment.text)))


def match_keyword(keyword: Keyword, segments: tuple[Segment, ...]) -> KeywordMatch:
    """Decide whether `keyword` is on the page in a form a literal search would find."""
    first = keyword.forms[0]
    hits = [find_form(form, segments) for form in keyword.forms]
    if (keyword.mode is Mode.PAIR and all(hits)) or (keyword.mode is not Mode.PAIR and hits[0]):
        return KeywordMatch(keyword, Status.FOUND, tuple(dict.fromkeys(hit for found in hits for hit in found)))
    if keyword.mode is Mode.PAIR and any(hits):
        present, absent = (keyword.forms if hits[0] else keyword.forms[::-1])
        return KeywordMatch(keyword, Status.PARTIAL, hits[0] or hits[1], f'page has "{present}" but not "{absent}"')
    if keyword.mode is Mode.ALIAS and any(hits[1:]):
        other = next(form for form, found in zip(keyword.forms[1:], hits[1:]) if found)
        found = next(found for found in hits[1:] if found)
        return KeywordMatch(keyword, Status.PARTIAL, found, f'page has "{other}", the post writes "{first}"')
    for form in keyword.forms:
        near = find_form(form, segments, near=True)
        if near:
            return KeywordMatch(keyword, Status.NEAR, near, f'page has only "{near_text(form, near)}", the post writes "{form}"')
    return KeywordMatch(keyword, Status.MISSING, ())


# =============================================================================
# Checks: the PDF itself
# =============================================================================


def check_pages(pdf: Path, bbox: str, report: Report) -> None:
    """Fail on anything but one page; report how full the page is."""
    info = run_tool("pdfinfo", str(pdf))
    if not re.search(r"^Encrypted:\s+no\b", info, re.MULTILINE):
        report.failures.append("PDF is encrypted or permission-protected, and some applicant tracking systems reject secured PDFs")
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
    if pages != 1:
        report.failures.append(f"{pages} pages, cut content until it fits on one")
        return

    page_height = float(PAGE_BOX.search(bbox).group(2))
    lowest_word = max(float(y) for y in re.findall(r'yMax="([\d.]+)"', bbox))
    usable_bottom = page_height - BOTTOM_MARGIN_PT
    fill = lowest_word / usable_bottom
    lines_free = int((usable_bottom - lowest_word) // LINE_HEIGHT_PT)
    message = f"1 page, {fill:.0%} full, about {lines_free} lines free"
    if fill >= PAGE_MIN_FILL:
        report.passes.append(message)
    else:
        report.warnings.append(f"{message}; add a bullet from Facts that earns its line")


def check_overfull(log: str, report: Report) -> None:
    """Fail on each line pdflatex set wider than the text block, which prints past the right margin."""
    overruns = 0
    for match in OVERFULL.finditer(log):
        width, first, last = float(match.group(1)), match.group(2), match.group(3)
        if width < OVERFULL_MAX_PT:
            continue
        overruns += 1
        # The log counts lines in the file TeX was reading, which is the resume source for every line on the page.
        where = f"lines {first}-{last}" if last and last != first else f"line {first}"
        report.failures.append(
            f"text runs {width:.1f}pt past the right margin at {where} of {report.tex.name}, "
            "reword it so the line can break, often before a long hyphenated or linked term"
        )
    if overruns == 0:
        report.passes.append("every line stays inside the margins")


def text_lines(bbox: str) -> list[list[tuple[float, float, float, str]]]:
    """Group the first page's `pdftotext -bbox` words into lines of (left edge, right edge, height, text), left to right."""
    words = sorted(
        ((float(y0) + float(y1)) / 2, float(x0), float(x1), float(y1) - float(y0), text)
        for x0, y0, x1, y1, text in WORD_BOX.findall(bbox.split("</page>")[0])
    )
    # Each word carries its vertical middle first, which the grouping reads and the result drops.
    lines: list[list[tuple[float, float, float, float, str]]] = []
    for word in words:
        # Words on one line share a vertical middle to within a fraction of the text height.
        if lines and word[0] - lines[-1][-1][0] < word[3] / 2:
            lines[-1].append(word)
        else:
            lines.append([word])
    return [sorted((word[1:] for word in line), key=lambda word: word[0]) for line in lines]


def check_column_gaps(bbox: str, report: Report) -> None:
    """Fail on a wide gap inside a line, unless it leads to a job or project date that a line under it reaches."""
    lines = text_lines(bbox)
    problems = []
    # (index of the line, left edge of its date, what the line starts with)
    dated: list[tuple[int, float, str]] = []
    for index, line in enumerate(lines):
        gaps = [
            position
            for position, (left, right) in enumerate(zip(line, line[1:]), start=1)
            if right[0] - left[1] > COLUMN_GAP_HEIGHTS * max(left[2], right[2])
        ]
        if not gaps:
            continue
        after = " ".join(word[3] for word in line[gaps[-1] :])
        if len(gaps) == 1 and not ROW_DATE.match(after) and LOOSE_DATE.match(after):
            # `check_date_format` fails a date in another form and names the form to write.
            continue
        if len(gaps) > 1 or not ROW_DATE.match(after):
            problems.append(f'"{after}" sits apart at the right of its line')
        else:
            start = " ".join(word[3] for word in line[: gaps[0]])
            dated.append((index, line[gaps[0]][0], start[:40]))
    if problems:
        report.failures.append(
            f"{'; '.join(problems[:4])}. Only the date of a job or project line may sit at the right margin;"
            " extractors read anything else there as a second column, so print it after a bar"
        )
    # A date stays with its entry whenever some line between it and the next date runs under it. When every such
    # line stops short, an extractor that groups text by position reads the dates as a column. The last date on the
    # page has no later one to be filed with.
    stacked = [
        start
        for (index, date_left, start), (next_index, _, _) in zip(dated, dated[1:])
        if not any(line[-1][1] >= date_left for line in lines[index + 1 : next_index])
    ]
    if stacked:
        report.failures.append(
            f"no line under {'; '.join(repr(start) for start in stacked)} runs past where its dates begin, so"
            " some extractors file the dates of two entries together; extend one bullet under it with another detail of"
            " the same claim from Facts, such as the tool, the scale or who it served, until its first line reaches the dates;"
            " when Facts hold no such detail, print every date after a bar with `\\documentclass[inlinedates]{resume}`"
        )
    if not problems and not stacked:
        report.passes.append(f"{len(dated)} right-aligned dates, each with a line under it that reaches the date")


def code_points(chars: set[str]) -> str:
    """Name characters as U+XXXX for a report line."""
    return ", ".join(f"U+{ord(char):04X}" for char in sorted(chars))


def source_letters(source: str) -> int:
    """Count the letters and digits a `resume.tex` prints: its text without comments, macro names and link targets."""
    body = re.sub(r"(?<!\\)%.*", "", source)
    body = re.sub(r"\\href\{[^}]*\}|\\(?:documentclass|begin|end)\{[^}]*\}|\\[A-Za-z]+", "", body)
    return sum(char.isalnum() for char in body)


def check_text_layer(layout_text: str, source: str, report: Report) -> None:
    """Fail a missing or garbled text layer; warn on characters a typed search will not match."""
    body = layout_text.replace("\f", "")
    visible = sum(char.isalnum() for char in body)
    expected = source_letters(source)
    words = len(body.split())
    # Ligatures, private-use glyphs, soft hyphens and no-break spaces are what a lost ToUnicode map leaves behind.
    broken = {
        char
        for char in body
        if char in "\ufffd\u00ad\u00a0"
        or 0xE000 <= ord(char) <= 0xF8FF
        or 0xFB00 <= ord(char) <= 0xFB06
        or (ord(char) < 32 and char not in "\n\t")
    }
    lost = visible < MIN_TEXT_SHARE * expected
    if lost:
        report.failures.append(
            f"text layer holds {visible} of the {expected} letters and digits the source prints, so a parser reads a"
            " near-empty page; restore the font and `\\pdfgentounicode` lines of `template/resume.cls`"
        )
    if broken:
        report.failures.append(f"text layer has {code_points(broken)}, which a keyword search reads as junk")
    # The bullet glyph and the apostrophe pdflatex prints for a typed ' are expected.
    unusual = {char for char in body if ord(char) > 126 and not unicodedata.category(char).startswith(("L", "M"))} - broken - {"•", "\u2019"}
    if unusual:
        report.warnings.append(f"{code_points(unusual)} on the page, use straight quotes, a hyphen and plain punctuation")
    if not lost and not broken:
        report.passes.append(f"text layer reads clean, {words} words")


def check_fonts(pdf: Path, report: Report) -> None:
    """Run `pdffonts` on the PDF and check each font it lists."""
    check_font_rows(run_tool("pdffonts", str(pdf)).splitlines()[2:], report)


def check_font_rows(rows: list[str], report: Report) -> None:
    """Fail on a Type 3, unembedded or unmapped font, and on a PDF that holds no space characters."""
    bad = []
    for row in rows:
        fields = row.split()
        # The object ID takes the last two columns, so emb sits fifth from the right and uni third.
        if "Type 3" in row or fields[-5] != "yes" or fields[-3] != "yes":
            bad.append(fields[0])
    if bad:
        report.failures.append(
            f"fonts {', '.join(bad)} are Type 3, unembedded or lack a Unicode map; avoid `\\texttt` and `\\url` fonts"
        )
    # pdftotext infers spaces from glyph positions, so only the font list shows whether the PDF holds real ones.
    spaced = any(SPACE_FONT in row for row in rows)
    if not spaced:
        report.failures.append(
            "PDF holds no space characters, so some parsers read words run together;"
            " keep `\\pdfinterwordspaceon` in `template/resume.cls`"
        )
    if not bad and spaced:
        report.passes.append(f"{len(rows)} fonts embedded with Unicode maps, with real spaces between words")


def check_images(pdf: Path, report: Report) -> None:
    """Warn on any raster image, whose text no parser reads without OCR."""
    images = run_tool("pdfimages", "-list", str(pdf)).splitlines()[2:]
    if images:
        report.warnings.append(f"{len(images)} images on the page; parsers skip the text inside an image, so remove them")


def check_size(pdf: Path, report: Report) -> None:
    """Fail a PDF over the size some applicant tracking systems stop parsing at."""
    size = pdf.stat().st_size
    if size > MAX_PDF_BYTES:
        report.failures.append(f"PDF is {size / 1e6:.1f} MB, and some applicant tracking systems do not parse files over 2.5 MB")


def render_gray(pdf: Path) -> tuple[int, int, bytes]:
    """Render page 1 as 8-bit grayscale and return its width, height and pixels."""
    result = subprocess.run(
        ["pdftoppm", "-gray", "-r", str(INK_DPI), "-f", "1", "-l", "1", str(pdf)], capture_output=True
    )
    header = re.match(rb"P5\s+(\d+)\s+(\d+)\s+255\s", result.stdout)
    if result.returncode != 0 or header is None:
        raise BuildError(f"`pdftoppm` could not render {pdf}: {result.stderr.decode().strip()}")
    return int(header.group(1)), int(header.group(2)), result.stdout[header.end():]


def darkest(image: tuple[int, int, bytes], box: tuple[float, float, float, float]) -> int:
    """Return the darkest gray level inside a word box given in points."""
    width, height, pixels = image
    scale = INK_DPI / 72
    x0, y0 = max(0, int(box[0] * scale)), max(0, int(box[1] * scale))
    x1, y1 = min(width, int(box[2] * scale) + 1), min(height, int(box[3] * scale) + 1)
    return min(min(pixels[row * width + x0 : row * width + x1]) for row in range(y0, y1))


def check_hidden_text(pdf: Path, bbox: str, report: Report) -> None:
    """Fail on words a parser reads but a person cannot see: tiny, off the page, or drawn without ink."""
    width, height = map(float, PAGE_BOX.search(bbox).groups())
    image = render_gray(pdf)
    hidden = []
    # Only page 1 is rendered; a longer resume already fails the page count.
    for *corners, word in WORD_BOX.findall(bbox.split("</page>")[0]):
        x0, y0, x1, y1 = map(float, corners)
        off_page = x0 < 0 or y0 < 0 or x1 > width or y1 > height
        if off_page or y1 - y0 < MIN_WORD_HEIGHT_PT or darkest(image, (x0, y0, x1, y1)) > INK_MAX_GRAY:
            hidden.append(word)
    if hidden:
        report.failures.append(
            f"{len(hidden)} hidden words a parser reads and a person cannot see, delete them: {' '.join(hidden[:12])}"
        )
    else:
        report.passes.append("no hidden text")


def check_injection(layout_text: str, report: Report) -> None:
    """Fail on text that instructs a screening model; warn on a phrase that may only describe the work."""
    flat = re.sub(r"\s+", " ", layout_text)
    hits = [match.group(0) for match in INJECTION.finditer(flat)]
    if hits:
        report.failures.append(f"text addressed to a screening model, delete it: {'; '.join(hits)}")
    soft = [match.group(0) for match in INJECTION_SOFT.finditer(flat)]
    if soft:
        report.warnings.append(f"reads as text addressed to a screening model, reword it unless it describes the work: {'; '.join(soft)}")


# =============================================================================
# Checks: layout a parser depends on
# =============================================================================


def check_headings(page: Page, titles: list[str], bank: Bank, report: Report) -> None:
    """Fail a section title that does not extract as its own line, or a bank's roles left off; warn without Education."""
    split = [title for title in titles if title not in page.headings]
    if split:
        report.failures.append(f"headings not on a line of their own in the text: {', '.join(split)}")
    held = {page.kind(title) for title in titles}
    if Section.ROLES not in held and any(entry.kind == "role" for entry in bank.entries):
        report.failures.append("the bank holds roles and the resume prints none; add a section of `\\job` lines, which parsers read work history from")
    if Section.EDUCATION not in held and "## education" in bank.profile.lower():
        report.warnings.append("`bank/profile.md` lists a school and the resume has no section of `\\entry` lines; add one, since most forms ask for it")
    joined = [title for title in titles if JOINED_HEADING.search(title)]
    if joined:
        report.warnings.append(
            f"headings that join two topics: {', '.join(joined)}; a parser files a section under one type,"
            " so give each section one plain heading"
        )
    if not split and not joined:
        report.passes.append(f"{len(titles)} section headings extract whole, one topic each")


def check_contact(page: Page, bank: Bank, report: Report) -> None:
    """Fail a contact block without the profile's email and phone; warn on a headline, or a missing link or location."""
    head = " ".join(page.head)
    emails = EMAIL.findall(head)
    phones = PHONE.findall(head)
    absent = [value for value in (bank.email, bank.phone) if value and value not in head]
    if absent:
        report.failures.append(
            f"contact block above the first heading lacks {' and '.join(absent)}; print each as `bank/profile.md` gives it"
        )
        return
    if len(emails) > 1 or len(phones) > 1:
        report.warnings.append("contact block lists more than one email or phone; parsers keep the first, so print one of each")
    missing = [link for link in bank.profile_links if link not in head]
    if missing:
        report.warnings.append(f"contact block lacks visible {', '.join(missing)} text; parsers ignore link targets")
    unplaced = bool(bank.location) and bank.location not in head
    if unplaced:
        report.warnings.append(
            f'contact block lacks "{bank.location}", the Location in `bank/profile.md`; recruiters filter on location'
        )
    # A line under the name with no contact detail is a headline or summary, which no parser has a field for.
    stray = [
        line
        for line in page.head[1:]
        if not (EMAIL.search(line) or PHONE.search(line) or WEB_ADDRESS.search(line) or any(value and value in line for value in (bank.location, bank.phone, *CONTACT_LABELS)))
    ]
    if stray:
        report.warnings.append(
            "lines above the first heading that hold no contact detail, move each under a heading or delete it:"
            f" {' / '.join(stray)[:80]}"
        )
    if len(page.head) > CONTACT_MAX_LINES:
        report.warnings.append(f"contact block runs {len(page.head)} lines; keep it to the name and two lines")
    if not missing and not unplaced and not stray and len(page.head) <= CONTACT_MAX_LINES:
        report.passes.append("contact block: name, then location, phone, email and profile links")


def check_contact_links(source: str, report: Report) -> None:
    """Warn on a contact link whose printed text is not its address, since a parser keeps the text and drops the target."""
    head = source.split("\\section{", 1)[0]
    hidden = [
        text
        for url, text in HREF_TEXT.findall(head)
        if text not in CONTACT_LABELS and text.lower().rstrip("/") not in url.lower()
    ]
    if hidden:
        report.warnings.append(
            f"contact links print {', '.join(hidden)} in place of an address; print the address, as linkedin.com/in/<handle>"
        )


def check_date_format(page: Page, report: Report) -> None:
    """Fail a role or project date in a form the checks cannot read, since its dates and figures then go unchecked."""
    if page.bad_dates:
        dates = "; ".join(f'"{date}" on {line[:40]}' for line, date in page.bad_dates)
        report.failures.append(
            f'dates in a form the build cannot read: {dates}. Write each as "Mar 2016 - Present": a three-letter month,'
            " the year, a hyphen with a space each side, and Present for work still going"
        )


def check_dates(page: Page, report: Report) -> None:
    """Warn on a right-aligned date a parser cannot read as a month and year."""
    bad = []
    for section, left, right in page.rows:
        if not any(char.isdigit() for char in right) or EXPECTED_DATE.match(right):
            continue
        # A grade holds digits in most scales, as "GPA: 3.8", "2:1" and "8.7/10" do, and is no date.
        if page.kind(section) is Section.EDUCATION and not LOOSE_DATE.match(right.removeprefix("Expected ")):
            continue
        if not ROW_DATE.match(right):
            bad.append(f'"{right}" on {left[:40]}')
        elif not left:
            bad.append(f'"{right}" sits on a line of its own, shorten the row so the date fits beside it')
        elif page.kind(section) is Section.ROLES and not MONTH_RANGE.match(right):
            bad.append(f'"{right}" on {left[:40]}, add the months')
    if bad:
        report.warnings.append(f"dates parsers misread, write Mon YYYY - Mon YYYY: {'; '.join(bad)}")
    else:
        report.passes.append("every date reads as Mon YYYY")


def check_graduation(page: Page, today: date, report: Report) -> None:
    """Warn when an Education date and the word Expected disagree with today's date."""
    this_month = today.year * 12 + today.month - 1
    for section, _, right in page.rows:
        match = GRADUATION.match(right) if page.kind(section) is Section.EDUCATION else None
        if match is None:
            continue
        expected, when = match.groups()
        month = month_index(when, today)
        if expected and month < this_month:
            report.warnings.append(
                f'"{right}" has passed; ask the user for the conferral date, then update `bank/profile.md` and this row'
            )
        elif not expected and month > this_month:
            report.warnings.append(f'"{right}" is still ahead; write "Expected {right}" so no reader takes the degree as finished')


def check_bullets(page: Page, report: Report) -> None:
    """Warn about bullets that run past the word or line limit, or that wrap for a few stray words."""
    bullets = [segment.lines for segment in page.segments if segment.kind is Kind.BULLET and segment.text.strip()]
    empty = sum(segment.kind is Kind.BULLET and not segment.text.strip() for segment in page.segments)
    if empty:
        report.warnings.append(f"{empty} empty bullet{'s' if empty > 1 else ''}; delete each `\\item` that prints no text")
    if not bullets:
        return
    # Character counts stand in for width; -layout keeps proportional text close enough for a share.
    full_width = max(len(line) for bullet in bullets for line in bullet)
    clean = True
    for bullet in bullets:
        words = sum(len(line.split()) for line in bullet)
        stray = len(bullet[-1].split())
        if len(bullet) > BULLET_MAX_LINES:
            problem = f"runs {len(bullet)} lines, cut it to one claim on one or two"
        elif words > BULLET_MAX_WORDS:
            problem = f"runs {words} words, over the cap of {BULLET_MAX_WORDS}; cut it to one claim, or split it into two bullets"
        elif len(bullet) > 1 and len(bullet[-1]) / full_width < BULLET_MIN_WRAP:
            problem = f"wraps for {stray} word{'s' if stray > 1 else ''}; cut that much so it ends on one line"
        else:
            continue
        clean = False
        report.warnings.append(f'bullet {problem}: "{bullet[0][:50]}..."')
    openers: dict[str, int] = {}
    for bullet in bullets:
        verb = bullet[0].split()[0].lower()
        openers[verb] = openers.get(verb, 0) + 1
    repeated = [f"{verb.title()} opens {count}" for verb, count in openers.items() if count > LEAD_VERB_MAX]
    if repeated:
        clean = False
        report.warnings.append(
            f"{'; '.join(repeated)} bullets, and {LEAD_VERB_MAX} is the most one verb may open;"
            " open each with the verb for what that bullet did, as Cut, Grew, Launched or Replaced"
        )
    if clean:
        single = sum(len(bullet) == 1 for bullet in bullets)
        report.passes.append(f"{len(bullets)} bullets, {single} on one line, none over {BULLET_MAX_WORDS} words")


def check_dashes(source: str, report: Report) -> None:
    """Warn on em and en dashes, which some parsers garble and a typed search does not match."""
    for number, line in enumerate(source.splitlines(), start=1):
        if line.lstrip().startswith("%"):
            continue
        if "\u2014" in line or "\u2013" in line or re.search(r"(?<!-)--(?!-)|---", line):
            report.warnings.append(f"dash on line {number}, use a hyphen, a comma or a new sentence")


def check_symbols(layout_text: str, report: Report) -> None:
    """Warn on spelled-out symbol terms, such as C Sharp, that a search for the real term misses."""
    text = re.sub(r"\s+", " ", layout_text)
    for pattern, literal in SYMBOL_SPELLINGS:
        for match in pattern.finditer(text):
            report.warnings.append(f'"{match.group(0)}" is not how anyone searches it, write {literal}')


# =============================================================================
# Checks: facts against the bank
# =============================================================================


def check_bank_dates(page: Page, bank: Bank, report: Report) -> None:
    """Fail a role or project the bank does not hold, or whose dates differ from its bank entry."""
    checked = 0
    for entry in page.entries:
        label = f"{entry.org}, {entry.name}" if entry.role else entry.name
        candidates = bank_candidates(entry, bank)
        if not candidates:
            source = "org and title" if entry.role else "name from the `# ` heading"
            report.failures.append(
                f'no bank entry matches "{label}"; print the {source} of its bank file, or log the entry in `bank/` first'
            )
            continue
        if bank_entry(entry, bank) is not None:
            checked += 1
            continue
        start = bank_dates(entry.date)[0]
        nearest = min(candidates, key=lambda b: abs(int(b.start[:4]) - int(start[:4])))
        report.failures.append(
            f'"{label}" says {entry.date}, but bank/{nearest.kind}s/{nearest.id}.md says {nearest.start} to {nearest.end}; copy the bank dates'
        )
    if checked and checked == len(page.entries):
        report.passes.append(f"{checked} role and project dates match the bank")


def check_avoided(page: Page, bank: Bank, report: Report) -> None:
    """Fail a role or project whose text prints wording its bank entry's `## Avoid` section rules out."""
    checked = 0
    for index, entry in enumerate(page.entries):
        found = bank_entry(entry, bank)
        if found is None or not found.avoid:
            continue
        checked += len(found.avoid)
        text = " ".join(s.text for s in page.segments if s.entry == index and s.kind is not Kind.DATE)
        for pattern, reason in found.avoid:
            if match := pattern.search(text):
                report.failures.append(
                    f'"{match.group(0)}" in {entry.name} {entry.date}: {reason} (bank/{found.kind}s/{found.id}.md, ## Avoid)'
                )
    if checked and not any("## Avoid" in line for line in report.failures):
        report.passes.append(f"clear of {checked} bank Avoid rule{'s' if checked > 1 else ''}")


def figures(text: str) -> list[str]:
    """Return each figure in `text` as plain digits and a magnitude letter: "6,300+" as "6300", "$96K" as "96k"."""
    return [number.replace(",", "") + MAGNITUDES.get(unit.lower(), "") for number, unit in FIGURE.findall(text)]


def check_figures(page: Page, bank: Bank, report: Report) -> None:
    """Fail a bullet figure that its bank entry's Facts do not state."""
    checked = 0
    for index, entry in enumerate(page.entries):
        found = bank_entry(entry, bank)
        if found is None:
            # `check_bank_dates` fails an entry the bank does not hold, figures and all.
            continue
        backed = set(figures(ISO_DATE.sub(" ", found.facts)))
        for segment in page.segments:
            if segment.entry != index or segment.kind is not Kind.BULLET:
                continue
            for figure in figures(segment.text):
                checked += 1
                if figure not in backed:
                    report.failures.append(
                        f'"{figure}" in a bullet of {entry.name} {entry.date} is not in the Facts of'
                        f" bank/{found.kind}s/{found.id}.md; copy the figure as Facts state it, or log it there first; a Fact marked {UNCONFIRMED} does not count"
                    )
    if checked and not any("is not in the Facts of" in line for line in report.failures):
        report.passes.append(f"all {checked} bullet figures are in their bank Facts")


def check_skill_rows(page: Page, bank: Bank, report: Report) -> None:
    """Fail a Skills row item the inventory, Facts and profile do not hold, and a credential the profile does not list."""
    facts = " ".join(entry.facts for entry in bank.entries)
    inventory = bank.skills + bank.listed

    def held(term: str) -> bool:
        pattern = form_pattern(term, near=True)
        # "ETL" is held by the inventory's "ETL pipelines", and "REST APIs" on the page by its "REST API".
        return bool(pattern.search(facts)) or any(
            pattern.search(skill) or form_pattern(skill, near=True).search(term) for skill in inventory
        )

    unknown: dict[str, None] = {}
    unlisted: dict[str, None] = {}
    for segment in page.segments:
        if segment.kind not in (Kind.SKILL, Kind.CREDENTIAL):
            continue
        label = SKILL_LABEL.match(segment.text)
        # A row labelled Languages or Awards may print what the profile lists, with no work logged behind it.
        profiled = label is not None and all(name in PROFILE_LABELS for name in label_names(label.group(1)))
        body = SKILL_LABEL.sub("", segment.text, count=1)
        for item in (part.strip() for part in re.split(r"[,()]", body)):
            if not item:
                continue
            if segment.kind is Kind.CREDENTIAL:
                if fold(item) not in bank.profile:
                    unlisted[item] = None
            elif not held(item) and not (profiled and fold(item) in bank.profile):
                unknown[item] = None
    if unlisted:
        report.failures.append(
            f"credential rows print {', '.join(unlisted)}, which `bank/profile.md` does not list;"
            " log each under its `## Licenses` or `## Certifications` first, or drop it"
        )
    if unknown:
        report.failures.append(
            f"Skills rows print {', '.join(unknown)}, which `bank/skills.md` and the bank's Facts do not hold;"
            " log each in `bank/skills.md` with its evidence first, the post's spelling as an alias in parentheses,"
            " or drop it; a license or certification goes in a row labelled `Licenses` or `Certifications`, and a"
            " language or an award under `## Languages` or `## Honors` in `bank/profile.md`, in a row labelled"
            " `Languages` or `Awards`"
        )
    if not unknown and not unlisted and any(segment.kind in (Kind.SKILL, Kind.CREDENTIAL) for segment in page.segments):
        report.passes.append("every Skills row item is in the bank")


def check_unbacked_terms(page: Page, bank: Bank, gaps: tuple[str, ...], report: Report) -> None:
    """Fail a bullet that claims a Listed skill or a `## Gaps` term its own bank entry's Facts do not state."""
    # A Listed skill the post names sits under `## Gaps` too; the Listed reason wins, since it says where the term may print.
    reasons = {term: f"`{JOB_NAME}` lists it under `## Gaps`; cut it from the bullet" for term in gaps}
    reasons.update({skill: "`bank/skills.md` lists it with no work behind it; move it to a Skills row" for skill in bank.listed})
    if not reasons:
        return
    claimed = False
    for index, entry in enumerate(page.entries):
        found = bank_entry(entry, bank)
        if found is None:
            # `check_bank_dates` fails an entry the bank does not hold, bullets and all.
            continue
        bullets = [segment.text for segment in page.segments if segment.entry == index and segment.kind is Kind.BULLET]
        for term, reason in reasons.items():
            pattern = form_pattern(term, near=True)
            # Facts are the source of truth: a term they state is backed here, whatever a stale Gaps line says.
            if pattern.search(found.facts) or not any(pattern.search(bullet) for bullet in bullets):
                continue
            claimed = True
            report.failures.append(
                f'"{term}" is in a bullet of {entry.name} {entry.date}, and {reason},'
                f" or log the work in bank/{found.kind}s/{found.id}.md first"
            )
    if not claimed:
        report.passes.append("no bullet claims a Listed skill or a `## Gaps` term")


def check_education(page: Page, bank: Bank, report: Report) -> None:
    """Fail a school, degree, major or grade in Education that the profile does not list."""
    rows = [segment.text for segment in page.segments if segment.kind is Kind.EDUCATION]
    if not rows:
        return
    profile = bank.profile.lower()
    text = " ".join(rows)
    words = {word.lower() for word in WORD.findall(text) if len(word) >= EDUCATION_WORD_MIN and word not in MONTHS}
    unlisted = sorted(word for word in words - EDUCATION_WORDS if not re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", profile))
    unlisted += [figure for figure in figures(text) if figure not in figures(profile)]
    # The page spells a level out where the profile may abbreviate it, so each level is matched by its own forms.
    unlisted += [level for level, forms in DEGREE_FORMS.items() if re.search(rf"\b{level}", text) and not re.search(forms, profile)]
    if unlisted:
        report.failures.append(
            f"Education prints {', '.join(dict.fromkeys(unlisted))}, which `bank/profile.md` does not list;"
            " copy the school, degree and grade from the profile, or log them there first"
        )
    else:
        report.passes.append("Education matches the profile")


def check_role_employers(page: Page, report: Report) -> None:
    """Warn on role rows that print no employer of their own, which a parser would have to carry down from above."""
    # A job line too long for one line leaves its dates on the next, and the first reads as an employer row.
    wrapped = [s.text for s in page.segments if s.kind is Kind.EMPLOYER and s.entry is None and ROW_SEP.search(s.text)]
    if wrapped:
        report.failures.append(
            f"job lines that wrap before their dates: {'; '.join(text[:60] for text in wrapped)}."
            " Shorten each to one line; a parser can cut the employer at the wrap"
        )
    bare = [f"{entry.name} {entry.date}" for entry in page.entries if entry.employerless]
    if bare:
        report.warnings.append(
            f"role rows with no employer on them: {'; '.join(bare)}; write each as"
            " `\\job{Employer}{Title}{Location}{Dates}`"
        )
    elif any(entry.role for entry in page.entries):
        report.passes.append("every role line prints its employer")


def month_index(when: str, today: date) -> int:
    """Count months since year 0 for "May 2023", or for "Present" as of `today`."""
    if when == "Present":
        return today.year * 12 + today.month - 1
    month, _, year = when.rpartition(" ")
    return int(year) * 12 + (MONTHS.index(month) if month else 0)


def experience_months(entries: list[Entry], today: date) -> int:
    """Count the months `entries` cover with overlaps counted once, as a date-based parser totals work experience."""
    months: set[int] = set()
    for entry in entries:
        start, _, end = entry.date.partition(" - ")
        months.update(range(month_index(start, today), month_index(end or start, today) + 1))
    return len(months)


def check_experience_months(page: Page, today: date, report: Report) -> None:
    """Note the months of experience a date-based parser computes, with and without internships and co-ops."""
    roles = [entry for entry in page.entries if entry.role]
    if not roles:
        return
    total = experience_months(roles, today)
    regular = experience_months([entry for entry in roles if not TRAINEE_TITLE.search(entry.name)], today)
    note = f"dated roles cover {total} months ({total / 12:.1f} years) with overlaps counted once"
    report.notes.append(note if regular == total else f"{note}; {regular} without intern, co-op, trainee and student rows")


def check_years_asked(post: str, page: Page, today: date, report: Report) -> None:
    """Note each experience floor in the post that the dated roles fall short of, with or without trainee rows."""
    roles = [entry for entry in page.entries if entry.role]
    floors = sorted({int(years) for years in YEARS_ASKED.findall(post)} - {0})
    if not roles or not floors:
        return
    total = experience_months(roles, today)
    regular = experience_months([entry for entry in roles if not TRAINEE_TITLE.search(entry.name)], today)
    short = [f"{years}+" for years in floors if years * 12 > total]
    trainee_only = [f"{years}+" for years in floors if regular < years * 12 <= total]
    if short:
        report.notes.append(
            f"the post asks for {' and '.join(short)} years of experience, more than the {total / 12:.1f} the dated"
            " roles cover; list it under `## Gaps`"
        )
    if trainee_only:
        report.notes.append(
            f"the post asks for {' and '.join(trainee_only)} years of experience, which the dated roles meet only when"
            f" Intern and Co-Op months count ({regular / 12:.1f} years without them)"
        )


def check_durations(layout_text: str, report: Report) -> None:
    """Note stated durations such as "3 years of Python", which must come from bank Facts."""
    hits = DURATION.findall(flatten(layout_text))
    if hits:
        report.notes.append(f"stated durations, each must be in bank Facts: {', '.join(hits)}")


def check_degree(page: Page, report: Report) -> None:
    """Warn when Education abbreviates the degree without its level in words."""
    education = " ".join(segment.text for segment in page.segments if segment.kind is Kind.EDUCATION)
    if DEGREE_ABBREVIATION.search(education) and not DEGREE_WORD.search(education):
        report.warnings.append(
            "write the degree level in words, as Bachelor of Science in Biology; a search for Bachelor misses B.S."
        )


# =============================================================================
# Checks: spelling
# =============================================================================


def word_stems(word: str) -> set[str]:
    """Return `word` in lower case, plus what is left once one common English ending comes off it."""
    lower = word.lower()
    stems = {lower}
    for ending in WORD_ENDINGS:
        base = lower[: -len(ending)]
        if not lower.endswith(ending) or len(base) < 3:
            continue
        # "provisioned" leaves "provision", "automated" leaves "automate", "debugged" leaves "debug".
        stems.update((base, base + "e", base[:-1] if base[-1] == base[-2] else base))
        if ending in ("ies", "ied"):
            stems.add(base + "y")
    return stems


def vocabulary(text: str) -> frozenset[str]:
    """Return the stems of every word in `text`, the form `check_spelling` looks a page word up in."""
    return frozenset(stem for word in WORD.findall(fold(text)) for stem in word_stems(word.strip("'")))


@lru_cache(maxsize=1)
def system_words() -> frozenset[str] | None:
    """Return the system word list in lower case, or None on a machine that has none."""
    if not WORD_LIST.is_file():
        return None
    return frozenset(line.strip().lower() for line in WORD_LIST.read_text(encoding="utf-8").splitlines())


def check_spelling(page: Page, known: frozenset[str], words: frozenset[str] | None, report: Report) -> None:
    """Warn on body words that `known` and the system word list both lack, which is how a typo looks."""
    if words is None:
        report.notes.append(f"no word list at {WORD_LIST}, so spelling was not checked")
        return
    # A dict keeps each word once, in the order the page prints them.
    unknown: dict[str, None] = {}
    for segment in page.segments:
        # A date holds only month names and digits, and the short month names are in no word list.
        if segment.kind is Kind.DATE:
            continue
        for raw in WORD.findall(segment.text):
            word = raw.strip("'")
            # An acronym such as ETL or KPIs is spelled by its letters, which no word list can vouch for.
            if word.rstrip("s").isupper() or word in MONTHS:
                continue
            stems = word_stems(word)
            if stems.isdisjoint(known) and stems.isdisjoint(words):
                unknown[word] = None
    if unknown:
        report.warnings.append(
            f"spelling: the bank, the post and the system word list all lack {', '.join(unknown)};"
            " fix a typo, or log a real term in the bank first"
        )
    else:
        report.passes.append("every word is in the bank, the post or the system word list")


# =============================================================================
# Checks: links and the example
# =============================================================================


def copied_facts(bank_dir: Path) -> list[str]:
    """Return a message for each Fact in `bank_dir` that repeats one of a made-up person's, word for word."""
    def facts(folder: Path) -> dict[str, Path]:
        found = {}
        for path in sorted(folder.glob("roles/*.md")) + sorted(folder.glob("projects/*.md")):
            for line in markdown_section(read_bank_file(path), "Facts").splitlines():
                if line.startswith("- "):
                    found[line] = path
        return found

    example = {line for example_dir in example_banks(bank_dir) for line in facts(example_dir)}
    if not example:
        return []
    return [
        f'{path.parent.name}/{path.name} repeats a Fact of a made-up person in `examples/`: "{line[2:60]}..."; replace it with the user\'s own'
        for line, path in facts(bank_dir).items()
        if line in example
    ]


def check_example(layout_text: str, names: tuple[str, ...], report: Report) -> None:
    """Fail a resume that prints one of the example person's names, which only a copy from `examples/` does."""
    flat = flatten(layout_text).lower()
    copied = [name for name in names if name.lower() in flat]
    if copied:
        report.failures.append(
            f"page prints {', '.join(copied)}, which belongs to a made-up person in `examples/`;"
            " replace it with a fact from this resume's own `bank/`, or delete `examples/` if the name is truly the user's"
        )


def check_links(source: str, layout_text: str, bank: Bank, report: Report) -> None:
    """Fail on a link to a private repo; warn when the page names public work without linking it."""
    hrefs = {normalize_url(url) for url in HREF.findall(source) if not url.startswith("mailto:")}
    by_url = {link.url: link for link in bank.links}
    private = sorted(url for url in hrefs if by_url.get(url) and by_url[url].public is False)
    if private:
        report.failures.append(f"links a private repo: {', '.join(private)}; remove the `\\href`")
    # A profile link such as github.com/jordan-example has no repo part, so only repo links need a bank line.
    unknown = sorted(url for url in hrefs if GITHUB_REPO.match(url) and url not in by_url)
    if unknown:
        report.warnings.append(f"links {', '.join(unknown)}, which no bank `## Links` line marks public or private; add that line to its entry")

    flat = flatten(layout_text)
    unlinked, linked = {}, set()
    for link in bank.links:
        if not link.public or not link.names:
            continue
        # Several entries can share a URL, such as a product page; one `\href` covers every mention.
        named = next((name for name in link.names if re.search(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", flat)), None)
        if named is None:
            continue
        if link.url in hrefs:
            linked.add(link.url)
        else:
            unlinked.setdefault(link.url, named)
    for url, name in unlinked.items():
        tex_name = name.replace("&", "\\&")
        report.warnings.append(f'"{name}" is public work with no link; wrap its first mention in \\href{{{url}}}{{{tex_name}}}')
    if not private and not unlinked:
        report.passes.append(f"links {len(linked)} public projects and no private repos")


# =============================================================================
# Checks: keywords
# =============================================================================


def describe_title(title: str, page: Page, segments: tuple[Segment, ...]) -> str:
    """Say where the post's title, or its longest tail of two or more words, lands on the page."""
    # A qualifier names the team or the place, not the job: "(Platform)", ", Progressive Care", " - Remote".
    words = re.split(r",| - ", re.sub(r"\s*\([^)]*\)\s*$", "", title))[0].split()
    for start in range(0, max(1, len(words) - 1)):
        tail = " ".join(words[start:])
        hits = find_form(tail, segments)
        if not hits:
            continue
        roles = [hit for hit in hits if hit.kind is Kind.ROLE]
        if any(page.entries[hit.entry].date.endswith("Present") for hit in roles):
            where = "the current role title line"
        elif roles:
            where = "a past role title line"
        else:
            where = f"a {hits[0].kind.value} only; parsers take titles from role title lines"
        return f'title "{title}": page has "{tail}" on {where}'
    return f'title "{title}": not on the page'


def note_role_spread(page: Page, bank: Bank, matches: list[KeywordMatch], report: Report) -> None:
    """Note page roles whose bank Facts back a keyword that their bullets leave out."""
    roles = {
        index: found
        for index, entry in enumerate(page.entries)
        if entry.role and (found := bank_entry(entry, bank)) is not None
    }
    unused = []
    for match in matches:
        on_page = {hit.entry for hit in match.hits if hit.entry in roles}
        backed = {
            index
            for index, role in roles.items()
            if any(form_pattern(form).search(role.facts) for form in match.keyword.forms)
        }
        left_out = [f"{page.entries[index].name} {page.entries[index].date}" for index in sorted(backed - on_page)]
        if match.keyword.required and left_out:
            report.notes.append(
                f'required "{match.keyword.forms[0]}" is in {len(on_page)} roles; Facts also back it in {"; ".join(left_out)}'
            )
        elif left_out and not on_page:
            unused.append(f"{match.keyword.forms[0]} ({'; '.join(left_out)})")
    if unused:
        report.notes.append(f"in no role bullet, though page roles' Facts back them: {', '.join(unused)}")


def check_keywords(page: Page, keywords: KeywordList, bank: Bank, report: Report) -> None:
    """Report each `keywords.txt` entry as found, near, partial or missing, and where the found ones sit."""
    if not keywords.keywords:
        report.warnings.append(f"{KEYWORDS_NAME} is empty")
        return
    segments = tuple(segment for segment in page.segments if segment.kind is not Kind.DATE)
    matches = [match_keyword(keyword, segments) for keyword in keywords.keywords]
    found = [match for match in matches if match.status is Status.FOUND]
    missing = [match.keyword.line for match in matches if match.status is Status.MISSING]

    for match in matches:
        if all(word.lower() in STOPWORDS for form in match.keyword.forms for word in form.split()):
            report.warnings.append(
                f'keyword "{match.keyword.line}" is only stopwords, which some searches ignore; spell it out'
            )
        if match.keyword.required and match.status is Status.MISSING:
            report.failures.append(f'required keyword "{match.keyword.forms[0]}" is not on the page; add a bullet from an entry whose Facts back it')
        elif match.keyword.required and match.status is not Status.FOUND:
            report.failures.append(f'required keyword "{match.keyword.line}": {match.note}')
        elif match.status in (Status.PARTIAL, Status.NEAR):
            report.warnings.append(f'keyword "{match.keyword.line}": {match.note}')
    summary = f"keywords {len(found)}/{len(matches)}"
    if len(found) == len(matches):
        report.passes.append(summary)
    elif missing:
        report.warnings.append(f"{summary}, missing: {', '.join(missing)}; add each from Facts, or note under `## Build notes` that it does not fit")
    else:
        report.warnings.append(f"{summary}, the rest only as other forms")

    skills_only, no_role = [], []
    for match in found:
        where = {area(hit) for hit in match.hits}
        if where == {"skills"} and match.keyword.required:
            report.warnings.append(
                f'required "{match.keyword.forms[0]}" is only in a Skills row; show it in a role or project bullet'
            )
        elif where == {"skills"}:
            skills_only.append(match.keyword.forms[0])
        elif "projects" in where and "experience" not in where:
            no_role.append(match.keyword.forms[0])
    if skills_only:
        report.notes.append(f"only in Skills rows, so no dated role backs them: {', '.join(skills_only)}")
    if no_role:
        report.notes.append(f"in projects but no role, so they carry no experience dates: {', '.join(no_role)}")
    note_role_spread(page, bank, matches, report)
    if keywords.title:
        report.notes.append(describe_title(keywords.title, page, segments))


@dataclass(frozen=True)
class JobPost:
    """The parts of `job.md` a keyword list answers to: the post as saved, and the gaps the bank cannot back."""

    post: str
    gaps: str
    # the term each `## Gaps` line names, which no bullet may claim
    gap_terms: tuple[str, ...] = ()


def gap_terms(section: str) -> tuple[str, ...]:
    """Return the terms a `## Gaps` section names: the part of each `- ` line before its colon, split where it joins several."""
    heads = [line[2:].split(":", 1)[0] for line in section.splitlines() if line.startswith("- ")]
    # "Six Sigma and CCRN" names two terms, and "Return on investment (ROI)" one term in two spellings.
    parts = (part.strip() for head in heads for part in re.split(r"[,()]|\s+(?:and|or)\s+", fold(head)))
    return tuple(dict.fromkeys(part for part in parts if part))


def read_job_post(folder: Path) -> JobPost | None:
    """Return the flattened `## Post` and `## Gaps` of the folder's `job.md`, or None when it saves no post."""
    job = folder / JOB_NAME
    if not job.is_file():
        return None
    text = job.read_text(encoding="utf-8")
    post = flatten(markdown_section(text, "Post"))
    gaps = markdown_section(text, "Gaps")
    return JobPost(post, flatten(gaps), gap_terms(gaps)) if post else None


def check_generator(folder: Path, report: Report) -> None:
    """Warn when a job folder does not record the generator version this build is, so a later reader knows its rules."""
    job = folder / JOB_NAME
    if not job.is_file():
        return
    # Only the header counts, as with Status: a "- Generator:" line inside the pasted post never does.
    recorded = GENERATOR_LINE.search(job.read_text(encoding="utf-8").split("\n## ", 1)[0])
    if recorded is None or recorded.group(1).strip() != GENERATOR:
        found = f"says {recorded.group(1).strip() or 'nothing'}" if recorded else "has no `- Generator:` line"
        report.warnings.append(f"{JOB_NAME} {found}, and this build is generator {GENERATOR}; write `- Generator: {GENERATOR}` in its header")


def check_post(job: JobPost, keywords: KeywordList, page: Page, bank: Bank, report: Report) -> None:
    """Warn when the keyword list or the page strays from the saved post: a term the post never writes, or a skill it skips."""
    strays = []
    for keyword in keywords.keywords:
        # An alias line leads with the post's spelling; a pair is the post's whenever it writes either form.
        forms = keyword.forms if keyword.mode is Mode.PAIR else keyword.forms[:1]
        # The degree line stands for whatever the post calls the degree, "BS" included; the Education row proves it.
        if DEGREE_LEVEL.fullmatch(forms[0]) or any(form_pattern(form).search(job.post) for form in forms):
            continue
        near = next((found.group(0) for form in forms if (found := form_pattern(form, near=True).search(job.post))), None)
        strays.append(f'{forms[0]} (the post writes "{near}")' if near else forms[0])
    if strays:
        report.warnings.append(
            f"{KEYWORDS_NAME} terms the saved post never writes this way: {', '.join(strays)};"
            " copy the post's spelling, or drop a term the post does not name"
        )

    listed = [form for keyword in keywords.keywords for form in keyword.forms]
    skipped = [
        skill
        for skill in bank.skills
        if form_pattern(skill, near=True).search(job.post)
        # "route optimization" on the list covers the bank's "Dynamic route optimization", and the reverse.
        and not any(form_pattern(skill, near=True).search(form) or form_pattern(form).search(skill) for form in listed)
        and not form_pattern(skill, near=True).search(job.gaps)
    ]
    if skipped:
        report.warnings.append(
            f"the post names {', '.join(skipped)}, which `bank/skills.md` backs;"
            f" add each to {KEYWORDS_NAME} in the post's spelling"
        )
    if not strays and not skipped:
        report.passes.append(f"{KEYWORDS_NAME} holds the post's own terms and every backed skill it names")

    # A Listed skill has no fact for a bullet, but a recruiter's literal search still finds it in a Skills row.
    printed = " ".join(segment.text for segment in page.segments)
    unprinted = [
        skill
        for skill in bank.listed
        if form_pattern(skill, near=True).search(job.post) and not form_pattern(skill, near=True).search(printed)
    ]
    if unprinted:
        report.warnings.append(
            f"the post names {', '.join(unprinted)}, which `bank/skills.md` lists with no work behind it;"
            " print each in a Skills row in the post's spelling, and keep it out of bullets"
        )


# =============================================================================
# Driver
# =============================================================================


def resolve_tex(target: Path) -> Path:
    """Accept a `resume.tex` path or the folder that holds one."""
    tex = target / "resume.tex" if target.is_dir() else target
    if not tex.is_file():
        raise BuildError(f"{target}: no `resume.tex` found")
    return tex.resolve()


def submitted(folder: Path) -> str | None:
    """Return the submission details from the folder's `job.md`, or None while the resume is still a draft."""
    job = folder / JOB_NAME
    # Only the header counts: a "- Submitted:" line inside the pasted post freezes nothing.
    match = SUBMITTED.search(job.read_text(encoding="utf-8").split("\n## ", 1)[0]) if job.is_file() else None
    return match.group(1).strip() if match else None


def build(target: Path, bank: Bank, example: tuple[str, ...] = ()) -> Report:
    """Compile one resume, copy the PDF beside it, and run every check; `example` holds the names it must not print."""
    tex = resolve_tex(target)
    source = tex.read_text(encoding="utf-8")
    keywords_file = tex.parent / KEYWORDS_NAME
    # Parse keywords.txt before compiling so a malformed file fails fast.
    keywords = read_keywords(keywords_file) if keywords_file.is_file() else None
    built_pdf = compile_pdf(tex)

    pdf = tex.parent / pdf_name(bank)
    layout_text = run_tool("pdftotext", "-layout", str(built_pdf), "-")
    bbox = run_tool("pdftotext", "-bbox", str(built_pdf), "-")
    text_file = tex.parent / BUILD_DIR_NAME / "resume.txt"
    text_file.write_text(layout_text, encoding="utf-8")
    # The same page in the order the PDF stores it, which a parser that does not sort by position reads.
    raw_text = run_tool("pdftotext", "-raw", str(built_pdf), "-")
    (tex.parent / BUILD_DIR_NAME / "resume.raw.txt").write_text(raw_text, encoding="utf-8")
    titles = section_titles(source)
    page = parse_page(layout_text, titles, section_kinds(source))

    # `base/` has no `job.md`, and a post the user has not pasted yet gives the checks nothing to answer to.
    job = read_job_post(tex.parent)
    today = date.today()

    report = Report(tex=tex, pdf=pdf, text_file=text_file)
    check_pages(built_pdf, bbox, report)
    # A TeX log can hold bytes that are not UTF-8; decode leniently rather than stop the build.
    check_overfull(built_pdf.with_suffix(".log").read_text(errors="replace"), report)
    check_column_gaps(bbox, report)
    check_text_layer(layout_text, source, report)
    check_fonts(built_pdf, report)
    check_images(built_pdf, report)
    check_size(built_pdf, report)
    check_hidden_text(built_pdf, bbox, report)
    check_injection(layout_text, report)
    check_headings(page, titles, bank, report)
    check_date_format(page, report)
    check_generator(tex.parent, report)
    check_contact(page, bank, report)
    check_contact_links(source, report)
    check_dates(page, report)
    check_graduation(page, today, report)
    check_bullets(page, report)
    check_dashes(source, report)
    check_symbols(layout_text, report)
    check_degree(page, report)
    check_durations(layout_text, report)
    check_bank_dates(page, bank, report)
    check_avoided(page, bank, report)
    check_figures(page, bank, report)
    check_skill_rows(page, bank, report)
    check_unbacked_terms(page, bank, job.gap_terms if job else (), report)
    check_education(page, bank, report)
    check_role_employers(page, report)
    check_experience_months(page, today, report)
    if job is not None:
        check_years_asked(job.post, page, today, report)
    check_spelling(page, bank.vocabulary | vocabulary(job.post if job else ""), system_words(), report)
    check_example(layout_text, example, report)
    check_links(source, layout_text, bank, report)
    if keywords is not None:
        check_keywords(page, keywords, bank, report)
        if job is not None:
            check_post(job, keywords, page, bank, report)
    # A failing build leaves no PDF under the name that ships, so a stale or broken one cannot be sent by mistake.
    if report.failures:
        pdf.unlink(missing_ok=True)
    else:
        shutil.copyfile(built_pdf, pdf)
    return report


def relative(path: Path) -> str:
    """Show `path` relative to the repo when it sits inside it."""
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def print_report(report: Report) -> None:
    """Print one resume's checks, failures first."""
    print(f"{relative(report.tex)}  (generator {GENERATOR})")
    print(f"  pdf   {relative(report.pdf)}" if not report.failures else f"  pdf   {report.pdf.name} is not written until every FAIL is fixed")
    print(f"  text  {relative(report.text_file)}")
    for label, items in (("FAIL", report.failures), ("warn", report.warnings), ("info", report.notes), ("ok", report.passes)):
        for item in items:
            print(f"  {label:<5} {item}")


def main() -> int:
    """Build every resume named on the command line; return 1 if any must not ship."""
    parser = argparse.ArgumentParser(description="Compile resumes and check each PDF the way a parser reads it, and against the bank.")
    parser.add_argument("targets", nargs="+", type=Path, help="`resume.tex` files or folders that hold one")
    args = parser.parse_args()

    missing_tools = [f"`{tool}` ({fix})" for tool, fix in REQUIRED_TOOLS.items() if shutil.which(tool) is None]
    if missing_tools:
        print(f"missing tools: {', '.join(missing_tools)}", file=sys.stderr)
        return 2

    failed = False
    # Each resume answers to the bank nearest it, so `examples/` and the user's own folders never share facts.
    banks: dict[Path, Bank] = {}
    for target in args.targets:
        try:
            bank_dir = find_bank(resolve_tex(target).parent)
            if bank_dir not in banks:
                banks[bank_dir] = load_bank(bank_dir)
                # A bank seeded from `examples/` would pass every other check, since its resumes match it.
                for conflict in (*banks[bank_dir].conflicts, *copied_facts(bank_dir)):
                    print(f"FAIL  {conflict}")
                    failed = True
            # A sent resume stays byte for byte what the employer has, so a submitted folder is never recompiled.
            sent = submitted(resolve_tex(target).parent)
            if sent is not None:
                print(f"{relative(resolve_tex(target))}  skipped, submitted {sent}; copy it to a new folder to change it")
                continue
            report = build(target, banks[bank_dir], example_names(bank_dir))
        except BuildError as error:
            print(f"FAIL  {error}", file=sys.stderr)
            failed = True
            continue
        print_report(report)
        failed = failed or bool(report.failures)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
