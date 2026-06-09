# Thesis TODO

## To confirm
- [ ] **Gradient-ascent failure simulation** (`fig:gradient-fail`, `chapters/chapter_2.tex`,
      "Why Existing Methods Fall Short"): confirm the described failure mode actually
      matches the simulation. The text currently says single-photodiode gradient ascent
      follows a *slow, wandering path and stalls where the field is shallow or noisy*.
      Correct the text if the real failure mode differs.

## Figures to produce (currently `\missingfigure` placeholders)
- [ ] `fig:bearing-fail` — `chapters/chapter_2.tex`: simulation of the bearing-only
      controller failing at an obstacle.
- [ ] `fig:gradient-fail` — `chapters/chapter_2.tex`: simulation of single-photodiode
      gradient ascent on a slow/wandering path (see "To confirm" above).
- [ ] `fig:fft-beacons` — `chapters/chapter_2.tex` (Multi-Beacon Traversal): FFT of a
      photodiode signal with two beacons, a separate peak per modulation frequency.
- [ ] `fig:gradient-comparison` — `chapters/chapter_2.tex` (Gradient Estimation):
      directional error of the five gradient methods on the dense vs sparse map.
- [ ] `fig:old-prototype` — `chapters/chapter_3.tex` (PCB): photo of the original
      Teensy 4.1 prototype board.
- [ ] `fig:teensy-setup` — `chapters/chapter_5.tex` (Multi-Beacon): static two-light
      Teensy setup.
- [ ] `fig:obstacle-setup` — `chapters/chapter_6.tex` (Obstacle): obstacle setup in
      simulation and the real room.

(`fig:controller-overview` and `fig:state-machine` are drawn as TikZ, not placeholders.)

## Citations / blank cites to fill
Still blank in the Background chapter (`chapters/chapter_1.tex`):
- [ ] Simulation environment reference (Simulation Environment section).
- [ ] Multiple-overlapping-lights / light-positioning claim (VLC & Sensing).
- [ ] Array-based direction estimation for radio, Bluetooth/WiFi/GPS (Bearing Angle).
- [ ] Related Work citations: general GPS-denied methods (UWB/WiFi/SLAM), light
      positioning, and the prior work by Harry Huang.

(Chapter 3 citations — Harry's arXiv paper `huang2026lta` and the five gradient
methods — are filled.)
