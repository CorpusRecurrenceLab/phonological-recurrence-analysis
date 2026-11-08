"""Recreate overview figures from frozen repository tables.

Usage, at the repository root:
    python src/analysis/overview_figures.py --out figures/overview

Inputs are immutable published tables under results/. No manual data editing.
Outputs: Figure_1.tif, Figure_2.tif, Figure_3.tif (RGB, 600 dpi).
"""
from __future__ import annotations

import argparse
import io
import os
import tempfile
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

REPO = Path(__file__).resolve().parents[2]  # when installed as src/analysis/submission_figures.py
BOOKS = REPO / 'results/tanakh/primary/source_books_39.csv'
HOSTS = REPO / 'results/tanakh/word_control/different_surface_coverage_summary.csv'
COMPARISON = REPO / 'results/comparison/tanakh_and_modern_44_work_descriptive.csv'
MODERN_NAMES = {
    'modern_523': 'Brenner',
    'modern_7924': 'Ahad Ha-Am',
    'modern_884': 'Tchernichovsky',
    'bialik_beir_haharegah': 'Bialik',
    'rivlin_ali_baba': 'Rivlin',
}

def save(fig: plt.Figure, path: Path) -> None:
    """Write a 600-dpi RGB/LZW TIFF without reopening or overwriting an open TIFF.

    Pillow reads the Matplotlib rendering from memory; a temporary destination
    is fully closed before os.replace() publishes the completed TIFF. This avoids
    Windows sharing/locking failures from reading and writing the same path.
    """
    buffer = io.BytesIO()
    temp_path = None
    try:
        fig.savefig(buffer, dpi=600, format='png', facecolor='white')
        plt.close(fig)
        buffer.seek(0)
        with Image.open(buffer) as image:
            rgb = image.convert('RGB')
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, filename = tempfile.mkstemp(prefix='.figure_', suffix='.tif', dir=path.parent)
        os.close(fd)
        temp_path = Path(filename)
        rgb.save(temp_path, format='TIFF', compression='tiff_lzw', dpi=(600, 600))
        rgb.close()
        os.replace(temp_path, path)
        temp_path = None
    finally:
        plt.close(fig)
        buffer.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=REPO/'figures/overview')
    args=p.parse_args()
    out=args.out.resolve();out.mkdir(parents=True, exist_ok=True)
    def rows(path):
        with path.open(newline='',encoding='utf-8-sig') as stream:
            return list(csv.DictReader(stream))
    a=rows(BOOKS); b=rows(HOSTS); c=rows(COMPARISON)
    if not (len(a)==39 and len(b)==39 and len(c)==88):
        raise ValueError('Unexpected frozen table dimensions')
    if {r['source_book'] for r in a}!={r['book'] for r in b}:
        raise ValueError('Source book IDs disagree')
    if sum(r['mode']=='exact' for r in c)!=44:
        raise ValueError('Missing exact-mode comparison data')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
        'axes.titlesize':14, 'axes.labelsize':12, 'xtick.labelsize':9, 'ytick.labelsize':10,
        'svg.fonttype':'none'})
    x=range(39)
    fig,ax=plt.subplots(figsize=(14.2,7.6),constrained_layout=True)
    ax.plot(x,[float(r['coverage_exact']) for r in a], color='black', marker='o',markersize=3.5,linewidth=1.3,label='Exact')
    ax.plot(x,[float(r['coverage_expanded']) for r in a],color='0.50',marker='s',markersize=3.5,linewidth=1.2,label='Restricted expanded')
    ax.set_xticks(list(x),[r['source_book'] for r in a],rotation=64,ha='right')
    ax.set_xlim(-.5,38.5);ax.set_ylim(.20,.60)
    ax.set_ylabel('Fraction of sound positions covered')
    ax.set_title('Mixed-triplet coverage across 39 Tanakh source books')
    ax.grid(axis='y',color='.88',lw=.65);ax.legend(frameon=False,loc='upper right')
    save(fig,out/'Figure_1.tif')
    z={r['book']:r for r in b}
    ordered=[z[r['source_book']] for r in a]
    fig,ax=plt.subplots(figsize=(14.2,7.6),constrained_layout=True)
    ax.plot(x,[float(r['baseline_coverage_R64']) for r in ordered],color='black',marker='o',lw=1.2,ms=3.4,label='All qualifying matches')
    ax.plot(x,[float(r['different_surface_coverage_R64']) for r in ordered],color='0.5',marker='s',lw=1.2,ms=3.4,label='Different complete wordform hosts')
    ax.set_xticks(list(x),[r['source_book'] for r in a],rotation=64,ha='right')
    ax.set_xlim(-.5,38.5);ax.set_ylim(.12,.55)
    ax.set_ylabel('Fraction of sound positions covered')
    ax.set_title('Exact coverage with and without identical wordform hosts')
    ax.grid(axis='y',color='.88',lw=.65);ax.legend(frameon=False,loc='upper right')
    save(fig,out/'Figure_2.tif')
    exact=[r for r in c if r['mode']=='exact']
    heb=[r for r in exact if r['group']=='tanakh_source_book']
    mod=[r for r in exact if r['group']=='modern_comparison']
    if len(heb)!=39 or len(mod)!=5:
        raise ValueError('Expected 39 biblical and five modern works')
    fig,ax=plt.subplots(figsize=(10.7,7.4),constrained_layout=True)
    ax.scatter([float(r['coverage_R64']) for r in heb],[float(r['spatial_local128_R64']) for r in heb],facecolors='white',edgecolors='0.2',s=70,label='Tanakh source books',zorder=3)
    ax.scatter([float(r['coverage_R64']) for r in mod],[float(r['spatial_local128_R64']) for r in mod],marker='s',color='black',s=75,label='Modern comparison works',zorder=4)
    displacements={
        'modern_523':(6,8),
        'modern_7924':(8,8),
        'modern_884':(9,-17),
        'bialik_beir_haharegah':(6,8),
        'rivlin_ali_baba':(8,9),
    }
    for r in mod:
        label=MODERN_NAMES.get(r['corpus'],r['corpus'])
        offset=displacements.get(r['corpus'],(5,5))
        ax.annotate(label,(float(r['coverage_R64']),float(r['spatial_local128_R64'])),xytext=offset,textcoords='offset points',fontsize=10,ha='left',va='center')
    ax.set_xlim(.275,.49);ax.set_ylim(-.002,.079)
    ax.grid(color='.89',lw=.7)
    ax.set_xlabel('Exact coverage, radius 64')
    ax.set_ylabel('Observed minus rearranged local coverage')
    ax.set_title('Descriptive overlap between biblical and modern works')
    ax.legend(frameon=False,loc='upper right')
    save(fig,out/'Figure_3.tif')
    print('Figures written:',out)
    print('Input rows:',len(a),len(b),len(c))

if __name__=='__main__':main()
