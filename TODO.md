# Thesis TODO

## Figures still to produce (`\missingfigure` placeholders)
- [ ] `fig:old-prototype` — `chapters/chapter_3.tex` (PCB): photo of the original
      Teensy 4.1 prototype board.
- [ ] `fig:teensy-setup` — `chapters/chapter_5.tex` (Multi-Beacon): static two-light
      Teensy setup.
- [ ] `fig:obstacle-setup` — `chapters/chapter_6.tex` (Obstacle): obstacle setup in
      simulation and the real room.

Chapter 3 figures are now real images (bearing/gradient/fused blimp trajectories and
the two gradient-method comparison plots). `fig:controller-overview` and
`fig:state-machine` are TikZ.

## Notes
- `figures/gradient_analysis/gradient_method_comparison.png` is ~5 MB, which makes
  the PDF large; downsample it before the final version. Layout is being switched
  from a 1x5 column to a 2x3 grid (landscape) in `gradient_fitting_analyzer.py`; once
  regenerated, set the LaTeX figure back to width-based sizing with normal placement.
- Raw simulation data is in `data/` (trajectories + precomputed map) if further
  analysis is needed.

---

# Citation audit & suggestions (DEFERRED — do not apply yet)

Citation fixes/additions for chapters **other than chapter_2** (Algorithm Design),
which we are not actively working on. Apply them when those chapters are in scope.
Chapter 2's own citation work is already done (see "Already applied" at the end).

All specific papers below are real, well-known works, but **verify exact volume /
number / pages before final submission.** Swap any reference for one you prefer.

## 1. Empty `\cite{}` placeholders to fill

| Location | Claim (short) | Proposed key | New bib entry? |
|---|---|---|---|
| introduction.tex:12 | "Recent work by Harry Huang demonstrated..." | `huang2026lta` | existing |
| chapter_1.tex:6 | GPS-denied nav: UWB + WiFi fingerprinting + visual SLAM | `zafari2019indoor` **+** `murartal2017orbslam2` (split) | new |
| chapter_1.tex:8 | VLP cm-level accuracy with many light anchors | `kuo2014luxapose` | new |
| chapter_1.tex:10 | single light source: bearing / single-photodiode gradient | `huang2026lta` | existing |
| chapter_1.tex:12 | "prior work by Harry Huang" | `huang2026lta` | existing |
| chapter_1.tex:18 | Lambertian intensity falloff model | `komine2004vlc` | new |
| chapter_1.tex:24 | bearing-angle algorithm from a photodiode ring | `huang2026lta` | existing |
| chapter_1.tex:26 | array-based direction estimation for radio (BT/WiFi/GPS) | `schmidt1986music` | new |
| chapter_1.tex:34 | "Prior work followed this gradient using a single photodiode" | `huang2026lta` | existing |
| chapter_1.tex:40 | "simulation environment ... developed in prior work" | `huang2026lta` ⚠️ verify | existing |
| chapter_6.tex:46 | methods "demonstrated on a lighter-than-air blimp" | `huang2026lta` | existing |

## 2. Additional uncited claims (no `\cite` at all) — from the audit

### High priority (examiner-bait)
| Location | Claim | Suggested |
|---|---|---|
| introduction.tex:6 | UAV applications + "GPS not accurate enough" indoors | `floreano2015drones` + `zafari2019indoor` |
| chapter_1.tex:16 | VLC definition (Background chapter, no cite) | `pathak2015vlc` (or IEEE 802.15.7 standard) |
| chapter_3.tex:21 | CrazyFlie "13 g / 44 mm" hard limits | `crazyflie21` (Bitcraze datasheet) |

### Medium priority
| Location | Claim | Suggested |
|---|---|---|
| introduction.tex:8 | light-based nav needs less infrastructure | `zhuang2018vlp` |
| chapter_4.tex:8 | anti-aliasing / Nyquist limit | `oppenheim1999dsp` (or Shannon 1949) |
| chapter_4.tex:10 | "Hamming window" | `harris1978windows` |
| chapter_3.tex:27 | photodiode transimpedance amplifier | `graeme1996photodiode` (or a TI TIA app note) |
| chapter_3.tex:37 | ground plane reduces motor EMI | `ott2009emc` |

> Note: chapter_4.tex:8 also has a prose-style issue (parentheses), separate from citations.

### Low priority — already applied in chapter 2 (see section 5)

## 3. Proposed NEW bib entries (verify fields before use)

```bibtex
@article{zafari2019indoor,
	title = "A Survey of Indoor Localization Systems and Technologies",
	author = "Faheem {Zafari} and Athanasios {Gkelias} and Kin K. {Leung}",
	journal = "IEEE Communications Surveys \& Tutorials",
	volume = "21", number = "3", pages = "2568--2599", year = "2019"
}

@article{murartal2017orbslam2,
	title = "{ORB-SLAM2}: An Open-Source {SLAM} System for Monocular, Stereo, and {RGB-D} Cameras",
	author = "Ra{\'u}l {Mur-Artal} and Juan D. {Tard{\'o}s}",
	journal = "IEEE Transactions on Robotics",
	volume = "33", number = "5", pages = "1255--1262", year = "2017"
}

@inproceedings{kuo2014luxapose,
	title = "Luxapose: Indoor Positioning with Mobile Phones and Visible Light",
	author = "Ye-Sheng {Kuo} and Pat {Pannuto} and Ko-Jen {Hsiao} and Prabal {Dutta}",
	booktitle = "Proc. 20th Annual Int. Conf. on Mobile Computing and Networking (MobiCom)",
	pages = "447--458", year = "2014"
}

@article{komine2004vlc,
	title = "Fundamental Analysis for Visible-Light Communication System using {LED} Lights",
	author = "Toshihiko {Komine} and Masao {Nakagawa}",
	journal = "IEEE Transactions on Consumer Electronics",
	volume = "50", number = "1", pages = "100--107", year = "2004"
}

@article{schmidt1986music,
	title = "Multiple Emitter Location and Signal Parameter Estimation",
	author = "Ralph O. {Schmidt}",
	journal = "IEEE Transactions on Antennas and Propagation",
	volume = "34", number = "3", pages = "276--280", year = "1986"
}

@article{floreano2015drones,
	title = "Science, Technology and the Future of Small Autonomous Drones",
	author = "Dario {Floreano} and Robert J. {Wood}",
	journal = "Nature",
	volume = "521", number = "7553", pages = "460--466", year = "2015"
}

@article{zhuang2018vlp,
	title = "A Survey of Positioning Systems Using Visible {LED} Lights",
	author = "Yuan {Zhuang} and others",
	journal = "IEEE Communications Surveys \& Tutorials",
	volume = "20", number = "3", pages = "1963--1988", year = "2018",
	note = "VERIFY full author list"
}

@article{pathak2015vlc,
	title = "Visible Light Communication, Networking, and Sensing: A Survey, Potential and Challenges",
	author = "Parth H. {Pathak} and Xiaotao {Feng} and Pengfei {Hu} and Prasant {Mohapatra}",
	journal = "IEEE Communications Surveys \& Tutorials",
	volume = "17", number = "4", pages = "2047--2077", year = "2015"
}

@misc{crazyflie21,
	title = "{Crazyflie 2.1}",
	author = "{Bitcraze AB}",
	year = "2021",
	howpublished = "\url{https://www.bitcraze.io/products/crazyflie-2-1/}",
	note = "Product documentation, last accessed 2026"
}

@article{harris1978windows,
	title = "On the Use of Windows for Harmonic Analysis with the Discrete {Fourier} Transform",
	author = "Fredric J. {Harris}",
	journal = "Proceedings of the IEEE",
	volume = "66", number = "1", pages = "51--83", year = "1978"
}

@book{graeme1996photodiode,
	title = "Photodiode Amplifiers: Op Amp Solutions",
	author = "Jerald G. {Graeme}",
	year = "1996", publisher = "McGraw-Hill", address = "New York, NY, USA"
}

@book{ott2009emc,
	title = "Electromagnetic Compatibility Engineering",
	author = "Henry W. {Ott}",
	year = "2009", publisher = "Wiley", address = "Hoboken, NJ, USA"
}
```

> `oppenheim1999dsp` and `mardia2000directional` are already in the bib (added for
> chapter 2), so the deferred chapter_4.tex:8 (Nyquist) cite can reuse
> `oppenheim1999dsp` without a new entry.

## 4. Judgment calls to confirm before applying

- **chapter_1.tex:40** — is the Webots sim environment from `huang2026lta`, or a separate
  source (e.g. the supervisor's)? Confirm the right key.
- **chapter_1.tex:6** — OK to split into a survey (`zafari2019indoor`) + ORB-SLAM2
  (`murartal2017orbslam2`)? A single cite for three techniques looks thin.
- **chapter_1.tex:16** — `pathak2015vlc` survey vs. the IEEE 802.15.7 standard for the
  VLC definition.
- VLP example: `kuo2014luxapose` (Luxapose) vs. Epsilon (Li et al., NSDI 2014).

## 5. Already applied (chapter 2 — in scope)

- **LOESS fix:** `\cite{cleveland1979loess}` → `\cite{bjorck1996lsq}`, because the
  "Polynomial Surface" method is an unweighted OLS quadratic fit, not LOESS.
- **chapter_2.tex:90** square-wave odd harmonics → `\cite{oppenheim1999dsp}` (entry in bib).
- **chapter_2.tex:194** weighted circular mean → `\cite{mardia2000directional}` (entry in bib).
