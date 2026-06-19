# Thesis TODO

## Notes
- Raw simulation data is in `data/` (trajectories + precomputed map) if further
  analysis is needed.

---

# Open items — confirm with Harry (blimp)

- [ ] **Blimp SNR numbers:** Harry's paper (`2026_Sensys_HarryHuang.pdf`) has NO
      direct CrazyFlie-vs-blimp SNR comparison; its only SNR figure is an arrival
      threshold of 50 (target reached within ~20 cm). The higher-SNR claim is kept
      qualitative for now. ASK HARRY for exact comparative numbers before final.

---

# Background chapter (chapter_1.tex) — still to confirm

- [ ] Related-Work / theory-section overlap (Marco flagged overlap risk).
- [ ] Optional reference swaps: VLC `pathak2015vlc` vs the IEEE 802.15.7 standard;
      VLP `kuo2014luxapose` (Luxapose) vs Epsilon (Li et al., NSDI 2014).


# Blimp generalisation figure (Ch. 7 §Generalisation to a Blimp Platform)

- [ ] ON HOLD: a blimp multi-target traverse figure (flight-path map + state/SNR)
      from `data/harry_blimp_data/navigate_session_perfect_multi_targets_last_one.csv`
      was drafted and trimmed to the first two waypoints, but the traverse still
      looked off (WP2 completes instantly with no usable map; ~22 s of SNR=0 dead
      time), so we are NOT using it for now. Bart to check with Harry and/or source
      a cleaner blimp run before deciding whether to add it to `chapter_6.tex`
      §Generalisation. NOTE: this session's max SNR (~33) does NOT exceed the
      CrazyFlie (~39), so it does not support the higher-SNR claim either.
