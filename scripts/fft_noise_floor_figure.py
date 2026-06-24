#!/usr/bin/env python3
"""
Illustrative ("mock") figure for Chapter 5, "Real-World Implementation":
how the signal-to-noise ratio (SNR) is read from a single channel's spectrum,
and why the noise floor is estimated with a median rather than a mean.

IMPORTANT: this uses SYNTHETIC data, generated only to show the principle. It is
NOT a real measurement. The real, measured SNR figures are the filter-validation
and ambient-light results reported in the same chapter. This figure complements
the clean two-beacon spectrum of Chapter 3 (fft_mock_figure.py): there the peaks
sit on an idealised floor, whereas here a single beacon sits on a realistic noise
floor, with a spurious interference spike, so the SNR and the median floor can be
shown.

The synthetic channel sees one beacon modulated at 150 Hz, broadband noise, and a
narrow interference spike (e.g. a motor harmonic or mains pickup). It is processed
exactly as the real pipeline does: sampled at fs, mean-subtracted, Hamming-windowed,
transformed, and averaged over several windows (Welch). The plot marks the beacon
peak, the median and mean noise floors over the off-target bins, the excluded guard
band, and the resulting SNR = peak / median floor.

Usage:
    python scripts/fft_noise_floor_figure.py [out.png]
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

OUT = sys.argv[1] if len(sys.argv) > 1 else "figures/fft_noise_floor.png"

rng = np.random.default_rng(7)

fs = 500.0            # sample rate (Hz), matching the real platform
N = 256               # FFT size, matching the real platform
n_avg = 8             # windows averaged (Welch); larger than the platform's 2
                      # only to render a smooth, legible floor for the figure
f_beacon = 150.0      # beacon modulation frequency (Hz)
f_spikes = (50.0, 90.0)   # narrow interference spikes (e.g. mains, motor harmonic)

ambient = 1500.0      # steady baseline (ADC counts), removed by mean subtraction
amp_beacon = 900.0    # beacon swing
amp_spikes = (520.0, 300.0)   # interference swings
noise_sd = 110.0      # broadband noise standard deviation

window = np.hanning(N)
df = fs / N
freqs = np.fft.rfftfreq(N, 1.0 / fs)

# Average the magnitude spectra of several independent windows (Welch).
acc = np.zeros(len(freqs))
for _ in range(n_avg):
    t = np.arange(N) / fs
    sig = (ambient
           + amp_beacon * np.sin(2 * np.pi * f_beacon * t)
           + rng.normal(0.0, noise_sd, N))
    for fsp, asp in zip(f_spikes, amp_spikes):
        sig = sig + asp * np.sin(2 * np.pi * fsp * t)
    acc += np.abs(np.fft.rfft((sig - sig.mean()) * window))
spec = acc / n_avg

# Beacon bin and a guard band around it (mirrors the pipeline's exclusion).
beacon_bin = int(round(f_beacon / df))
guard = 10                                   # bins excluded each side
peak = spec[beacon_bin]

# Off-target bins: everything except DC and the guard band around the beacon.
mask = np.ones(len(spec), dtype=bool)
mask[0] = False
mask[max(0, beacon_bin - guard): beacon_bin + guard + 1] = False
median_floor = np.median(spec[mask])
mean_floor = np.mean(spec[mask])
snr = peak / median_floor

fig, ax = plt.subplots(figsize=(8.5, 4.2))
ax.semilogy(freqs, spec, color="#1f3b73", lw=1.3, zorder=3)

# Guard band shading.
gb_lo = (beacon_bin - guard) * df
gb_hi = (beacon_bin + guard) * df
ax.axvspan(gb_lo, gb_hi, color="#d1495b", alpha=0.10, zorder=1)
ax.text((gb_lo + gb_hi) / 2, peak * 1.35, "guard band\n(excluded)",
        ha="center", va="bottom", fontsize=8, color="#d1495b")

# Beacon peak.
ax.annotate(f"beacon peak ({f_beacon:.0f} Hz)",
            xy=(f_beacon, peak), xytext=(f_beacon + 28, peak * 1.0),
            fontsize=9, color="#1f3b73",
            arrowprops=dict(arrowstyle="->", color="#1f3b73", lw=1.0))

# Interference spikes.
ax.annotate("interference spikes\n(motor / mains)",
            xy=(f_spikes[0], spec[int(round(f_spikes[0] / df))]),
            xytext=(f_spikes[0] + 6, peak * 0.5),
            fontsize=8, color="#9a6700",
            arrowprops=dict(arrowstyle="->", color="#9a6700", lw=0.9))

# Noise floors.
ax.axhline(mean_floor, color="grey", ls=":", lw=1.3, zorder=2)
ax.text(fs / 2, mean_floor, " mean floor\n (pulled up by spikes)", va="center",
        ha="left", fontsize=8, color="grey")
ax.axhline(median_floor, color="#2a9d8f", ls="--", lw=1.3, zorder=2)
ax.text(fs / 2, median_floor * 0.78, " median floor\n (used for SNR)", va="center",
        ha="left", fontsize=8, color="#2a9d8f")

# SNR annotation.
ax.annotate("", xy=(f_beacon - 14, peak), xytext=(f_beacon - 14, median_floor),
            arrowprops=dict(arrowstyle="<->", color="black", lw=1.1))
ax.text(f_beacon - 20, np.sqrt(peak * median_floor),
        f"SNR =\npeak / floor\n$\\approx$ {snr:.0f}",
        ha="right", va="center", fontsize=9)

ax.set_xlim(0, fs / 2)
ax.set_ylim(median_floor * 0.25, peak * 2.2)
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Averaged FFT magnitude (log scale)")
ax.set_title("Synthetic data — illustrates how the SNR is read, not a real measurement",
             fontsize=10, fontstyle="italic")
ax.grid(True, which="both", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT, dpi=300, bbox_inches="tight")
print(f"Saved -> {OUT}  (peak={peak:.0f}, median floor={median_floor:.0f}, "
      f"mean floor={mean_floor:.0f}, SNR={snr:.1f})")
