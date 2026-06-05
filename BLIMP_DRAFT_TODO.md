# Blimp Draft TODO

Harry's review asks for the **blimp results** to be included in the thesis. The
agreed plan is to produce **two drafts** — one *with* the blimp results and one
*without* — and to **minimise the diff** between them. All non-blimp review
comments have already been processed on `single-sentence-draft`; the blimp work
below is intentionally isolated and should be done last so the two drafts differ
as little as possible.

> Blimp work lives in a separate repo:
> `~/Projects/University/Thesis/GT-MAB-simulator-webot/`

## Decision still open
- [ ] Confirm with supervisor / Marco whether the blimp results go in the final
      thesis (direct supervisor is in favour). This gates everything below.

## Edits required for the blimp draft (review comments #1, #30, #31)

### #1 — Introduction, Motivation (`chapters/introduction.tex`)
- [ ] Bring up the blimp platform/result in the opening motivation, where
      micro-UAVs are introduced. Keep it to one sentence/paragraph to stay within
      the single-sentence-draft style.

### #30 — Conclusions, Summary (`chapters/conclusions.tex`)
- [ ] Add the blimp real-world experiment to the summary; it links the real-world
      validation back to the simulation (the blimp also ran in the simulator).
      Currently the summary only mentions the CrazyFlie 2.1.

### #31 — Conclusions, Limitations (`chapters/conclusions.tex`)
- [ ] Revisit the operating-range limitation. Harry noted "on my blimp is fine" —
      i.e. the narrow operating band caused by the photodiode circuit may not apply
      (or applies differently) to the blimp, so this limitation likely needs
      rewording or qualifying in the blimp draft.

## Supporting content needed
- [ ] Blimp experiment results / figures to cite or include (from the
      GT-MAB-simulator-webot repo).
- [ ] Decide where blimp experiments sit relative to the CrazyFlie experiments in
      the Real-World chapter (own subsection? interleaved?).

## Mechanics for the two-draft approach
- [ ] Decide how to maintain both drafts (e.g. a `with-blimp` branch off
      `single-sentence-draft`, or a LaTeX toggle). Keep blimp content in clearly
      isolated blocks to minimise the diff.
