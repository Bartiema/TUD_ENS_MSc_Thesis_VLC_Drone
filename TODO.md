# Thesis TODO

## Notes
- Raw simulation data is in `data/` (trajectories + precomputed map) if further
  analysis is needed.
- **Unplaced observation (from ambient-light work):** a higher SNR sustained
  throughout a flight extends the drone's usable sensing range, letting it pick out
  the beacon direction from further away. NOT shown by the ambient-light figures
  (same take-off/setup both flights), so it was kept out of `chp:realworld` §Effect
  of Ambient Lighting. Decide its home later (Conclusions or Future Work) once those
  chapters are fleshed. NOTE: now also surfaced in `chp:obstacle` §Generalisation to
  a Blimp Platform (blimp's higher SNR -> longer range), with a forward ref to
  `chp:futurework`.
- [ ] **Future Work:** add a paragraph on the blimp's much higher SNR and its
      probable cause (buoyancy means motors run only when moving and at lower power
      -> less vibration/EMI than the always-spinning CrazyFlie; the PCB itself is
      unchanged and in the same place). `chp:obstacle` §Blimp now forward-refs
      `chp:futurework` for it. Keep causes hypotheses, not asserted facts.
- [ ] **Blimp SNR numbers:** Harry's paper (`2026_Sensys_HarryHuang.pdf`) has NO
      direct CrazyFlie-vs-blimp SNR comparison; its only SNR figure is an arrival
      threshold of 50 (target reached within ~20 cm). The higher-SNR claim is kept
      qualitative for now. ASK HARRY for exact comparative numbers before final.
- [ ] **Blimp control change:** confirm with Harry whether running on the blimp needed
      only re-tuned PID gains or a different low-level controller / mixer for the motor
      layout. Text currently says "with only the low-level control adapted to its motor
      layout" (deliberately loose). Tighten once confirmed.
- [ ] **Blimp narrative (confirm with Harry):** chapter now states Harry's bearing/gradient
      methods were sim-only, and the REAL blimp flights use OUR PCB + fused controller
      (per Bart), showing multi-target, obstacle avoidance, and higher SNR. Verify this
      framing matches what Harry's paper claims/authorship before final.
- [x] Geometry of the real-flight setup is now stated as indicative, not a hard
      measured truth (done in `chp:obstacle` §Setup caption + §SNR Field Mapping
      odometry-drift paragraph).

---

# Multi-Beacon chapter (chapter_5.tex) — possible addition
- [ ] We have lawnmower SNR-field survey data for the multi-beacon (no-obstacle)
      case too (`figures/real_data_gather_flights/{150,170}hz_lawnmower_no_obstacle.png`,
      `data/real_data_gather_flights/data_gather_{150,170}hz_..._0.20ms.csv`). Consider
      adding a real-room SNR field map to the Multi-Beacon chapter to mirror the
      field-mapping section being added to the Obstacle chapter (`chp:obstacle`).

---

# Open cross-chapter items

- [ ] `chapter_2.tex` (Algorithm) System Overview and `chapter_6.tex` (Obstacle): point to
      `\ref{chp:hardware}` where they mention the photodiode board.

- [ ] **Chapter/section openings (ALL chapters):** several chapters, and some sections,
      jump straight from the `\chapter`/`\section` title into the next (sub-)section title
      with no lead-in. Proper style is to first introduce the chapter/section, saying what
      it will contain, before the first sub-heading. Audit every chapter and add a short
      orienting paragraph after each title that is immediately followed by a lower-level
      heading. (Cross-chapter cleanup; can be done later or in a separate session.)

---

# Background chapter (chapter_1.tex) — still to confirm
- [ ] Related-Work / theory-section overlap (Marco flagged overlap risk).
- [ ] Optional reference swaps: VLC `pathak2015vlc` vs the IEEE 802.15.7 standard;
      VLP `kuo2014luxapose` (Luxapose) vs Epsilon (Li et al., NSDI 2014).

---

# Citation audit (DEFERRED — remaining chapters)

Applies to `introduction.tex` and `chapter_6.tex` (Obstacle), which are not yet fleshed.
Apply when each is in scope. All proposed bib entries are already in
`bib/MyMScTUDESThesisBibFile.bib`; verify exact volume / number / pages before final
submission. (The `chapter_4.tex` Real-World citations are all done.)

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
