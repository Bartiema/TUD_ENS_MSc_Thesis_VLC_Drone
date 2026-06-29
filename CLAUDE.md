# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

```bash
make              # compile thesis.pdf (pdflatex + bibtex if needed, 4 passes)
make clean        # remove build artifacts from build/
make spell        # spell-check all .tex files with aspell (British English)
make view         # compile and open thesis.pdf in Evince
```

**NixOS environment** (provides full TeXLive + gnumake + ghostscript):
```bash
nix develop       # enter dev shell, then run make
```

## Structure

- `thesis.tex` — main entry point; defines all metadata (`\reportTitle`, `\reportAuthor`, `\reportDate`, `\reportAbstract`, `\reportKeywords`, graduation committee, etc.)
- `chapters/` — chapter files (`introduction.tex`, `chapter_1.tex`, `conclusions.tex`, `futurework.tex`, `preface.tex`, `quotation.tex`, `appendix_a.tex`)
- `template/` — TU Delft ES template files (`frontcover.tex`, `titlepage.tex`, `graduationdata.tex`)
- `template-pics/` — TU Delft logo and border images (including tikz source for logo)
- `bib/MyMScTUDESThesisBibFile.bib` — bibliography file
- `build/` — intermediate files (`.aux`, `.log`, `.toc`, `.bbl`); final `thesis.pdf` is moved to root

## Key Conventions

- Build output goes to `build/`; `TEXINPUTS` includes `.`, `./template`, `template-pics/tud-ens-logo-tikz`, and `./chapters` — so `\include{introduction}` resolves to `chapters/introduction.tex`.
- The bib path in `thesis.tex` uses `../bib/MyMScTUDESThesisBibFile` (with `../`) for local compilation via make. If compiling directly in Overleaf or another local LaTeX distribution, remove the `../` prefix.
- New chapters are added via `\input{chapters/chapter_X}` in `thesis.tex`.
- Bibliography style is fixed as `plain` — do not change it.
