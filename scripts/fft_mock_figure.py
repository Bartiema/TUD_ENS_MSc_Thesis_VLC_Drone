#!/usr/bin/env python3
"""
Illustrative ("mock") figure for Chapter 3, Section "Multi-Beacon Traversal":
how a frequency analysis separates two beacons modulated at different rates.

IMPORTANT: this uses SYNTHETIC data, generated only to show the principle. It is
not a real measurement. The real, measured beacon separation is presented in the
multi-beacon experiments chapter.

The synthetic photodiode reading is expressed in ADC counts (0..4095, the 12-bit
range of the real sensor): a steady ambient baseline plus two square-wave beacons
switched on and off at f1 and f2. One photodiode sees their sum. The left panel
shows a slice of that reading in time; the right panel shows the magnitude of its
discrete Fourier transform, where each beacon is a peak at its own frequency.

Usage:
    python scripts/fft_mock_figure.py [out.png]
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle as fst   # 'fs' is used below for the sampling rate

OUT = sys.argv[1] if len(sys.argv) > 1 else "figures/fft_mock.png"

# Included at width=\textwidth. Generate at scale 1 (5 in wide) so text is
# readable on the page; the PNG is the printed result.
fst.apply(5.0, frac=1.0, suptitle=9)

ADC_MAX = 4095.0               # 12-bit ADC full scale
f1, f2 = 150.0, 200.0          # beacon modulation frequencies (Hz)
fs = 4000.0                    # sampling rate for the illustration (Hz)
T = 0.2                        # signal length (s)
t = np.arange(0, T, 1.0 / fs)

ambient = 400.0                # steady baseline (ADC counts)
amp1, amp2 = 1900.0, 1300.0    # on-amplitudes; ambient + amp1 + amp2 < ADC_MAX

sq1 = 0.5 * (1 + np.sign(np.sin(2 * np.pi * f1 * t)))   # 0/1 on-off
sq2 = 0.5 * (1 + np.sign(np.sin(2 * np.pi * f2 * t)))
signal = ambient + amp1 * sq1 + amp2 * sq2

# Single-sided FFT magnitude.
N = len(signal)
window = np.hanning(N)
spec = np.abs(np.fft.rfft((signal - signal.mean()) * window))
freqs = np.fft.rfftfreq(N, 1.0 / fs)
spec /= spec.max()

fig, (axT, axF) = plt.subplots(1, 2, figsize=(5.0, 2.6), layout="constrained")

# Time domain (short slice for legibility).
slice_n = int(0.05 * fs)
axT.plot(t[:slice_n] * 1e3, signal[:slice_n], color="#1f3b73", lw=1.2)
axT.axhline(ADC_MAX, color="grey", ls="--", lw=1.0)
axT.text(0.5, ADC_MAX, "ADC saturation (4095)", va="bottom", ha="left",
         fontsize=fst.pt(7), color="grey")
axT.set_ylim(0, ADC_MAX * 1.08)
axT.set_xlabel("Time (ms)")
axT.set_ylabel("Photodiode reading (ADC counts)")
axT.set_title("Time domain")
axT.grid(True, alpha=0.3)

# Frequency domain.
axF.plot(freqs, spec, color="#1f3b73", lw=1.2)
axF.set_xlim(0, 800)
axF.set_ylim(0, 1.18)
axF.set_xlabel("Frequency (Hz)")
axF.set_ylabel("Normalised magnitude")
axF.set_title("Frequency domain (FFT)")
axF.grid(True, alpha=0.3)
# Labels stacked on the right, each pointing left to its peak, so they don't
# pile up over the two closely-spaced beacons.
for f, name, col, ty in [(f1, "beacon 1", "#d1495b", 1.02),
                         (f2, "beacon 2", "#2a9d8f", 0.86)]:
    axF.axvline(f, color=col, ls="--", lw=1.1, alpha=0.85)
    axF.annotate(f"{name} ({f:.0f} Hz)", xy=(f, 1.0), xytext=(430, ty),
                 ha="left", va="center", fontsize=fst.pt(7), color=col,
                 arrowprops=dict(arrowstyle="->", color=col, lw=1.0))
    for k in (3, 5):
        if f * k <= 800:
            axF.axvline(f * k, color=col, ls=":", lw=0.8, alpha=0.5)
axF.text(430, 0.46, "dotted: odd harmonics", ha="left", va="center",
         fontsize=fst.pt(7), color="grey")

fig.suptitle("Synthetic data — illustrates the principle, not a real measurement",
             fontstyle="italic")
fst.save(fig, OUT)
