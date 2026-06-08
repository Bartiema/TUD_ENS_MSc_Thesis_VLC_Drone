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

### #1 — Introduction, Motivation (`chapters/introduction.tex`) — DONE
- [x] Added one sentence after the micro-UAV/endurance opening: LTA blimps address
      endurance and serve as a second validation platform. Cites `huang2026lta`.
- [ ] Confirm the `huang2026lta` bib entry author list/order + publication status
      (entry currently `Harry Huang and others`, "Under submission").

### #30 — Conclusions, Summary (`chapters/conclusions.tex`) — DONE
- [x] Added a sentence at the end of the Summary: the same controller was also
      deployed on the LTA blimp, strengthening the sim<->real link. Cites
      `huang2026lta`. (All three controllers, incl. the fused one, flew on the
      real blimp; achieved multi-target, obstacle avoidance, better SNR.)

### #31 — Conclusions, Limitations (`chapters/conclusions.tex`) — DONE
- [x] Scoped the narrow-operating-band limitation to the CrazyFlie platform; added
      that the blimp has significantly better SNR; cause left as future work with
      motor-proximity / power / EMI / reflection as plausible-but-unverified
      hypotheses (not stated as facts). Three single-sentence paragraphs.

## Supporting content needed
- [ ] Blimp experiment results / figures to cite or include (from the
      GT-MAB-simulator-webot repo).
- [ ] Decide where blimp experiments sit relative to the CrazyFlie experiments in
      the Real-World chapter (own subsection? interleaved?).

## Mechanics for the two-draft approach
- [ ] Decide how to maintain both drafts (e.g. a `with-blimp` branch off
      `single-sentence-draft`, or a LaTeX toggle). Keep blimp content in clearly
      isolated blocks to minimise the diff.
