"""Generate the three article figures from paired comparison CSVs."""
from __future__ import annotations
import csv, os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D

P = Path(__file__).resolve().parents[2]
A = P / "results" / "comparison"
F = P / "figures"
F.mkdir(exist_ok=True)

ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges",
    "modern_523", "modern_7924", "modern_884", "rivlin_ali_baba", "bialik_beir_haharegah",
]
NAMES = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges",
    "Brenner", "Ahad Ha-Am", "Tchernichovsky", "Rivlin — Ali Baba", "Bialik — Be-ir ha-haregah",
]
MODE_STYLE = {
    "exact": dict(color="#245b91", marker="o", linestyle="-", label="Exact"),
    "expanded": dict(color="#b65019", marker="s", linestyle="--", label="Exact + one allowed substitution"),
}
CONTROL_STYLE = {
    "local128": dict(color="#336fa0", marker="o", label="Within 128 words"),
    "regional1024": dict(color="#d08426", marker="s", label="Within up to 1,024 words"),
    "whole_corpus": dict(color="#39875b", marker="^", label="Across the same work"),
}


def read(name):
    with (A / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def save(fig, name):
    for ext, dpi in (("png", 300), ("svg", 300)):
        destination = F / f"{name}.{ext}"
        pending = F / f"{name}.pending.{ext}"
        kwargs = {"dpi": dpi, "bbox_inches": "tight"}
        if ext == "svg":
            kwargs["metadata"] = {"Date": None}
        fig.savefig(pending, **kwargs)
        os.replace(pending, destination)
    plt.close(fig)


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "svg.hashsalt": "phonological-recurrence-v1",
})

# Figure 1: distance-sensitive similarity
rows = read("distance")
fig, axes = plt.subplots(4, 3, figsize=(11, 10), sharex=True, sharey=True)
for k, (corpus, name, ax) in enumerate(zip(ORDER, NAMES, axes.flat)):
    reference_rows = None
    for mode in ("exact", "expanded"):
        style = MODE_STYLE[mode]
        rr = sorted(
            [r for r in rows if r["corpus"] == corpus and r["mode"] == mode and r["cap"] == "1024" and r["offset"] == "0" and r["phase"] == "0"],
            key=lambda r: int(r["gap"]),
        )
        reference_rows = rr
        ax.plot(
            range(len(rr)), [float(r["mean"]) for r in rr],
            color=style["color"], marker=style["marker"], linestyle=style["linestyle"],
            markersize=4, linewidth=1.6,
        )
    ax.set_title(name, fontsize=10, loc="left")
    ax.grid(axis="y", alpha=.18)
    ax.set_xticks(range(4), ["Adjacent", "64", "256", "1,024"], fontsize=8)
    if reference_rows:
        ax.text(.98, .94, f"{reference_rows[0]['blocks']} blocks; {float(reference_rows[0]['retained_fraction']):.0%} retained", transform=ax.transAxes, ha="right", va="top", fontsize=7, color="#555555")
    if k % 3 == 0:
        ax.set_ylabel("Motif-set similarity")
    if k >= 9:
        ax.set_xlabel("Gap between 64-unit windows")
fig.legend(
    handles=[Line2D([0],[0], color=s["color"], marker=s["marker"], linestyle=s["linestyle"], label=s["label"]) for s in MODE_STYLE.values()],
    loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(.5, 1.015),
)
fig.subplots_adjust(hspace=.43, wspace=.15)
save(fig, "figure1_distance")

# Figure 2: sequential density
rows = read("density")
fig, axes = plt.subplots(1, 2, figsize=(13, 7.5), sharex=True, sharey=True)
end = max(int(r["start"]) + int(r["length"]) for r in rows) / 1000
collection = None
for ax, mode in zip(axes, ("exact", "expanded")):
    polygons, values = [], []
    for k, corpus in enumerate(ORDER):
        for row in rows:
            if row["corpus"] == corpus and row["mode"] == mode:
                a = int(row["start"]) / 1000
                b = a + int(row["length"]) / 1000
                polygons.append([(a,k-.35),(b,k-.35),(b,k+.35),(a,k+.35)])
                values.append(float(row["coverage"]))
    collection = PolyCollection(polygons, array=np.array(values), cmap="viridis", clim=(0,1), edgecolors="none", rasterized=True)
    ax.add_collection(collection)
    ax.set_xlim(0, end)
    ax.set_ylim(11.65, -.65)
    ax.set_title("Exact" if mode == "exact" else "Exact + one allowed substitution", fontsize=11)
    ax.set_xlabel("Position in resolved sound stream (thousands of units)")
    for boundary in (4.5, 6.5, 9.5):
        ax.axhline(boundary, color="#dddddd", linewidth=.6)
axes[0].set_yticks(range(12), NAMES)
fig.subplots_adjust(wspace=.08, bottom=.19)
cax = fig.add_axes([.3,.075,.47,.025])
fig.colorbar(collection, cax=cax, orientation="horizontal", label="Coverage in a complete 512-unit block (R64)")
save(fig, "figure2_density")

# Figure 3: fragment-preserving rearrangement
rows = read("spatial")
fig, axes = plt.subplots(1, 2, figsize=(12, 8), sharey=True, sharex=True)
controls = ("local128", "regional1024", "whole_corpus")
for ax, mode in zip(axes, ("exact", "expanded")):
    for k, corpus in enumerate(ORDER):
        for j, control in enumerate(controls):
            row = next(r for r in rows if r["corpus"] == corpus and r["mode"] == mode and r["radius"] == "64" and r["control"] == control)
            style = CONTROL_STYLE[control]
            y = k + (j-1)*.22
            observed = float(row["observed"])
            lo = 100 * (observed - float(row["null_max"]))
            hi = 100 * (observed - float(row["null_min"]))
            ax.plot([lo,hi], [y,y], color=style["color"], linewidth=1)
            ax.scatter([100*float(row["delta"])], [y], color=style["color"], marker=style["marker"], s=28, zorder=3)
    for boundary in (4.5, 6.5, 9.5):
        ax.axhline(boundary, color="#bbbbbb", linewidth=.7)
    ax.axvline(0, color="#666666", linewidth=.8)
    ax.grid(axis="x", alpha=.15)
    ax.set_title("Exact" if mode == "exact" else "Exact + one allowed substitution", fontsize=11)
    ax.set_xlabel("Original minus shuffled coverage (percentage points)")
axes[0].set_yticks(range(12), NAMES)
axes[0].invert_yaxis()
fig.legend(
    handles=[Line2D([0],[0], color=s["color"], marker=s["marker"], linestyle="-", label=s["label"]) for s in CONTROL_STYLE.values()],
    loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(.5, 1.015),
)
fig.subplots_adjust(wspace=.1)
save(fig, "figure3_rearrangement")

print("PASS figures: PNG and SVG generated from comparison tables")
