# Filter Validation — Run Plan

Experiment for Chapter 5 (`chp:realworld`), Section "Filter Validation", Table 5.1
(`tab:filter-snr`). Goal: show that each stage of the SNR pipeline is necessary and
quantify what it contributes, separating the *level* of the signal from its *stability*.

---

## 1. The metric (why hold still)

Hold the drone at a **fixed pose** relative to a **fixed beacon** so the *true* SNR is
constant. Then any variation in the logged SNR over time is noise/jitter — exactly what
the filters are meant to remove. We therefore report **two numbers per run**:

- **mean SNR** — the signal *level*. Raised by the hardware filter (removes aliased motor
  energy) and the median floor (rejects spikes that inflate the noise estimate).
- **std of SNR** — the *jitter*. Lowered by Welch averaging and the magnitude EMA.
- (also log **min / 5th-percentile SNR** — the worst case, which the median floor protects.)

Use the **max-across-channels SNR** (`logMaxSnr`, the value the gate actually uses) as the
primary number. `logChSnr[8]` is logged too, so a per-photodiode breakdown can go in the
appendix if wanted.

## 2. The four filters and their switches

| Filter | What it does | Firmware knob | Off | On |
|---|---|---|---|---|
| Hardware 500 Hz LP | analogue anti-alias (removes motor/switching noise) | populate filter pads on the PCB (Ch. 4) | pads bare | filter soldered |
| Welch averaging | averages overlapping FFT frames → lower variance | `nav.fftAvg` param (`pdFftAverages`, `pd_fft_analyzer.c`) | `1` | `2` |
| Median noise floor | median instead of mean over off-target bins → spike-robust | `nav.medianFloor` param (`pdNoiseFloorMedian`, `pd_fft_analyzer.c`) | `0` (mean) | `1` (median) |
| Magnitude EMA | per-channel exponential smoothing → lower jitter | `nav.magAlpha` param (`magIirAlpha`, `mode_manager.c`) | `0.0` | `0.5` |

DC removal and the Hamming window are part of the base analysis and stay **on** throughout.

All three software filters are now runtime params (no reflash needed between
SW configs — only the HW step C0→C1 requires resoldering). Per-config values:

| Config | `nav.fftAvg` | `nav.medianFloor` | `nav.magAlpha` |
|---|---|---|---|
| C0 | `1` | `0` | `0.0` |
| C1 | `1` | `0` | `0.0` |
| C2 | `2` | `0` | `0.0` |
| C3 | `2` | `1` | `0.0` |
| C4 | `2` | `1` | `0.5` |

Firmware defaults (`pdFftAverages=2`, `pdNoiseFloorMedian=1`, `magIirAlpha=0.5`)
correspond to the full pipeline (C4); set the params down to reach C0–C3.

## 3. Setup and controls (hold constant for every run)

- **Beacon**: single beacon at a known position, modulating at **150 Hz** (same setup as the
  other real-world experiments).
- **Pose**: one fixed distance + bearing at flight altitude. Pick a **mid-range** distance —
  SNR moderate, so differences are visible (not saturated, not at the floor). Same pose every run.
- **Lighting**: **dark room**, constant (ambient is a separate experiment).
- **Window**: log ~30–60 s per run; discard the first ~2 s (settling); **3 repeats** per condition.

**Motor states (the "cost of flight"):**
- **Motors off** — drone held on a **static rig/tripod** at flight altitude. Clean ceiling, no drift.
- **Motors on** — **free hover** at the same pose. (A clamped motors-on bench test would be
  cleaner if it ever becomes possible; free hover adds a little drift — see §7.)

## 4. Experiment matrix (cumulative ablation)

Each config is run at **Motors off** and **Motors on**, ×3 repeats.

| ID | Config | HW | Welch (`N_avg`) | Median floor | EMA (`α_m`) |
|----|--------|----|----|----|----|
| C0 | No filtering        | off (bare) | off (1) | off (mean)   | off (0)   |
| C1 | + Hardware          | **on**     | off (1) | off (mean)   | off (0)   |
| C2 | + Welch averaging   | on         | **on (2)** | off (mean) | off (0)   |
| C3 | + Median floor      | on         | on (2)  | **on (median)** | off (0) |
| C4 | + Magnitude EMA (full) | on      | on (2)  | on (median)  | **on (0.5)** |

5 configs × 2 motor states × 3 repeats = **30 logs** (~30–60 s each).

**Optional cross-check (leave-one-out, motors-on only):** full pipeline (C4) minus each of
Welch / Median / EMA, 3 extra configs, to confirm each filter still helps given the others.
For the appendix; skip if time-limited.

## 5. Procedure (ordered to resolder only once)

1. **HW pads bare.** Run **C0**: motors off ×3, motors on ×3.
2. **Solder the 500 Hz filter** onto the pads. HW now on for everything below.
3. **C1** (all SW off): off ×3, on ×3.
4. **C2** (`PD_FFT_AVERAGES=2`): off ×3, on ×3.
5. **C3** (+ median floor): off ×3, on ×3.
6. **C4** (+ `magIirAlpha=0.5`, full pipeline): off ×3, on ×3.

Keep the beacon, pose, distance, and room lighting identical across all of the above.

## 6. Logging and analysis

- Log `nav.snr` (= `logMaxSnr`, the overall max-across-channels SNR) and optionally
  `nav.snr0..7` to CSV over the radio/USB, as with the ambient flights in `data/`.
- **Name each CSV** `filter_<config>_<motor>[_<repeat>].csv`, e.g. `filter_c0_off_1.csv`,
  `filter_c4_on_3.csv` (config `c0`–`c4`, motor `off`/`on`). The analysis script parses this.
- Run `python scripts/filter_validation_stats.py data/filter_validation/` to get, per cell,
  the **mean ± std** (and min / 5th-percentile) over the steady window, plus a ready-to-paste
  LaTeX table body for `tab:filter-snr`. Use `--per-channel` for the 8-photodiode breakdown.
  It discards the first `--settle` seconds (default 2 s) and pools the repeats.

## 7. Hypotheses (how to read the result)

- **Motors off**: all configs ≈ same, high SNR, low std → the ceiling; filters do little here.
- **Motors on, C0**: lower mean, high std (motor noise + aliasing + spikes + jitter).
- **+ Hardware**: mean recovers (aliased motor energy removed).
- **+ Welch**: std drops.
- **+ Median**: std drops, worst-case (min) SNR recovers (spikes rejected).
- **+ EMA**: std drops further.

The off-vs-on gap is the cost of flight; closing it down the rows is each filter's contribution.

## 8. Caveats / limitations to state in the write-up

- **Free-hover drift**: the motors-on std includes a small contribution from position drift
  (true SNR moving slightly), not pure jitter. Mitigate with a moderate distance and a short,
  tight hover; the mean is robust to unbiased drift. Note this in the chapter.
- **150 Hz harmonics**: the 2nd–4th harmonics (300/450/600 Hz) exceed the 250 Hz Nyquist and
  alias back into the band — relevant to both the anti-alias filter's job and the median floor's
  harmonic-exclusion guard band. Reconcile this wording in §"From Intensity to SNR".
- **Single beacon, single pose**; ambient held dark. Repeats give a spread, not a full statistic.

## 9. Resulting thesis table (Table 5.1)

```
                     Motors off        Motors on
                     mean ± std        mean ± std
No filtering         --                --
+ Hardware           --                --
+ Welch averaging    --                --
+ Median floor       --                --
+ Magnitude EMA      --                --
        (SNR = max across the 8 channels; min/worst-case noted in text;
         per-photodiode breakdown optional in the appendix)
```
