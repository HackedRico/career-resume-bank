# Examples

Two made-up people, to show what the repo looks like in use. Every employer, number, link and contact detail here is invented.

| Folder | Person | Shows |
| --- | --- | --- |
| `data-engineer/` | Jordan Example | Projects with public links, a Listed skill, an `## Avoid` rule |
| `nurse/` | Morgan Sample | A license and certifications, a section named Volunteer Work, Education last, no GPA |

Each folder holds:

- `bank/`: a filled experience bank, with its focus tags listed in `bank/README.md`.
- `base/`: the general-purpose resume built from it.
- `jobs/<date>-<company>-<role>/`: one application, with the post, the keyword list and the tailored resume.

Build one with `python3 scripts/build.py examples/nurse/base`. Delete the folder whenever you like; no script depends on it.
