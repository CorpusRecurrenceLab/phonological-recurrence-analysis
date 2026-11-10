
"""Recreate overview figures from frozen repository tables.

Usage, at the repository root:
    python src/analysis/overview_figures.py --out figures/overview

Inputs are immutable published tables under results/. No manual data editing.
Outputs: Figure_1.tif, Figure_2.tif, Figure_3.tif (RGB, 600 dpi).
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
BOOKS = REPO / 'results/tanakh/primary/source_books_39.csv'
HOSTS = REPO / 'results/tanakh/word_control/different_surface_coverage_summary.csv'
COMPARISON = REPO / 'results/comparison/tanakh_and_modern_44_work_descriptive.csv'

MODERN_ORDER = [
    'modern_523',
    'modern_7924',
    'modern_884',
    'bialik_beir_haharegah',
    'rivlin_ali_baba',
]
MODERN_NAMES = {
    'modern_523': 'Brenner',
    'modern_7924': 'Ahad Ha-Am',
    'modern_884': 'Tchernichovsky',
    'bialik_beir_haharegah': 'Bialik',
    'rivlin_ali_baba': 'Rivlin',
}
SELECTED_BIBLICAL_LABELS = [
    'Genesis', 'Leviticus', 'Psalms', 'Job', 'Obadiah', 'Esther', 'Haggai', 'Proverbs'
]

BLUE = '#1f4e79'
ORANGE = '#c8742a'
GRAY = '#666666'
LIGHTGRAY = '#bcbcbc'


def save(fig: plt.Figure, path: Path) -> None:
    """Render in memory, then atomically replace a closed TIFF (Windows safe)."""
    image_bytes = io.BytesIO()
    try:
        # A PNG memory buffer avoids opening and re-saving an active TIFF.
        fig.savefig(image_bytes, dpi=600, format='png', facecolor='white', bbox_inches='tight')
    finally:
        plt.close(fig)
    image_bytes.seek(0)
    fd, temporary_name = tempfile.mkstemp(prefix=path.stem + '_', suffix='.tif', dir=path.parent)
    os.close(fd)
    try:
        with Image.open(image_bytes) as im:
            rgb = im.convert('RGB')
            rgb.save(temporary_name, compression='tiff_lzw', dpi=(600, 600))
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def load_rows(path: Path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def set_common_style() -> None:
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'font.size': 12,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'svg.fonttype': 'none',
    })


def figure_1(source_rows, comparison_rows, out: Path) -> None:
    x = np.arange(len(source_rows))
    fig = plt.figure(figsize=(9.5, 7.4), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[4.7, 1.8])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    cov_exact = np.array([float(r['coverage_exact']) for r in source_rows])
    cov_expanded = np.array([float(r['coverage_expanded']) for r in source_rows])

    ax1.plot(x, cov_exact, color=BLUE, marker='o', markersize=3.6, linewidth=1.35, label='Exact')
    ax1.plot(x, cov_expanded, color=ORANGE, marker='s', markersize=3.3, linewidth=1.2, label='Restricted expanded')
    ax1.set_xticks(x)
    ax1.set_xticklabels([r['source_book'] for r in source_rows], rotation=64, ha='right')
    ax1.set_xlim(-0.5, len(source_rows)-0.5)
    ax1.set_ylim(0.20, 0.60)
    ax1.set_ylabel('Covered fraction of sound positions')
    ax1.set_xlabel('Tanakh source books')
    ax1.grid(axis='y', color='#e6e6e6', linewidth=0.7)
    ax1.legend(frameon=False, loc='upper right')

    exact = [r for r in comparison_rows if r['mode'] == 'exact' and r['group'] == 'modern_comparison']
    expanded = [r for r in comparison_rows if r['mode'] == 'expanded' and r['group'] == 'modern_comparison']
    exact_map = {r['corpus']: r for r in exact}
    expanded_map = {r['corpus']: r for r in expanded}
    y = np.arange(len(MODERN_ORDER))
    ex_vals = np.array([float(exact_map[k]['coverage_R64']) for k in MODERN_ORDER])
    ex2_vals = np.array([float(expanded_map[k]['coverage_R64']) for k in MODERN_ORDER])
    labels = [MODERN_NAMES[k] for k in MODERN_ORDER]
    for yy, a, b in zip(y, ex_vals, ex2_vals):
        ax2.plot([a, b], [yy, yy], color=LIGHTGRAY, linewidth=1.3, zorder=1)
    ax2.scatter(ex_vals, y, color=BLUE, s=34, marker='o', zorder=3, label='Exact')
    ax2.scatter(ex2_vals, y, color=ORANGE, s=32, marker='s', zorder=3, label='Restricted expanded')
    ax2.set_yticks(y)
    ax2.set_yticklabels(labels)
    ax2.invert_yaxis()
    xmin = min(ex_vals.min(), ex2_vals.min()) - 0.015
    xmax = max(ex_vals.max(), ex2_vals.max()) + 0.015
    ax2.set_xlim(max(0.20, xmin), min(0.60, xmax))
    ax2.set_xlabel('Coverage')
    ax2.grid(axis='x', color='#e6e6e6', linewidth=0.7)
    # Exact/expanded marker meanings are already given by the left-panel legend;
    # a duplicate legend here obscured Rivlin's low row and resembled data.

    save(fig, out / 'Figure_1.tif')


def figure_2(source_rows, host_rows, out: Path) -> None:
    z = {r['book']: r for r in host_rows}
    ordered = [z[r['source_book']] for r in source_rows]
    x = np.arange(len(ordered))
    baseline = np.array([float(r['baseline_coverage_R64']) for r in ordered])
    filtered = np.array([float(r['different_surface_coverage_R64']) for r in ordered])
    reduction = baseline - filtered

    fig = plt.figure(figsize=(9.5, 8.2), constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[3.2, 1.5])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)

    for xx, a, b in zip(x, baseline, filtered):
        ax1.plot([xx, xx], [b, a], color=LIGHTGRAY, linewidth=1.0, zorder=1)
    ax1.plot(x, baseline, color=BLUE, marker='o', linewidth=1.2, markersize=3.5, label='All qualifying matches')
    ax1.plot(x, filtered, color=ORANGE, marker='s', linewidth=1.15, markersize=3.2, label='Different complete wordform hosts')
    ax1.set_ylim(0.12, 0.55)
    ax1.set_ylabel('Covered fraction of sound positions')
    ax1.grid(axis='y', color='#e6e6e6', linewidth=0.7)
    ax1.legend(frameon=False, loc='upper right')
    ax1.tick_params(axis='x', which='both', bottom=False, labelbottom=False)

    ax2.bar(x, reduction, width=0.74, color=GRAY)
    ax2.set_ylabel('Reduction')
    ax2.set_xlabel('Tanakh source books')
    ax2.set_xticks(x)
    ax2.set_xticklabels([r['source_book'] for r in source_rows], rotation=64, ha='right')
    ax2.grid(axis='y', color='#e6e6e6', linewidth=0.7)
    ax2.set_ylim(0, max(reduction) * 1.25)

    save(fig, out / 'Figure_2.tif')


def figure_3(comparison_rows, out: Path) -> None:
    exact = [r for r in comparison_rows if r['mode'] == 'exact']
    heb = [r for r in exact if r['group'] == 'tanakh_source_book']
    mod = [r for r in exact if r['group'] == 'modern_comparison']
    if len(heb) != 39 or len(mod) != 5:
        raise ValueError('Expected 39 biblical and five modern works')

    fig, ax = plt.subplots(figsize=(7.4, 6.4), constrained_layout=True)
    hx = np.array([float(r['coverage_R64']) for r in heb])
    hy = np.array([float(r['spatial_local128_R64']) for r in heb])
    ax.scatter(hx, hy, facecolors='white', edgecolors=BLUE, linewidths=1.1, s=58, label='Tanakh source books', zorder=2)

    selected = {r['corpus']: r for r in heb if r['corpus'] in SELECTED_BIBLICAL_LABELS}
    offsets = {
        'Genesis': (8, 8), 'Leviticus': (8, -14), 'Psalms': (-43, -26), 'Job': (-35, 23),
        'Obadiah': (8, 9), 'Esther': (11, -16), 'Haggai': (-45, 16), 'Proverbs': (8, 9),
    }
    for key in SELECTED_BIBLICAL_LABELS:
        if key not in selected:
            continue
        r = selected[key]
        # Leader lines identify the crowded Job/Habakkuk and Psalms/Hosea points.
        pointer = {'arrowstyle': '-', 'color': BLUE, 'lw': 0.7, 'shrinkA': 2,
                   'shrinkB': 3} if key in {'Job', 'Psalms'} else None
        ax.annotate(key, (float(r['coverage_R64']), float(r['spatial_local128_R64'])),
                    xytext=offsets.get(key, (8, 8)), textcoords='offset points',
                    fontsize=9.2, color=BLUE, arrowprops=pointer)

    modern_map = {r['corpus']: r for r in mod}
    mx = np.array([float(modern_map[k]['coverage_R64']) for k in MODERN_ORDER])
    my = np.array([float(modern_map[k]['spatial_local128_R64']) for k in MODERN_ORDER])
    ax.scatter(mx, my, marker='s', color=ORANGE, edgecolors=ORANGE, s=66, label='Modern comparison works', zorder=3)
    modern_offsets = {
        'modern_523': (8, 8),
        'modern_7924': (8, 8),
        'modern_884': (8, -14),
        'bialik_beir_haharegah': (8, 8),
        'rivlin_ali_baba': (8, 8),
    }
    for key in MODERN_ORDER:
        r = modern_map[key]
        ax.annotate(MODERN_NAMES[key], (float(r['coverage_R64']), float(r['spatial_local128_R64'])),
                    xytext=modern_offsets.get(key, (8, 8)), textcoords='offset points',
                    fontsize=9.2, color=ORANGE)

    ax.set_xlim(0.27, 0.49)
    ax.set_ylim(-0.002, 0.079)
    ax.set_xlabel('Exact coverage, radius 64')
    ax.set_ylabel('Observed minus rearranged local coverage')
    ax.grid(color='#e6e6e6', linewidth=0.7)
    ax.legend(frameon=False, loc='upper right')

    save(fig, out / 'Figure_3.tif')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=REPO / 'figures/overview')
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    source_rows = load_rows(BOOKS)
    host_rows = load_rows(HOSTS)
    comparison_rows = load_rows(COMPARISON)

    if not (len(source_rows) == 39 and len(host_rows) == 39 and len(comparison_rows) == 88):
        raise ValueError('Unexpected frozen table dimensions')
    if {r['source_book'] for r in source_rows} != {r['book'] for r in host_rows}:
        raise ValueError('Source book IDs disagree')
    if sum(r['mode'] == 'exact' for r in comparison_rows) != 44:
        raise ValueError('Missing exact-mode comparison data')

    set_common_style()
    figure_1(source_rows, comparison_rows, out)
    figure_2(source_rows, host_rows, out)
    figure_3(comparison_rows, out)
    print('Figures written:', out)
    print('Input rows:', len(source_rows), len(host_rows), len(comparison_rows))


if __name__ == '__main__':
    main()
