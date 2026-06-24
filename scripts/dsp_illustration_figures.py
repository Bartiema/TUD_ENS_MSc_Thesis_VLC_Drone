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

import numpy as np
import matplotlib.pyplot as plt

BLUE = "#1f3b73"
RED = "#d1495b"
TEAL = "#2a9d8f"
GREY = "grey"

fs = 500.0            # sample rate (Hz), matching the real platform
N = 256               # FFT size, matching the real platform
f_beacon = 150.0      # beacon modulation frequency (Hz)

SYN = "Synthetic data — illustrates the principle only, not a real measurement"


def _synth_window(rng, freq=f_beacon, ambient=3000.0, amp=650.0, noise_sd=70.0):
    """One sampled window: a beacon sinusoid on an ambient baseline, plus noise."""
    t = np.arange(N) / fs
    return ambient + amp * np.sin(2 * np.pi * freq * t) + rng.normal(0, noise_sd, N)


def fig_windowing(out="figures/dsp_windowing.png"):
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

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(12, 3.6))

    a.plot(t_ms, raw, color=BLUE, lw=1.2)
    a.axhline(raw.mean(), color=RED, ls="--", lw=1.0)
    a.text(t_ms[-1], raw.mean(), " mean\n (ambient)", color=RED, fontsize=8, va="center")
    a.set_title("(a) Raw sampled window")
    a.set_xlabel("Time (ms)")
    a.set_ylabel("Photodiode reading (ADC counts)")
    a.set_ylim(0, raw.max() * 1.15)

    b.plot(t_ms, windowed, color=BLUE, lw=1.2)
    b.plot(t_ms, +env, color=TEAL, ls=":", lw=1.2)
    b.plot(t_ms, -env, color=TEAL, ls=":", lw=1.2)
    b.text(t_ms[N // 2], env.max() * 1.04, "Hamming taper", color=TEAL,
           fontsize=8, ha="center", va="bottom")
    b.axhline(0, color="black", lw=0.6)
    b.set_title("(b) After mean subtraction\nand Hamming taper")
    b.set_xlabel("Time (ms)")
    b.set_ylabel("Centred reading")

    c.semilogy(freqs, spec_rect, color=GREY, lw=1.1, label="no window (rectangular)")
    c.semilogy(freqs, spec_ham, color=BLUE, lw=1.3, label="Hamming window")
    c.set_xlim(0, 80)
    c.set_ylim(1e-4, 2)
    c.set_title("(c) Spectrum, with and\nwithout the window")
    c.set_xlabel("Frequency (Hz)")
    c.set_ylabel("Normalised magnitude (log)")
    c.legend(fontsize=8, loc="upper right")
    c.annotate("leakage skirts", xy=(30, 1.5e-2), xytext=(45, 4e-1),
               fontsize=8, color=GREY,
               arrowprops=dict(arrowstyle="->", color=GREY, lw=0.9))

    for ax in (a, b, c):
        ax.grid(True, alpha=0.3)
    fig.suptitle(SYN, fontsize=10, fontstyle="italic", y=1.02)
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"Saved -> {out}")


def fig_welch(out="figures/dsp_welch.png"):
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

    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    ax.semilogy(freqs, single, color=GREY, lw=1.0, alpha=0.9,
                label="single window: noisy floor")
    ax.semilogy(freqs, averaged, color=BLUE, lw=1.4,
                label=f"averaged over {n_avg} windows: smoother floor")
    ax.set_xlim(0, fs / 2)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("FFT magnitude (log scale)")
    ax.set_title(SYN, fontsize=10, fontstyle="italic")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, which="both", alpha=0.3)
    ax.annotate("beacon peak", xy=(f_beacon, averaged[int(round(f_beacon / (fs / N)))]),
                xytext=(f_beacon + 30, averaged.max() * 0.6), fontsize=9, color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.0))
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"Saved -> {out}")


def fig_ema(out="figures/dsp_ema.png", alpha=0.5):
    rng = np.random.default_rng(11)
    k = np.arange(120)
    # True magnitude steps up midway, as the drone moves nearer the beacon.
    true = np.where(k < 60, 1.0, 2.0)
    raw = true + rng.normal(0, 0.35, len(k))
    smoothed = np.empty_like(raw)
    smoothed[0] = raw[0]
    for i in range(1, len(raw)):
        smoothed[i] = alpha * smoothed[i - 1] + (1 - alpha) * raw[i]

    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.plot(k, raw, color=GREY, lw=0.9, alpha=0.8, label=r"raw per-frame $\hat{S}_n$")
    ax.plot(k, true, color=RED, ls="--", lw=1.1, label="true signal")
    ax.plot(k, smoothed, color=BLUE, lw=1.8,
            label=r"smoothed $S_n$ ($\alpha_m=%.1f$)" % alpha)
    ax.set_xlabel("Frame index")
    ax.set_ylabel("Per-channel magnitude (a.u.)")
    ax.set_title(SYN, fontsize=10, fontstyle="italic")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.annotate("smoothing lags\nthe step slightly", xy=(64, 1.6), xytext=(74, 1.05),
                fontsize=8, color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9))
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"Saved -> {out}")


def fig_ambient(out="figures/ambient_baseline.png"):
    ADC_MAX = 4095.0
    t = np.arange(0, 0.04, 1.0 / 8000.0)
    sq = 0.5 * (1 + np.sign(np.sin(2 * np.pi * f_beacon * t)))   # 0/1 on-off
    amp = 1700.0
    dark = 350.0 + amp * sq
    lit = np.minimum(3100.0 + amp * sq, ADC_MAX)                 # clipped at the ceiling

    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, sig, base, title, pp in [
            (a, dark, 350.0, "(a) Darkened room: low baseline", amp),
            (b, lit, 3100.0, "(b) Lit room: high baseline", ADC_MAX - 3100.0)]:
        ax.plot(t * 1e3, sig, color=BLUE, lw=1.4)
        ax.axhline(ADC_MAX, color=GREY, ls="--", lw=1.0)
        ax.text(t[-1] * 1e3, ADC_MAX, " ADC ceiling (4095)", color=GREY, fontsize=8,
                va="top", ha="right")
        ax.set_ylim(0, ADC_MAX * 1.10)
        ax.set_xlabel("Time (ms)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        # Peak-to-peak arrow at a fixed time.
        x0 = 26
        lo, hi = base, base + pp
        ax.annotate("", xy=(x0, hi), xytext=(x0, lo),
                    arrowprops=dict(arrowstyle="<->", color=RED, lw=1.3))
        ax.text(x0 + 0.6, (lo + hi) / 2, f"swing\n$\\approx${pp:.0f}", color=RED,
                fontsize=8, va="center")
    a.set_ylabel("Photodiode reading (ADC counts)")
    fig.suptitle(SYN, fontsize=10, fontstyle="italic", y=1.02)
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    fig_windowing()
    fig_welch()
    fig_ema()
    fig_ambient()
