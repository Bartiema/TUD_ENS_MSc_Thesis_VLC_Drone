# Thesis TODO

## Figures still to produce (`\missingfigure` placeholders)
- [ ] `fig:old-prototype` — `chapters/chapter_3.tex` (PCB): photo of the original
      Teensy 4.1 prototype board. No photo exists on the `figures` branch yet.
- [x] `fig:teensy-setup` — `chapters/chapter_5.tex` (Multi-Beacon): static two-light
      Teensy setup.
- [x] `fig:obstacle-setup` — `chapters/chapter_6.tex` (Obstacle): obstacle setup in
      simulation and the real room.

Chapter 3 figures are now real images (bearing/gradient/fused blimp trajectories and
the two gradient-method comparison plots). `fig:controller-overview` and
`fig:state-machine` are TikZ. The PCB chapter uses `fig:new-board`
(`figures/new_pcb_picture.jpeg`).

## Notes
- Raw simulation data is in `data/` (trajectories + precomputed map) if further
  analysis is needed.

---

# Chapter 4 / `chapter_3.tex` (PCB Hardware Design) — open questions for Bart

Parked while fleshing the PCB chapter (branch `flesh-hardware`). The prose was grounded
in the KiCad sources: new board `crazyflie2-exp-photodiodes/ecad/photodiode-expansion`
(OPA4350 TIAs, ADS7953 ADC, REF5025A reference, TPS73133 LDO, VEMD4200 photodiodes);
old platform `harry_pcb` (Teensy main board) + `harry_pcb_opt101` (OPT101 sensor board).
Confirm or correct the following:

- [ ] **Teensy 4.0 vs 4.1.** The chapter says Teensy~4.1 (kept from the skeleton), but the
      `harry_pcb` schematic lists a Teensy~4.0. Which did the prototype actually use?
- [ ] **`fig:old-prototype` photo.** No photo of the original Teensy+OPT101 prototype exists
      on the `figures` branch, so it is still a `\missingfigure`. A photo is needed.
- [ ] **Original-prototype description.** Confirm: two boards combined (Teensy main board +
      OPT101 sensor board), OPT101 = integrated photodiode + transimpedance amplifier, and
      "space for sixteen photodiodes". Adjust if any detail is off.
- [ ] **Part numbers named in prose.** I name the OPA4350 (op-amp) and ADS7953 (ADC), and now
      also the REF5025A reference and TPS73133 LDO, in Circuit Design. Keep all four, or
      trim? Also: should the photodiode part (VEMD4200) be named?
- [ ] **CrazyFlie limits.** Verify the "13 g mass / 44 mm diagonal" numbers against the
      Bitcraze datasheet before final (cited `crazyflie21`).
- [ ] **Measured mass of the new board.** The chapter states the limit, not the achieved
      mass. If the final board's measured weight is known, adding it would strengthen the
      "meets the limit" claim.
- [ ] **Optional new-board schematic figure.** A generated schematic PDF exists at
      `crazyflie2-exp-photodiodes/generated/photodiode-expansion.pdf`. Worth adding a
      schematic or block-diagram figure of the new board, or is the photo enough?

### Raised by the examiner-style review (need a measurement or your decision; not invented)
- [ ] **Close the requirements loop.** The chapter states the 13 g / 44 mm limit but never
      reports whether the finished board meets it. Add the measured assembled mass and
      actual diagonal, and ideally a rough power budget (LDO + ADC + 3x quad op-amps). These
      are measurements, so they need real numbers from you, not estimates.
- [ ] **Deeper part justifications + passive values.** The chapter names the parts and gives a
      functional reason for each, but not a design-driven "why this exact part" (ADC
      resolution adequacy, reference temperature drift, LDO noise). The TIA feedback values
      (3.2 k / 2.5 nF, setting gain and bandwidth) are deliberately left out per the "no
      minutiae" rule; decide if they belong here or in the appendix.
- [ ] **Validation criterion.** "Correct voltage readings on all eight channels" is asserted
      without a criterion (correct against what: dark/full-scale levels, inter-channel
      uniformity within X%, linearity?). Tighten with what was actually checked, ideally a
      measurement or small plot.
- [ ] **ADC sample rate / throughput.** Worth one sentence: at what rate are the eight
      channels sampled, and is it comfortably above the Nyquist limit for the beacon
      modulation frequencies of Chapter~\ref{chp:algorithm}?
- [ ] **SPI / connector mapping.** The two headers and the SPI interface to the CrazyFlie
      are mentioned but not mapped to specific deck pins; add if you want full hardware
      detail.

### Inbound cross-references other (skeleton) chapters should add when fleshed
- [ ] `chapter_4.tex` (Real-World, `chp:realworld`): when describing "the PCB", reference
      `\ref{chp:hardware}`; and the 500 Hz low-pass it mentions is the filter pad this
      chapter now forward-refers to, so keep them consistent.
- [ ] `chapter_2.tex` (Algorithm) System Overview and `chapter_6.tex` (Obstacle): point to
      `\ref{chp:hardware}` where they mention the photodiode board.

### Review processing already applied to chapter_3.tex (this pass)
- Style: passive openings -> "we"; named the Graeme and Ott citations; added paragraph
  closings; LDO reasoning.
- Coherency: fixed the filter contradiction (low-pass IS populated; forward-ref to
  `chp:realworld`); stopped conflating the prototype with the thesis's all-eight gradient
  novelty; added a `chp:background` back-ref, a `chp:realworld` hand-off sentence, and a
  link to the thesis-level size/power constraints; clarified the bench Teensy.
- Academic: softened the "compared throughout" over-promise; removed the vague "a few
  grams"; named REF5025A and TPS73133; tied the ADC to the eight-channel requirement.

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

Applies to `introduction.tex`, `chapter_4.tex` (Real-World Impl) and `chapter_6.tex`
(Obstacle), which are not yet fleshed. Apply when each is in scope. `chapter_3.tex` (PCB)
is now fleshed and its citations are applied (see below). All proposed bib entries are
already in `bib/MyMScTUDESThesisBibFile.bib`; verify exact volume / number / pages before
final submission.

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

## 3. Applied to `chapter_3.tex` (PCB) while fleshing on `flesh-hardware`
- [x] CrazyFlie "13 g / 44 mm" hard limits — `crazyflie21`
- [x] photodiode transimpedance amplifier — `graeme1996photodiode`
- [x] ground plane reduces motor EMI — `ott2009emc`
