% =============================================================================
% Module Overview
% =============================================================================
% The layout every resume in this repo shares: page geometry, font, section
% rules, and the entry macros `\resumeheader`, `\entry`, `\job`, `\project`
% and `\skillrow`, plus the `bullets` list. It holds no facts about anyone;
% those live in each `resume.tex` and in `bank/`.

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{resume}[2026/11/15 One-page resume layout]

% `\documentclass[inlinedates]{resume}` prints each job and project date after a
% bar in place of the right margin, for a resume whose bullets are too short to
% reach the dates.
\newif\if@inlinedates
\DeclareOption{inlinedates}{\@inlinedatestrue}
% `\documentclass[a4paper]{resume}` prints on A4 in place of US Letter.
\newcommand{\resume@paper}{letterpaper}
\DeclareOption{a4paper}{\renewcommand{\resume@paper}{a4paper}}
\ProcessOptions\relax

\LoadClass[11pt]{article}

% =============================================================================
% Page, font, and text extraction
% =============================================================================
\RequirePackage[T1]{fontenc}
% Times, the face recruiters see most; NimbusRomNo9L ships with BasicTeX and TeX Live.
\RequirePackage{mathptmx}
\RequirePackage[\resume@paper, top=0.4in, bottom=0.4in, left=0.5in, right=0.5in]{geometry}
\RequirePackage{enumitem}
\RequirePackage{xcolor}
\RequirePackage[colorlinks=true, urlcolor=blue!60!black, linkcolor=black, pdfborder={0 0 0}]{hyperref}

% Map every glyph to Unicode so ATS parsers read real words. Needs pdflatex.
\input{glyphtounicode}
\pdfgentounicode=1
% The apostrophe prints curled and extracts straight, so a search for "team's" finds it.
\pdfglyphtounicode{quoteright}{0027}
% Leave the build time, a random file id and the TeX banner out of the PDF, so the same source always
% gives the same file and a rebuild with no edits leaves nothing to commit.
\pdfinfoomitdate=1
\pdftrailerid{}
\pdfsuppressptexinfo=-1
% Put a real space character between words. Without it the PDF holds none, and a
% parser that does not infer spaces from glyph positions reads "projectmanager".
\pdfinterwordspaceon

\RequirePackage{ragged2e}
\RequirePackage{microtype}

% 10.5pt reads like 11pt Times in a word processor and fits a full page.
\AtBeginDocument{\fontsize{10.5}{12.4}\selectfont}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\raggedbottom
\urlstyle{same}

% No hyphenation: an ATS reads "engi-" and "neering" as two words. Ragged right
% keeps the spacing even once words cannot break.
\hyphenpenalty=10000
\exhyphenpenalty=10000
\AtBeginDocument{\RaggedRight}

% =============================================================================
% Header and sections
% =============================================================================

% Name on top, then contact items joined by `\contactsep`; also sets PDF metadata.
\newcommand{\resumeheader}[2]{%
  \hypersetup{pdftitle={#1 Resume}, pdfauthor={#1}}%
  % No `center` environment: it adds a blank line above and below, and the header should cost two lines, or three when the contact details wrap.
  {\centering{\fontsize{18}{20}\selectfont\bfseries #1}\par\vspace{2pt}#2\par}%
  \vspace{1pt}}
% A bar with one word space each side. A wider gap, such as \enspace, makes some
% extractors break the line there.
\newcommand{\contactsep}{\unskip\ |\ \ignorespaces}

% Plain uppercase heading over a rule. Small caps would read better, but
% pdftotext splits them into "P ROFESSIONAL", which an ATS parser can miss.
\renewcommand{\section}[1]{%
  \par\vspace{4pt}%
  {\fontsize{11}{13}\selectfont\bfseries\MakeUppercase{#1}}\par\vspace{-4pt}%
  \rule{\linewidth}{0.5pt}\par\vspace{1pt}}

% =============================================================================
% Entries
% =============================================================================

% Only the date of a job or project line sits at the right margin, where a
% reader looks for it. A field pushed there leaves a wide gap, and an extractor
% that groups text by position reads what follows as a second column. A job date stays
% with its job as long as one line under it runs to the date, which the build
% checks. The Education date does not: even alone it lands under the next
% heading, so Education prints every field left to right with a bar between.

% Education: school and date in bold, then degree and GPA in italic. Leave the
% last argument empty to print no GPA.
\newcommand{\entry}[4]{%
  \par\vspace{2pt}%
  \textbf{#1}\ |\ \textbf{#2}\par
  \textit{#3}\ifx\relax#4\relax\else\ |\ \textit{#4}\fi\par}

% A date at the right margin, or after a bar under the `inlinedates` option.
\newcommand{\resume@date}[1]{\if@inlinedates\ |\ #1\else\hfill #1\fi}

% One role on one line: bold employer and title, location, dates right. The
% title is bold so several roles at one employer can be told apart at a glance.
% Leave the location empty for work with no one place, and its bar goes with it.
% Every role prints its own employer because parsers file one per position and
% none documents carrying it down from a row above.
\newcommand{\job}[4]{%
  \par\vspace{3pt}%
  \textbf{#1}\ |\ \textbf{#2}\ifx\relax#3\relax\else\ |\ #3\fi\resume@date{#4}\par}

% Project line: bold name, italic context such as an award or the tools used, date right.
\newcommand{\project}[3]{%
  \par\vspace{3pt}%
  \textbf{#1}\ifx\relax#2\relax\else\ |\ \textit{#2}\fi\resume@date{#3}\par}

\newenvironment{bullets}
  {\begin{itemize}[leftmargin=1.6em, label=\textbullet, topsep=1pt, itemsep=0pt, parsep=0pt, partopsep=0pt]}
  {\end{itemize}}

% One labelled line in the skills block.
\newcommand{\skillrow}[2]{\par\textbf{#1:} #2\par}

\endinput
