"""
motor_noise_stats.py
Summarise the motor-noise experiment runs for Chapter 5 (MOTOR_NOISE_RUNPLAN.md).

Reads motor_<config>_<repeat>.csv files from the bare-pads and HW-filter
sessions, pools repeats, and produces:

  1. Terminal table   — mean ± std SNR per config per session
  2. LaTeX table body — paste into the thesis
  3. High-DPI PNG bar chart — grouped bars (bare vs hw) with std error bars;
     m4ext shown separately to highlight the vibration-isolation comparison

── Filename convention (case-insensitive) ────────────────────────────────────
    motor_<config>_<repeat>.csv
        config : m0 | m1 | m2 | m3 | m4 | m4ext
    e.g.  motor_m0_1.csv,  motor_m4_3.csv,  motor_m4ext_2.csv

── Session directories ────────────────────────────────────────────────────────
    ../runs/motor_noise/bare/   HW filter pads bare  (auto-detected)
    ../runs/motor_noise/hw/     HW filter soldered   (auto-detected)
Override with --bare / --hw.  Either session can be omitted (partial data).

── Usage ─────────────────────────────────────────────────────────────────────
    python motor_noise_stats.py                          # auto-detect sessions
    python motor_noise_stats.py --bare path/bare/        # explicit dirs
    python motor_noise_stats.py --hw   path/hw/
    python motor_noise_stats.py --plot motor_noise.png   # save bar chart
    python motor_noise_stats.py --settle 5.0             # longer discard
    python motor_noise_stats.py --out summary.csv        # save summary CSV
"""

import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

# ── Config metadata ───────────────────────────────────────────────────────────
CONFIG_ORDER = ['m0', 'm1', 'm2', 'm3', 'm4']
CONFIG_EXT   = 'm4ext'

CONFIG_LABEL = {
    'm0':   '0 motors',
    'm1':   '1 motor',
    'm2':   '2 motors',
    'm3':   '3 motors',
    'm4':   '4 motors',
    'm4ext':'4 motors (ext. wires)',
}
CONFIG_N = {'m0': 0, 'm1': 1, 'm2': 2, 'm3': 3, 'm4': 4, 'm4ext': 4}

SESSION_LABEL = {
    'bare': 'No HW filter (pads bare)',
    'hw':   'HW filter soldered',
}
SESSION_COLOR = {
    'bare': '#d62728',   # red
    'hw':   '#1f77b4',   # blue
}

FNAME_RE = re.compile(r'motor_(m[0-4](?:ext)?)_(\d+)', re.IGNORECASE)


# ── I/O helpers ───────────────────────────────────────────────────────────────

def find_csvs(directory: str) -> list[str]:
    return sorted(glob.glob(os.path.join(directory, '*.csv')))


def overall_snr(df: pd.DataFrame):
    if 'nav.snr' in df.columns:
        return df['nav.snr'].astype(float)
    ch = [f'nav.snr{i}' for i in range(8) if f'nav.snr{i}' in df.columns]
    if ch:
        return (df[ch].astype(float) * 0.01).max(axis=1)
    return None


def steady_window(df: pd.DataFrame, settle_s: float) -> pd.DataFrame:
    ts_col = 'timestamp_ms' if 'timestamp_ms' in df.columns else df.columns[0]
    t = (df[ts_col] - df[ts_col].iloc[0]) / 1000.0
    return df[t >= settle_s]


def stats(samples: np.ndarray) -> dict:
    s = samples[np.isfinite(samples)]
    if s.size == 0:
        return dict(n=0, mean=np.nan, std=np.nan, p5=np.nan)
    return dict(
        n=int(s.size),
        mean=float(np.mean(s)),
        std=float(np.std(s, ddof=1)) if s.size > 1 else 0.0,
        p5=float(np.percentile(s, 5)),
    )


def collect(directory: str, settle_s: float) -> tuple[dict, list]:
    """Return {config: pooled_snr_array} and list of skipped filenames."""
    pooled, skipped = {}, []
    for p in find_csvs(directory):
        m = FNAME_RE.search(os.path.basename(p))
        if not m:
            skipped.append(os.path.basename(p))
            continue
        cfg = m.group(1).lower()
        try:
            df = steady_window(pd.read_csv(p), settle_s)
        except Exception as e:
            skipped.append(f"{os.path.basename(p)} ({e})")
            continue
        snr = overall_snr(df)
        if snr is None:
            skipped.append(os.path.basename(p) + ' (no SNR column)')
            continue
        pooled.setdefault(cfg, []).append(snr.to_numpy())
    return {cfg: np.concatenate(arrs) for cfg, arrs in pooled.items()}, skipped


def fmt_latex(mean, std):
    if not np.isfinite(mean):
        return '--'
    return f'{mean:.1f} \\pm {std:.1f}'


# ── Plot ──────────────────────────────────────────────────────────────────────

def make_plot(session_data: dict, out_path: str, frac: float = 0.85):
    """
    session_data: {session_key: {config: stats_dict}}
    session_key in ('bare', 'hw')
    frac: on-page width as a fraction of \\textwidth (controls text scaling).
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import matplotlib.ticker as mticker
    except ImportError:
        print("matplotlib not installed — skipping plot.", file=sys.stderr)
        return

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import figstyle as fs

    # Native canvas: enlarge only the text so it reads at ~8-9 pt once LaTeX
    # scales the figure to its on-page width (frac * textwidth). The on-page
    # width is fixed by \includegraphics, so a taller canvas just buys vertical
    # room for the (now larger) titles and axis labels without shrinking text.
    FIG_W, FIG_H = 9.0, 5.2
    fs.apply(FIG_W, frac)

    available_sessions = [s for s in ('bare', 'hw') if s in session_data]
    n_sessions = len(available_sessions)

    fig, axes = plt.subplots(
        1, 2,
        figsize=(FIG_W, FIG_H),
        gridspec_kw={'width_ratios': [5, 1.4]},
        layout='constrained',
    )
    ax, ax_ext = axes

    bar_w  = 0.35
    x      = np.arange(len(CONFIG_ORDER))
    offset = np.linspace(-(n_sessions - 1) / 2, (n_sessions - 1) / 2, n_sessions) * bar_w

    for si, session in enumerate(available_sessions):
        sdata  = session_data[session]
        means  = [sdata.get(cfg, {}).get('mean', np.nan) for cfg in CONFIG_ORDER]
        stds   = [sdata.get(cfg, {}).get('std',  np.nan) for cfg in CONFIG_ORDER]
        ax.bar(
            x + offset[si], means, bar_w,
            yerr=stds, capsize=3,
            color=SESSION_COLOR[session], alpha=0.85,
            label=SESSION_LABEL[session],
            error_kw=dict(elinewidth=1, ecolor='#333333'),
        )

    ax.set_xticks(x)
    ax.set_xticklabels([CONFIG_LABEL[c].replace(' motors', '') for c in CONFIG_ORDER])
    ax.set_xlabel('Number of spinning motors')
    ax.set_ylabel('SNR (mean ± std)')
    ax.set_title('Motor noise vs. N motors')
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False, fontsize=fs.pt(8), loc='upper center')
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(1))

    # ── Right panel: m4ext vibration-isolation comparison ─────────────────
    ax_ext.set_title('Vib. isolation\n(4 motors)', fontsize=fs.pt(9))
    ext_x = np.arange(n_sessions)
    for si, session in enumerate(available_sessions):
        sdata = session_data[session]
        # Show m4 (close-mount) as faded reference and m4ext as solid
        m4_st  = sdata.get('m4',    {})
        ext_st = sdata.get('m4ext', {})
        color  = SESSION_COLOR[session]
        if np.isfinite(m4_st.get('mean', np.nan)):
            ax_ext.bar(si - 0.2, m4_st['mean'], 0.35,
                       yerr=m4_st.get('std', 0), capsize=3,
                       color=color, alpha=0.35,
                       error_kw=dict(elinewidth=1, ecolor='#333333'))
        if np.isfinite(ext_st.get('mean', np.nan)):
            ax_ext.bar(si + 0.2, ext_st['mean'], 0.35,
                       yerr=ext_st.get('std', 0), capsize=3,
                       color=color, alpha=0.85, hatch='//',
                       error_kw=dict(elinewidth=1, ecolor='#333333'))

    ax_ext.set_xticks(ext_x)
    ax_ext.set_xticklabels([s[:2].upper() for s in available_sessions], fontsize=fs.pt(8))
    ax_ext.set_ylabel('')
    ax_ext.yaxis.set_tick_params(labelleft=False)
    ax_ext.spines[['top', 'right']].set_visible(False)
    ax_ext.set_ylim(ax.get_ylim())
    ax_ext.yaxis.set_minor_locator(mticker.MultipleLocator(1))

    # Legend for right panel
    solid_patch  = mpatches.Patch(facecolor='grey', alpha=0.85, hatch='//', label='Ext. wires')
    faded_patch  = mpatches.Patch(facecolor='grey', alpha=0.35,             label='Close-mount')
    ax_ext.legend(handles=[solid_patch, faded_patch], fontsize=fs.pt(7),
                  frameon=False, loc='upper left')

    # Constrained layout (set at figure creation) fits the larger titles and
    # axis labels within the canvas. Save at the native width (no 'tight' crop)
    # so the figstyle scale holds.
    fs.save(fig, out_path, dpi=300)
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    default_base = os.path.join(os.path.dirname(__file__), '..', 'runs', 'motor_noise')

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bare', default=os.path.join(default_base, 'bare'),
                    help='Directory of bare-pads session CSVs.')
    ap.add_argument('--hw',   default=os.path.join(default_base, 'hw'),
                    help='Directory of HW-filter-soldered session CSVs.')
    ap.add_argument('--settle', type=float, default=2.0,
                    help='Seconds to discard at the start of each run (default 2.0).')
    ap.add_argument('--plot', default=None, metavar='FILE.png',
                    help='Save bar chart to this PNG file (300 dpi).')
    ap.add_argument('--page-frac', type=float, default=0.85, dest='page_frac',
                    help='On-page width as a fraction of \\textwidth '
                         '(controls text scaling; default 0.85).')
    ap.add_argument('--out',  default=None, metavar='FILE.csv',
                    help='Save summary statistics to this CSV.')
    args = ap.parse_args()

    # ── Load sessions ─────────────────────────────────────────────────────
    sessions = {}
    for key, path in [('bare', args.bare), ('hw', args.hw)]:
        if not os.path.isdir(path):
            print(f"  [{key}] directory not found, skipping: {path}")
            continue
        pooled, skipped = collect(path, args.settle)
        if skipped:
            print(f"  [{key}] skipped: {', '.join(skipped)}")
        if pooled:
            sessions[key] = {cfg: stats(arr) for cfg, arr in pooled.items()}
            print(f"  [{key}] loaded {len(pooled)} config(s): "
                  f"{', '.join(sorted(pooled))}")
        else:
            print(f"  [{key}] no matching CSVs found.")

    if not sessions:
        print("No data found. Check --bare / --hw paths.", file=sys.stderr)
        sys.exit(1)

    all_cfgs     = CONFIG_ORDER + ([CONFIG_EXT] if any(CONFIG_EXT in s for s in sessions.values()) else [])
    col_w        = 26
    session_keys = [k for k in ('bare', 'hw') if k in sessions]

    # ── Terminal table ────────────────────────────────────────────────────
    print()
    header = f"{'Config':<{col_w}}" + ''.join(f"{SESSION_LABEL[k]:>22}" for k in session_keys)
    print(header)
    print('-' * len(header))

    csv_rows = []
    for cfg in all_cfgs:
        row_str = f"{CONFIG_LABEL[cfg]:<{col_w}}"
        for k in session_keys:
            st = sessions[k].get(cfg)
            if st and np.isfinite(st['mean']):
                row_str += f"  {st['mean']:5.1f} ± {st['std']:4.1f}  (n={st['n']:4d})"
            else:
                row_str += f"{'--':>22}"
            if st:
                csv_rows.append(dict(session=k, config=cfg,
                                     label=CONFIG_LABEL[cfg], **st))
        print(row_str)

    # ── LaTeX table body ──────────────────────────────────────────────────
    print('\nLaTeX table body:\n')
    col_headers = ' & '.join(f'\\textbf{{{SESSION_LABEL[k]}}}' for k in session_keys)
    print(f'        \\textbf{{Config}} & {col_headers} \\\\')
    print('        \\midrule')
    for cfg in CONFIG_ORDER:
        cells = []
        for k in session_keys:
            st = sessions[k].get(cfg)
            cells.append(f'${fmt_latex(st["mean"], st["std"])}$' if st and np.isfinite(st['mean']) else '--')
        print(f"        {CONFIG_LABEL[cfg]:<20} & {' & '.join(cells)} \\\\")

    if CONFIG_EXT in (sessions.get('bare', {}) | sessions.get('hw', {})):
        print('        \\midrule')
        cells = []
        for k in session_keys:
            st = sessions[k].get(CONFIG_EXT)
            cells.append(f'${fmt_latex(st["mean"], st["std"])}$' if st and np.isfinite(st['mean']) else '--')
        print(f"        {CONFIG_LABEL[CONFIG_EXT]:<20} & {' & '.join(cells)} \\\\")

    # ── Vibration isolation addendum ──────────────────────────────────────
    has_ext = any(CONFIG_EXT in s for s in sessions.values())
    if has_ext:
        print('\n' + '-' * len(header))
        print('Vibration isolation (m4ext vs m4) — EMI vs mechanical contribution:\n')
        for k in session_keys:
            m4_st  = sessions[k].get('m4')
            ext_st = sessions[k].get(CONFIG_EXT)
            if not (m4_st and ext_st):
                continue
            if np.isfinite(m4_st['mean']) and np.isfinite(ext_st['mean']):
                delta = m4_st['mean'] - ext_st['mean']
                pct   = 100 * delta / (m4_st['mean'] - sessions[k].get('m0', {}).get('mean', m4_st['mean']) + 1e-9)
                print(f"  [{SESSION_LABEL[k]}]")
                print(f"    Close-mount (m4): {m4_st['mean']:.1f} ± {m4_st['std']:.1f}")
                print(f"    Ext. wires (m4ext): {ext_st['mean']:.1f} ± {ext_st['std']:.1f}")
                print(f"    Δ = {delta:+.1f}  ({pct:.0f}% of m0→m4 drop is mechanical vibration)")

    # ── Save CSV ──────────────────────────────────────────────────────────
    if args.out:
        pd.DataFrame(csv_rows).to_csv(args.out, index=False)
        print(f'\nWrote summary: {args.out}')

    # ── Plot ──────────────────────────────────────────────────────────────
    if args.plot:
        make_plot({k: sessions[k] for k in session_keys}, args.plot,
                  frac=args.page_frac)


if __name__ == '__main__':
    main()
