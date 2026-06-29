#!/usr/bin/env python3
"""
Illustrative ("mock") figures for Chapter 5, "Real-World Implementation".

IMPORTANT: every figure here uses SYNTHETIC data, generated only to make each
signal-pipeline step easy to picture. None of it is a real measurement; the real,
measured SNR figures are the filter-validation and ambient-light results in the
same chapter. These complement the example spectrum (fft_noise_floor_figure.py)
and the clean two-beacon spectrum of Chapter 3 (fft_mock_figure.py).

Outputs (into figures/):
    dsp_windowing.png   mean subtraction + Hamming window, and the leakage it removes
    dsp_welch.png       Welch averaging: a single noisy spectrum vs the averaged one
    dsp_ema.png         exponential moving average smoothing a noisy magnitude over time
    ambient_baseline.png  a higher ambient baseline compressing the beacon's swing

Usage:
    python scripts/dsp_illustration_figures.py
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle as fst   # 'fs' is used below for the sample rate

BLUE = "#1f3b73"
RED = "#d1495b"
TEAL = "#2a9d8f"
GREY = "grey"

fs = 500.0            # sample rate (Hz), matching the real platform
N = 256               # FFT size, matching the real platform
f_beacon = 150.0      # beacon modulation frequency (Hz)

SYN = "Synthetic data — not a real measurement"


def _synth_window(rng, freq=f_beacon, ambient=3000.0, amp=650.0, noise_sd=70.0):
    """One sampled window: a beacon sinusoid on an ambient baseline, plus noise."""
    t = np.arange(N) / fs
    return ambient + amp * np.sin(2 * np.pi * freq * t) + rng.normal(0, noise_sd, N)


def fig_windowing(out="figures/dsp_windowing.png"):
    """Three separate sub-panels (a/b/c), placed with \\subfigure in LaTeX.

    Titles and the rectangular-vs-Hamming legend live in the sub-captions, so
    each PNG is just its plot. ``out`` gives the base name; _a/_b/_c are written.
    """
    base = out[:-4] if out.endswith(".png") else out
    rng = np.random.default_rng(1)
    # A low illustrative frequency (off the FFT bin grid) so the individual
    # oscillations and the taper are both legible, and the leakage is visible.
    f_ill = 12.7
    amp = 650.0
    raw = _synth_window(rng, freq=f_ill, amp=amp, noise_sd=15.0)
    t_ms = np.arange(N) / fs * 1e3
    meaned = raw - raw.mean()
    ham = np.hamming(N)
    windowed = meaned * ham
    env = amp * ham

    # Spectra with a rectangular vs a Hamming window (single-sided, normalised).
    freqs = np.fft.rfftfreq(N, 1.0 / fs)
    spec_rect = np.abs(np.fft.rfft(meaned))
    spec_ham = np.abs(np.fft.rfft(windowed))
    spec_rect /= spec_rect.max()
    spec_ham /= spec_ham.max()

    # (a) Raw window — placed at 0.47\textwidth.
    fst.apply(2.35, frac=0.47, tick=8, label=8)
    fig, a = plt.subplots(figsize=(2.35, 1.95), layout="constrained")
    a.plot(t_ms, raw, color=BLUE, lw=1.1)
    a.axhline(raw.mean(), color=RED, ls="--", lw=1.0)
    a.set_ylim(0, raw.max() * 1.42)   # headroom for the label, clear of the trace
    a.text(t_ms[-1], raw.max() * 1.30, "mean (ambient)", color=RED,
           fontsize=fst.pt(7), va="center", ha="right")
    a.set_xlabel("Time (ms)")
    a.set_ylabel("Reading (ADC counts)")
    a.grid(True, alpha=0.3)
    fst.save(fig, base + "_a.png")
    plt.close(fig)

    # (b) Centred and tapered — 0.47\textwidth.
    fst.apply(2.35, frac=0.47, tick=8, label=8)
    fig, b = plt.subplots(figsize=(2.35, 1.95), layout="constrained")
    b.plot(t_ms, windowed, color=BLUE, lw=1.1)
    b.plot(t_ms, +env, color=TEAL, ls=":", lw=1.2)
    b.plot(t_ms, -env, color=TEAL, ls=":", lw=1.2)
    b.axhline(0, color="black", lw=0.6)
    b.set_ylim(-env.max() * 1.25, env.max() * 1.5)
    b.text(t_ms[N // 2], env.max() * 1.08, "Hamming taper", color=TEAL,
           fontsize=fst.pt(7), ha="center", va="bottom")
    b.set_xlabel("Time (ms)")
    b.set_ylabel("Centred reading")
    b.grid(True, alpha=0.3)
    fst.save(fig, base + "_b.png")
    plt.close(fig)

    # (c) Spectrum, with vs without the window — wider, 0.62\textwidth.
    fst.apply(3.1, frac=0.62, tick=8, label=8)
    fig, c = plt.subplots(figsize=(3.1, 2.1), layout="constrained")
    c.semilogy(freqs, spec_rect, color=GREY, lw=1.1)
    c.semilogy(freqs, spec_ham, color=BLUE, lw=1.3)
    c.set_xlim(0, 80)
    c.set_ylim(1e-4, 2)
    c.set_xlabel("Frequency (Hz)")
    c.set_ylabel("Normalised magnitude (log)")
    c.grid(True, which="both", alpha=0.3)
    c.annotate("Hamming", xy=(13, 1.0), xytext=(40, 4.5e-1),
               fontsize=fst.pt(7), color=BLUE, ha="center",
               arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9))
    c.annotate("rectangular:\nleakage skirts", xy=(33, 2.0e-2), xytext=(50, 7e-2),
               fontsize=fst.pt(7), color=GREY, ha="center",
               arrowprops=dict(arrowstyle="->", color=GREY, lw=0.9))
    fst.save(fig, base + "_c.png")
    plt.close(fig)


def fig_welch(out="figures/dsp_welch.png"):
    # Included at 0.85\textwidth -> 4.25 in. Scale 1: the PNG is the page.
    fst.apply(4.25, frac=0.85, tick=8, label=9, title=9, legend=8)
    rng = np.random.default_rng(4)
    ham = np.hamming(N)
    freqs = np.fft.rfftfreq(N, 1.0 / fs)

    def one_spec():
        w = _synth_window(rng, amp=650.0, noise_sd=120.0)
        return np.abs(np.fft.rfft((w - w.mean()) * ham))

    single = one_spec()
    n_avg = 16
    acc = np.zeros(len(freqs))
    for _ in range(n_avg):
        acc += one_spec()
    averaged = acc / n_avg

    fig, ax = plt.subplots(figsize=(4.25, 2.3))
    ax.semilogy(freqs, single, color=GREY, lw=1.0, alpha=0.9,
                label="single window: noisy floor")
    ax.semilogy(freqs, averaged, color=BLUE, lw=1.4,
                label=f"averaged over {n_avg} windows")
    ax.set_xlim(0, fs / 2)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("FFT magnitude (log scale)")
    ax.set_title(SYN, fontstyle="italic")
    ax.legend(loc="upper left")
    ax.grid(True, which="both", alpha=0.3)
    ax.annotate("beacon peak", xy=(f_beacon, averaged[int(round(f_beacon / (fs / N)))]),
                xytext=(f_beacon + 30, averaged.max() * 0.55), fontsize=fst.pt(7),
                color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.0))
    fig.tight_layout()
    fst.save(fig, out)


def fig_ema(out="figures/dsp_ema.png", alpha=0.5):
    # Included at 0.85\textwidth -> 4.25 in. Scale 1.
    fst.apply(4.25, frac=0.85, tick=8, label=9, title=9, legend=8)
    rng = np.random.default_rng(11)
    k = np.arange(120)
    # True magnitude steps up midway, as the drone moves nearer the beacon.
    true = np.where(k < 60, 1.0, 2.0)
    raw = true + rng.normal(0, 0.35, len(k))
    smoothed = np.empty_like(raw)
    smoothed[0] = raw[0]
    for i in range(1, len(raw)):
        smoothed[i] = alpha * smoothed[i - 1] + (1 - alpha) * raw[i]

    fig, ax = plt.subplots(figsize=(4.25, 2.2))
    ax.plot(k, raw, color=GREY, lw=0.9, alpha=0.8, label=r"raw per-frame $\hat{S}_n$")
    ax.plot(k, true, color=RED, ls="--", lw=1.1, label="true signal")
    ax.plot(k, smoothed, color=BLUE, lw=1.8,
            label=r"smoothed $S_n$ ($\alpha_m=%.1f$)" % alpha)
    ax.set_xlabel("Frame index")
    ax.set_ylabel("Per-channel magnitude (a.u.)")
    ax.set_title(SYN, fontstyle="italic")
    ax.legend(loc="upper left", handlelength=1.4)
    ax.grid(True, alpha=0.3)
    ax.annotate("smoothing lags\nthe step slightly", xy=(64, 1.6), xytext=(74, 1.02),
                fontsize=fst.pt(7), color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9))
    fig.tight_layout()
    fst.save(fig, out)


def fig_ambient(out="figures/ambient_baseline.png"):
    # Included at width=\textwidth -> 5.0 in (2 panels). Scale 1.
    fst.apply(5.0, frac=1.0, tick=8, label=9, title=9, suptitle=9)
    ADC_MAX = 4095.0
    t = np.arange(0, 0.04, 1.0 / 8000.0)
    sq = 0.5 * (1 + np.sign(np.sin(2 * np.pi * f_beacon * t)))   # 0/1 on-off
    amp = 1700.0
    dark = 350.0 + amp * sq
    lit = np.minimum(3100.0 + amp * sq, ADC_MAX)                 # clipped at the ceiling

    fig, (a, b) = plt.subplots(1, 2, figsize=(5.0, 2.4), sharey=True,
                               layout="constrained")
    for ax, sig, base, title, pp, lbl_y in [
            (a, dark, 350.0, "(a) Dark room: low baseline", amp, 2400),
            (b, lit, 3100.0, "(b) Lit room: high baseline", ADC_MAX - 3100.0, 2650)]:
        ax.plot(t * 1e3, sig, color=BLUE, lw=1.3)
        ax.axhline(ADC_MAX, color=GREY, ls="--", lw=1.0)
        ax.text(t[-1] * 1e3, ADC_MAX + 60, "ADC ceiling (4095)", color=GREY,
                fontsize=fst.pt(7), va="bottom", ha="right")
        ax.set_ylim(0, ADC_MAX * 1.13)
        ax.set_xlabel("Time (ms)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        # Peak-to-peak arrow at a fixed time; label placed in the empty half of
        # the panel (above the low-baseline wave, below the high-baseline one).
        x0 = 26
        lo, hi = base, base + pp
        ax.annotate("", xy=(x0, hi), xytext=(x0, lo),
                    arrowprops=dict(arrowstyle="<->", color=RED, lw=1.3))
        ax.text(x0, lbl_y, f"swing $\\approx${pp:.0f}", color=RED, ha="center",
                va="center", fontsize=fst.pt(7))
    a.set_ylabel("Photodiode reading (ADC counts)")
    fig.suptitle(SYN, fontstyle="italic")
    fst.save(fig, out)


if __name__ == "__main__":
    fig_windowing()
    fig_welch()
    fig_ema()
    fig_ambient()
