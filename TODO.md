# Thesis TODO

## Figures still to produce (`\missingfigure` placeholders)
- [ ] `fig:old-prototype` — `chapters/chapter_3.tex` (PCB): photo of the original
      three-part Teensy 4.1 prototype. No photo exists on the `figures` branch yet.

## Notes
- Raw simulation data is in `data/` (trajectories + precomputed map) if further
  analysis is needed.

---

# Chapter 4 / `chapter_3.tex` (PCB Hardware Design) — open items

- [ ] **500 Hz sample rate vs 500 Hz filter (Nyquist).** Bart says the numbers are right
      and will explain why it works; the explanation belongs in `chp:realworld`. The
      500/1600 Hz sentence stays in this chapter as a bare spec for now. Still decide
      whether the bench 1600 Hz figure earns its place here (reviewers called it orphaned).

### Inbound cross-references other (skeleton) chapters should add when fleshed
- [ ] `chapter_4.tex` (Real-World, `chp:realworld`): when describing "the PCB", reference
      `\ref{chp:hardware}`. The populated 500 Hz low-pass and its cut-off live there (this
      chapter only describes the optional filter provision), so present it as populating
      the pads this chapter provides.
- [ ] `chapter_2.tex` (Algorithm) System Overview and `chapter_6.tex` (Obstacle): point to
      `\ref{chp:hardware}` where they mention the photodiode board.
- [ ] `chapter_5.tex` (Multi-Beacon): its "Teensy-based sensing platform" should back-ref
      `\ref{chp:hardware}` and be distinguished from the retired Teensy 4.1 prototype.

---

# Background chapter (chapter_1.tex) — still to confirm
- [ ] Related-Work / theory-section overlap (Marco flagged overlap risk).
- [ ] Optional reference swaps: VLC `pathak2015vlc` vs the IEEE 802.15.7 standard;
      VLP `kuo2014luxapose` (Luxapose) vs Epsilon (Li et al., NSDI 2014).

---

# Citation audit (DEFERRED — remaining chapters)

Applies to `introduction.tex`, `chapter_4.tex` (Real-World Impl) and `chapter_6.tex`
(Obstacle), which are not yet fleshed. Apply when each is in scope. All proposed bib
entries are already in `bib/MyMScTUDESThesisBibFile.bib`; verify exact volume / number /
pages before final submission.

## 1. Empty `\cite{}` placeholders to fill
| Location | Claim (short) | Proposed key |
|---|---|---|
| introduction.tex:12 | "Recent work by Harry Huang demonstrated..." | `huang2026lta` |
| chapter_6.tex:46 | methods "demonstrated on a lighter-than-air blimp" | `huang2026lta` |

## 2. Additional uncited claims (no `\cite` at all)

### High priority (examiner-bait)
| Location | Claim | Suggested |
|---|---|---|
| introduction.tex:6 | UAV applications + "GPS not accurate enough" indoors | `floreano2015drones` + `zafari2019indoor` |

### Medium priority
| Location | Claim | Suggested |
|---|---|---|
| introduction.tex:8 | light-based nav needs less infrastructure | `zhuang2018vlp` |
| chapter_4.tex:8 | anti-aliasing / Nyquist limit | `oppenheim1999dsp` (or Shannon 1949) |
| chapter_4.tex:10 | "Hamming window" | `harris1978windows` |

> Note: chapter_4.tex:8 also has a prose-style issue (parentheses), separate from citations.
