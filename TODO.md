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
- [ ] **Blimp control change:** confirm with Harry whether running on the blimp needed
      only re-tuned PID gains or a different low-level controller / mixer for the motor
      layout. Text currently says "adapting only the low-level control to its motor
      layout" (deliberately loose). Tighten once confirmed.
- [ ] **Blimp narrative (confirm with Harry):** chapter states Harry's bearing/gradient
      methods were sim-only, and the REAL blimp flights use OUR PCB + fused controller
      (per Bart), showing multi-target, obstacle avoidance, and higher SNR. Verify this
      framing matches what Harry's paper claims/authorship before final.

---

# Background chapter (chapter_1.tex) — still to confirm

- [ ] Related-Work / theory-section overlap (Marco flagged overlap risk).
- [ ] Optional reference swaps: VLC `pathak2015vlc` vs the IEEE 802.15.7 standard;
      VLP `kuo2014luxapose` (Luxapose) vs Epsilon (Li et al., NSDI 2014).
