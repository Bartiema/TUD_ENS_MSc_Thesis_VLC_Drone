"""
filter_validation_stats.py
Summarise the filter-validation runs for Chapter 5, Table 5.1 (tab:filter-snr).

Reads a collection of CrazyFlie session CSVs (same format as plot_session.py:
a `timestamp_ms` column, an overall `nav.snr` column = max SNR across channels,
and optional per-channel `nav.snr0`…`nav.snr7` stored as int16 ×100), groups
them by filter configuration and motor state, and reports the mean, std, and
worst-case SNR over the steady part of each run.

The drone is held at a fixed pose, so the true SNR is constant and the spread
over time is the jitter the filters are meant to remove (see
FILTER_VALIDATION_RUNPLAN.md). We therefore report both the level (mean) and the
stability (std), plus the worst-case (5th percentile / min) for the median floor.

── Filename convention (case-insensitive) ─────────────────────────────────────
    filter_<config>_<motor>[_<repeat>].csv
        config : c0 | c1 | c2 | c3 | c4
        motor  : off | on
    e.g.  filter_c0_off_1.csv,  filter_c4_on_3.csv
Repeats of the same (config, motor) cell are pooled.

── Usage ───────────────────────────────────────────────────────────────────────
    python scripts/filter_validation_stats.py data/filter_validation/
    python scripts/filter_validation_stats.py "data/filter_validation/*.csv"
    python scripts/filter_validation_stats.py DIR --settle 2.0 --out summary.csv
    python scripts/filter_validation_stats.py DIR --per-channel   # 8-PD breakdown
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

# Cumulative ablation configs, in pipeline order, with display labels.
CONFIG_ORDER = ["c0", "c1", "c2", "c3", "c4"]
CONFIG_LABEL = {
    "c0": "No filtering",
    "c1": "+ Hardware",
    "c2": "+ Welch averaging",
    "c3": "+ Median floor",
    "c4": "+ Magnitude EMA",
}
MOTOR_ORDER = ["off", "on"]

FNAME_RE = re.compile(r"filter_(c[0-4])_(off|on)(?:_(\d+))?", re.IGNORECASE)


def find_csvs(arg: str):
    """Accept a directory, a glob, or a single file; return a sorted list."""
    if os.path.isdir(arg):
        paths = glob.glob(os.path.join(arg, "*.csv"))
    else:
        paths = glob.glob(arg)
    return sorted(paths)


def overall_snr(df: pd.DataFrame) -> "pd.Series | None":
    """Overall (max-across-channels) SNR. Prefer nav.snr; else build from nav.snrN."""
    if "nav.snr" in df.columns:
        return df["nav.snr"].astype(float)
    ch = [f"nav.snr{i}" for i in range(8) if f"nav.snr{i}" in df.columns]
    if ch:
        return (df[ch].astype(float) * 0.01).max(axis=1)
    return None


def steady_window(df: pd.DataFrame, settle_s: float) -> pd.DataFrame:
    """Drop the first `settle_s` seconds (settling) using timestamp_ms."""
    ts_col = "timestamp_ms" if "timestamp_ms" in df.columns else df.columns[0]
    t = (df[ts_col] - df[ts_col].iloc[0]) / 1000.0
    return df[t >= settle_s]


def stats(samples: np.ndarray) -> dict:
    s = samples[np.isfinite(samples)]
    if s.size == 0:
        return dict(n=0, mean=np.nan, std=np.nan, min=np.nan, p5=np.nan)
    return dict(
        n=int(s.size),
        mean=float(np.mean(s)),
        std=float(np.std(s, ddof=1)) if s.size > 1 else 0.0,
        min=float(np.min(s)),
        p5=float(np.percentile(s, 5)),
    )


def collect(paths, settle_s, per_channel):
    """Return {(config, motor): pooled samples}. Samples are overall SNR, or a
    dict of per-channel arrays when per_channel is set."""
    pooled = {}
    skipped = []
    for p in paths:
        m = FNAME_RE.search(os.path.basename(p))
        if not m:
            skipped.append(os.path.basename(p))
            continue
        cfg, motor = m.group(1).lower(), m.group(2).lower()
        df = steady_window(pd.read_csv(p), settle_s)
        key = (cfg, motor)
        if per_channel:
            bucket = pooled.setdefault(key, {i: [] for i in range(8)})
            for i in range(8):
                col = f"nav.snr{i}"
                if col in df.columns:
                    bucket[i].append(df[col].astype(float).to_numpy() * 0.01)
        else:
            snr = overall_snr(df)
            if snr is None:
                skipped.append(os.path.basename(p) + " (no SNR column)")
                continue
            pooled.setdefault(key, []).append(snr.to_numpy())
    return pooled, skipped


def fmt(mean, std):
    if not np.isfinite(mean):
        return "--"
    return f"{mean:.1f} \\pm {std:.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="Directory, glob, or single CSV of filter-validation runs.")
    ap.add_argument("--settle", type=float, default=2.0,
                    help="Seconds to discard at the start of each run (default 2.0).")
    ap.add_argument("--per-channel", action="store_true",
                    help="Report the 8-photodiode breakdown instead of the overall SNR.")
    ap.add_argument("--out", default=None, help="Write the summary to this CSV.")
    args = ap.parse_args()

    paths = find_csvs(args.path)
    if not paths:
        print(f"No CSV files found at: {args.path}", file=sys.stderr)
        sys.exit(1)

    pooled, skipped = collect(paths, args.settle, args.per_channel)
    if skipped:
        print("Skipped (name did not match filter_<c0-4>_<off|on>_*.csv):")
        for s in skipped:
            print(f"  {s}")
    if not pooled:
        print("No matching runs to summarise.", file=sys.stderr)
        sys.exit(1)

    rows = []  # for the output CSV

    if args.per_channel:
        print("\nPer-photodiode SNR (mean +/- std over the steady window):\n")
        for cfg in CONFIG_ORDER:
            for motor in MOTOR_ORDER:
                bucket = pooled.get((cfg, motor))
                if not bucket:
                    continue
                print(f"{CONFIG_LABEL[cfg]:<20} motors {motor}")
                for i in range(8):
                    arr = np.concatenate(bucket[i]) if bucket[i] else np.array([])
                    st = stats(arr)
                    print(f"    PD{i}: {st['mean']:.1f} +/- {st['std']:.1f}  "
                          f"(min {st['min']:.1f}, n={st['n']})")
                    rows.append(dict(config=CONFIG_LABEL[cfg], motor=motor,
                                     channel=f"PD{i}", **st))
    else:
        # Main 5x2 table: config rows, motors off/on columns, mean +/- std.
        col_w = 20
        print("\nOverall SNR (max across channels), mean +/- std over the steady window:\n")
        print(f"{'Configuration':<{col_w}} {'Motors off':>18} {'Motors on':>18}")
        print("-" * (col_w + 38))
        latex_rows = []
        for cfg in CONFIG_ORDER:
            cells = {}
            for motor in MOTOR_ORDER:
                runs = pooled.get((cfg, motor))
                st = stats(np.concatenate(runs)) if runs else stats(np.array([]))
                cells[motor] = st
                rows.append(dict(config=CONFIG_LABEL[cfg], motor=motor, **st))
            off, on = cells["off"], cells["on"]
            off_s = "--" if not np.isfinite(off["mean"]) else f"{off['mean']:.1f} +/- {off['std']:.1f}"
            on_s = "--" if not np.isfinite(on["mean"]) else f"{on['mean']:.1f} +/- {on['std']:.1f}"
            print(f"{CONFIG_LABEL[cfg]:<{col_w}} {off_s:>18} {on_s:>18}")
            latex_rows.append(
                f"        {CONFIG_LABEL[cfg]:<19}& ${fmt(off['mean'], off['std'])}$ "
                f"& ${fmt(on['mean'], on['std'])}$ \\\\")

        print("\nLaTeX table body (paste into tab:filter-snr):\n")
        print("\n".join(latex_rows))

    if args.out:
        pd.DataFrame(rows).to_csv(args.out, index=False)
        print(f"\nWrote summary: {args.out}")


if __name__ == "__main__":
    main()
