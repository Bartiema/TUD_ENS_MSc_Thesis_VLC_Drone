# Thesis TODO

## Figures still to produce (`\missingfigure` placeholders)
- [x] `fig:old-prototype` — `chapters/chapter_3.tex` (PCB): photo of the original
      Teensy 4.1 prototype board.
- [x] `fig:teensy-setup` — `chapters/chapter_5.tex` (Multi-Beacon): static two-light
      Teensy setup.
- [x] `fig:obstacle-setup` — `chapters/chapter_6.tex` (Obstacle): obstacle setup in
      simulation and the real room.

Chapter 3 figures are now real images (bearing/gradient/fused blimp trajectories and
the two gradient-method comparison plots). `fig:controller-overview` and
`fig:state-machine` are TikZ.

## Notes
- Raw simulation data is in `data/` (trajectories + precomputed map) if further
  analysis is needed.

---

# Background chapter (chapter_1.tex) — DONE

All blank `\cite{}` placeholders filled; chapter builds clean.

### Citations wired
- [x] UWB + WiFi fingerprinting — `zafari2019indoor`
- [x] Visual SLAM — `murartal2017orbslam2`
- [x] VLP — `zhuang2018vlp` (survey) + `kuo2014luxapose` (Luxapose)
- [x] VLC definition — `pathak2015vlc`
- [x] Lambertian — `komine2004vlc`
- [x] Radio array direction finding — `schmidt1986music` (MUSIC)
- [x] Source / extremum seeking — `ariyur2003extremum`, `zhang2006sourceseeking`,
      `cochran2009sourceseeking` (framed: ESC dither -> Harry dither-free single-PD
      -> our all-eight-PD, yaw-invariant)
- [x] Harry's bearing / gradient / simulation environment — `huang2026lta`

### Review-driven content changes applied
- [x] Related Work expanded to a paragraph per family (RF, vision, VLP), descriptive only.
- [x] Lambertian stated with the cos(phi)cos(psi)/d^2 relation (the "middle" level).
- [x] Bearing "reliably" softened to an angular-coverage statement; line-of-sight /
      direct-path limitation noted (reflections need stronger sensors).
- [x] Gradient clarified: spatial gradient comes from the MAP (samples across positions),
      eight PDs give the yaw-invariant per-location value; forward-references Ch 3.
- [x] Obstacle-as-shadow mechanism stated in the gap paragraph.

### Still to confirm
- [ ] First names in `zhang2006sourceseeking` — `Daniel {Arnold}` and
      `Antranik {Siranosian}` — check against the PDF.
- [ ] Related-Work / theory-section overlap (Marco flagged overlap risk).
- [ ] Optional reference swaps: VLC `pathak2015vlc` vs the IEEE 802.15.7 standard;
      VLP `kuo2014luxapose` (Luxapose) vs Epsilon (Li et al., NSDI 2014).

---

# Citation audit (DEFERRED — remaining chapters)

Applies to `introduction.tex`, `chapter_3.tex` (PCB), `chapter_4.tex` (Real-World Impl)
and `chapter_6.tex` (Obstacle), which are not yet fleshed. Apply when each is in scope.
All proposed bib entries are already in `bib/MyMScTUDESThesisBibFile.bib`; verify exact
volume / number / pages before final submission.

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
| chapter_3.tex:21 | CrazyFlie "13 g / 44 mm" hard limits | `crazyflie21` |

### Medium priority
| Location | Claim | Suggested |
|---|---|---|
| introduction.tex:8 | light-based nav needs less infrastructure | `zhuang2018vlp` |
| chapter_4.tex:8 | anti-aliasing / Nyquist limit | `oppenheim1999dsp` (or Shannon 1949) |
| chapter_4.tex:10 | "Hamming window" | `harris1978windows` |
| chapter_3.tex:27 | photodiode transimpedance amplifier | `graeme1996photodiode` |
| chapter_3.tex:37 | ground plane reduces motor EMI | `ott2009emc` |

> Note: chapter_4.tex:8 also has a prose-style issue (parentheses), separate from citations.

## 3. Bib entries (all now in the bib)
Keys available in `bib/MyMScTUDESThesisBibFile.bib`: `zafari2019indoor`,
`murartal2017orbslam2`, `kuo2014luxapose`, `komine2004vlc`, `schmidt1986music`,
`floreano2015drones`, `zhuang2018vlp`, `pathak2015vlc`, `crazyflie21`, `harris1978windows`,
`graeme1996photodiode`, `ott2009emc`, `ariyur2003extremum`, `zhang2006sourceseeking`,
`cochran2009sourceseeking`. Plus `oppenheim1999dsp` and `mardia2000directional` (added
earlier for chapter 2).
