# Thesis TODO

# Open items

## Cross-chapter sweeps surfaced while revising Ch2 (for their own branches)
- [ ] **Notation in Ch5 (`chapter_4.tex`):** the per-sensor signal is written `m_n` / `\hat{m}_n`
      / `\alpha_m` there, while Ch2/Ch3 use `S_n`. Reconcile to `S_n` on the Ch5 branch
      (note `\alpha_m` is the magnitude-smoothing factor, a distinct symbol — check each use). (2026-06-23)
- [ ] **Work in Ch9 (`future_work.tex`):** Confidence-weighted fusion: let the bearing/gradient weights $w_B$, $w_G$ scale
  with a per-input confidence, instead of the current fixed, equal-weight gated
  hand-off (moved out of Ch3 §Control Output, 2026-06-21).

## Spotted in Ch3 (`chapter_2.tex`) while revising Ch5 (2026-06-23)
Minor issues noticed but NOT changed, since Ch3 is already at standard. Added
`\label{sec:multibeacon-separation}` to §Multi-Beacon Traversal so Ch5 can
reference it (the only edit made to Ch3). To consider on a Ch3 touch-up:
- [ ] Typo §Multi-Beacon Traversal: "the photodiode array can sense them all of
      them at once" (line ~229) — drop the duplicated "all of them".
- [ ] Past tense in the same section: "We took this into account when choosing the
      modulation frequencies for our experiments" (line ~242) — present-tense sweep
      (P4) would make this "We take this into account when choosing...".
- [ ] §Light Intensity Map: "the next section explaines how" (line ~131) — typo
      "explaines" → "explains"; and "if drift in position occurs the heading of the
      estimate and drone stays accurate" (line ~122) reads awkwardly.
- [ ] §System Overview: "The per-sensor light signals $S_n$ ... are writen into the
      light map" (line ~63) — typo "writen" → "written".
