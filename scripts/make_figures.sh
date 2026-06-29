#!/usr/bin/env bash
#
# Regenerate every in-scope thesis figure from its source data.
#
# All figures are drawn at "scale 1": each is generated at its true on-page
# width (figsize = frac * textwidth, with textwidth = 5 in) so the saved PNG is
# exactly what prints. Fonts are kept readable (in-plot text ~7 pt next to the
# 10 pt body) via scripts/figstyle.py. See that module for the sizing model.
#
# Run from anywhere:   bash scripts/make_figures.sh
# Needs python3 with matplotlib/numpy/pandas/scipy (the nix dev shell provides
# them: `nix develop` then run this).
#
# Figures deliberately NOT regenerated here (kept as-is, see the thesis figure
# list): teensy_test_setup, simulation_setup, real_life_setup*, new/old_pcb_*,
# motor_noise, teensy_multi_freq_tests/*.

set -euo pipefail

# Repo root = parent of this script's directory.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
S="scripts"

echo "== Standalone illustrative figures =="
$PY $S/single_pd_gradient_figure.py
$PY $S/fft_mock_figure.py
$PY $S/fft_noise_floor_figure.py
$PY $S/dsp_illustration_figures.py        # dsp_welch, dsp_ema, ambient_baseline, dsp_windowing_a/b/c
$PY $S/light_map_figure.py

echo "== Gradient-fitting analysis (comparison + numbered performance bars) =="
$PY $S/gradient_fitting_analyzer.py data/gradient_analysis/precomputed_map.csv

echo "== Simulation blimp trajectories (0.6 textwidth) =="
# gradient-only and bearing-only collide -> --trim-at-contact stops the path at
# first contact; fused clears the pillar so it is drawn in full.
$PY $S/trajectory_analyzer.py data/gradient_only_sim/history_gradient_trajectory.csv \
    --controller gradient --trim-at-contact --only-2d --page-frac 0.6 \
    --outdir figures/gradient_only_sim
$PY $S/trajectory_analyzer.py data/bearing_only_sim/trajectory_debug.csv \
    --controller bearing --trim-at-contact --only-2d --page-frac 0.6 \
    --outdir figures/bearing_only_sim
$PY $S/trajectory_analyzer.py data/fused_sim/fixed_fusion_trajectory.csv \
    --controller fused --only-2d --page-frac 0.6 \
    --outdir figures/fused_sim

# ---------------------------------------------------------------------------
# plot_session.py figures. Validated CLI parameters:
#   * real_data lights:   150 Hz -> (3.20,0.70) / (3.20,0.50);
#                         170 Hz -> (3.00,1.80) / (2.70,1.80).
#     obstacle is auto-parsed from the "_obs.." filename.
#   * obstacle dodges:    waypoint 0 is the dodge; obstacle boxes per flight.
#   * page-frac per chapter slot: survey/multi-beacon 1.0, ambient 0.95,
#                                 obstacle 0.85.
# ---------------------------------------------------------------------------
PS="$PY $S/plot_session.py"

echo "== Real-world lawnmower SNR surveys (textwidth) =="
RD=data/real_data_gather_flights ; RO=figures/real_data_gather_flights
$PS $RD/data_gather_150hz_3.0x1.5m_20cm_0.8m_0.20ms.csv \
    --light 3.20 0.70 --no-title --page-frac 1.0 --dpi 300 \
    --out-map $RO/150hz_lawnmower_no_obstacle.png
$PS $RD/data_gather_150hz_3.0x1.5m_20cm_0.8m_0.20ms_obs2.15-0.80m_30x40cm.csv \
    --light 3.20 0.50 --no-title --page-frac 1.0 --dpi 300 \
    --out-map $RO/150hz_lawnmower_with_obstacle.png
$PS $RD/data_gather_170hz_3.0x1.5m_20cm_0.8m_0.20ms.csv \
    --light 3.00 1.80 --no-title --page-frac 1.0 --dpi 300 \
    --out-map $RO/170hz_lawnmower_no_obstacle.png
$PS $RD/data_gather_170hz_3.0x1.5m_20cm_0.8m_0.20ms_obs2.15-0.80m_30x40cm.csv \
    --light 2.70 1.80 --no-title --page-frac 1.0 --dpi 300 \
    --out-map $RO/170hz_lawnmower_with_obstacle.png

echo "== Obstacle-dodging real flights (0.85 textwidth, waypoint 0) =="
OD=data/obstacle_dodging_real ; OO=figures/obstacle_dodging_real
$PS $OD/navigate_session_5x5_cells_one_waypoint_with_good_dodge.csv \
    --panels state,snr --obstacle 1.35 0.25 0.20 0.25 --waypoint 0 \
    --no-title --page-frac 0.85 --dpi 300 \
    --out-ts $OO/one_waypoint_good_dodge_state_snr.png \
    --out-map $OO/one_waypoint_good_dodge_trajectory.png
$PS $OD/navigate_session_5x5_cells_dodges_obstacle.csv \
    --panels state,snr --obstacle 1.15 0.10 0.20 0.25 --waypoint 0 \
    --no-title --page-frac 0.85 --dpi 300 \
    --out-ts $OO/one_waypoint_dodges_obstacle_state_snr.png \
    --out-map $OO/one_waypoint_dodges_obstacle_trajectory.png

echo "== Multi-beacon waypoint flights (textwidth) =="
MB=data/multi_beacon_lights_flights ; MO=figures/multi_beacon_lights_flights
$PS $MB/navigate_session_5x5_cells_gradient_on_2wps.csv \
    --panels state,snr --no-title --page-frac 1.0 --dpi 300 \
    --out-ts $MO/2_waypoint_snr_and_state.png \
    --out-map $MO/2_waypoint_flight_path.png
$PS $MB/navigate_session_5x5_cells_decent_3_wps.csv \
    --panels state,snr --no-title --page-frac 1.0 --dpi 300 \
    --out-ts $MO/3_waypoint_snr_and_state.png \
    --out-map $MO/3_waypoint_flight_path.png

echo "== Ambient-light flights (0.95 textwidth) =="
# bright = the gradient_on_2wps flight (lit room); dark = dark_no_obstacle.
AB=data/ambient_light_fligts ; AO=figures/ambient_light_flights
$PS $AB/navigate_session_5x5_cells_gradient_on_2wps.csv \
    --panels state,snr --no-title --page-frac 0.95 --dpi 300 \
    --out-ts $AO/bright_snr_plot.png \
    --out-map $AO/bright_traversal_plot.png
$PS $AB/navigate_session_5x5_cells_dark_no_obstacle.csv \
    --panels state,snr --no-title --page-frac 0.95 --dpi 300 \
    --out-ts $AO/dark_snr_plot.png \
    --out-map $AO/dark_traversal_plot.png

echo ""
echo "All figures regenerated under figures/."
