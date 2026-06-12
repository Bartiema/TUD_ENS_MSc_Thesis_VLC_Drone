# Thesis TODO

## Data still to measure
- [ ] `tab:filter-snr` — `chapters/chapter_4.tex` (Real-World): per-channel SNR
      (all 8 photodiodes) at the beacon modulation frequency, for the 4 filter
      configurations (no filtering / hardware only / software only / hardware +
      software) × {stationary, in flight} = 8 rows. All 64 cells are `--`
      placeholders pending bench + in-flight measurement.

## Notes
- Raw simulation data is in `data/` (trajectories + precomputed map) if further
  analysis is needed.
- **Unplaced observation (from ambient-light work):** a higher SNR sustained
  throughout a flight extends the drone's usable sensing range, letting it pick out
  the beacon direction from further away. NOT shown by the ambient-light figures
  (same take-off/setup both flights), so it was kept out of `chp:realworld` §Effect
  of Ambient Lighting. Decide its home later (Conclusions or Future Work) once those
  chapters are fleshed.

---

# Open cross-chapter items

- [ ] The bench 1600 Hz sample rate was dropped from `chp:hardware`; still to be introduced
      in a later chapter where the bench setup is actually used (not yet placed).
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
