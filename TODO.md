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

## Citations / blank cites to fill (Background, `chapters/chapter_1.tex`)
- [ ] Simulation environment reference (Simulation Environment section).
- [ ] Multiple-overlapping-lights / light-positioning claim (VLC & Sensing).
- [ ] Array-based direction estimation for radio, Bluetooth/WiFi/GPS (Bearing Angle).
- [ ] Related Work citations: general GPS-denied methods (UWB/WiFi/SLAM), light
      positioning, and the prior work by Harry Huang.

## Notes
- `figures/gradient_analysis/gradient_method_comparison.png` is ~5 MB, which makes
  the PDF large; downsample it before the final version.
- Raw simulation data is in `data/` (trajectories + precomputed map) if further
  analysis is needed.
