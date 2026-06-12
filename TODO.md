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

Builds clean; all `\cite{}` placeholders filled. Committed and pushed (squashed as
"Add Background & Related Work chapter (Chapter 2)"). Sections: Related Work, Drone
Platform, Visible Light Communication & Sensing, Light Signals, Bearing Angle
Estimation, Gradient-Based Source Seeking, Simulation Environment.

### Citations wired
- [x] UWB + WiFi fingerprinting — `zafari2019indoor`
- [x] Visual SLAM — `murartal2017orbslam2`
- [x] VLP — `zhuang2018vlp` (survey) + `kuo2014luxapose` (Luxapose)
- [x] VLC definition — `pathak2015vlc`
- [x] Lambertian — `komine2004vlc`
- [x] Square-wave harmonics / FFT — `oppenheim1999dsp`
- [x] Amplitude-comparison direction finding — `iqbal2020amplitude`
      (replaced the MUSIC analogy; `schmidt1986music` is now unused but kept in the bib)
- [x] Source / extremum seeking — `ariyur2003extremum`, `zhang2006sourceseeking`,
      `cochran2009sourceseeking` (ESC dither -> Harry's dither-free single-PD)
- [x] CrazyFlie 2.1 platform — `crazyflie21`
- [x] Harry's bearing / gradient / simulator and its validation — `huang2026lta`

### Content and structure (applied)
- [x] New "Drone Platform" section: CrazyFlie 2.1, low-level flight controller and
      setpoints, onboard position estimate and drift, body-vs-world frames.
- [x] New "Light Signals" section: defines the per-sensor signal m_n; real-world FFT
      pipeline vs the simulation's idealised Webots irradiance, cross-referenced with
      the Simulation Environment section both ways.
- [x] Bearing: weighted-vector-sum formula added (matches the firmware).
- [x] Lambertian stated as cos^m(alpha) cos(beta) / d^2 (m order noted; angles
      renamed to alpha/beta to avoid the psi clash with the bearing).
- [x] Related Work: fuller (RF, vision, VLP), enumerated contribution, WiFi/UWB split.
- [x] Gradient/source-seeking kept to background only; contributions live in Ch 3.
- [x] Simulation: fidelity grounded in Harry's flight-dynamics validation (CFD and
      real flights); light model idealised; blimp-vs-CrazyFlie distinction explicit.
- [x] Ch 3 cross-references pointed at Section `sec:lightsignal` (m_n) and `sec:bearing`.

### Still to confirm
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
