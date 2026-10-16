# -*- coding: utf-8 -*-
import csv
import glob
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PAPER = os.path.dirname(os.path.abspath(__file__))
BDA = os.path.dirname(PAPER)
SRC = os.path.join(BDA, "web", "sumber")
OUT = os.path.join(PAPER, "figures")
os.makedirs(OUT, exist_ok=True)

INK, INK2, RULE, RULE2, PAPER = "#10140d", "#3d4738", "#cdd4c4", "#e0e5d7", "#ffffff"
D1, D2, D3, D4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
ACCENT = "#1d5c3a"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": RULE,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.facecolor": PAPER, "figure.facecolor": PAPER,
    "savefig.facecolor": PAPER, "axes.grid": True,
    "grid.color": RULE2, "grid.linewidth": 0.8, "axes.axisbelow": True,
})

SEG = {1: "PB2", 2: "PB1", 3: "PA", 4: "HA", 5: "NP", 6: "NA", 7: "M", 8: "NS"}
GENE = {1: "Polymerase basic 2", 2: "Polymerase basic 1", 3: "Polymerase acidic",
        4: "Hemagglutinin", 5: "Nucleoprotein", 6: "Neuraminidase",
        7: "Matrix", 8: "Non-structural"}


def js(p):
    return json.load(io.open(p, encoding="utf-8"))


def csvread(p):
    with io.open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


INS = js(os.path.join(SRC, "insight.json"))
MODEL = csvread(os.path.join(BDA, "models", "metrik_model.csv"))
SCALE = csvread(os.path.join(BDA, "models", "metrik_skalabilitas.csv"))
STRAT = js(os.path.join(BDA, "web", "stratifikasi.json"))

made = []


def save(fig, name, caption):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)
    made.append((name, caption))
    print("  %-30s %6.1f KB  %s" % (name, os.path.getsize(p) / 1024, caption))


def tidy(ax, xlab=None, ylab=None):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    if xlab:
        ax.set_xlabel(xlab, color=INK2, fontsize=8.5)
    if ylab:
        ax.set_ylabel(ylab, color=INK2, fontsize=8.5)


def thousands(v, p=None):
    return format(int(round(v)), ",")


def hbar(name, caption, labels, vals, color, width=7.0, fmt=None):
    n = len(labels)
    fig, ax = plt.subplots(figsize=(width, 0.34 * n + 0.9))
    y = np.arange(n)[::-1]
    ax.barh(y, vals, height=0.62, color=color)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, max(vals) * 1.24)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(thousands))
    ax.grid(axis="y", visible=False)
    for yi, v in zip(y, vals):
        ax.text(v + max(vals) * 0.012, yi, (fmt(v) if fmt else thousands(v)),
                va="center", fontsize=8.5, color=INK)
    tidy(ax)
    save(fig, name, caption)


# ── Figure 1: archive growth ─────────────────────────────────────────
r = [(x["tahun_rilis"], x["count"]) for x in INS["per_tahun_rilis"]
     if x["tahun_rilis"] and x["tahun_rilis"] >= 1990]
fig, ax = plt.subplots(figsize=(7.0, 3.1))
ax.fill_between([a for a, _ in r], [b for _, b in r], color=ACCENT, alpha=0.13)
ax.plot([a for a, _ in r], [b for _, b in r], color=ACCENT, linewidth=2.2)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(thousands))
ax.set_ylim(bottom=0)
tidy(ax, "Release year", "Sequences")
save(fig, "fig1_archive_growth.png",
     "Sequences released per year, 1990 onward")

# ── Figure 2: reporting lag ──────────────────────────────────────────
jt = [(x["tahun_koleksi"], float(x["rata"])) for x in INS["jeda_per_tahun"]
      if 1995 <= x["tahun_koleksi"] <= 2025]
fig, ax = plt.subplots(figsize=(7.0, 3.1))
ax.plot([a for a, _ in jt], [b for _, b in jt], color=ACCENT, linewidth=2.2,
        marker="o", markersize=3.5)
ax.set_ylim(bottom=0)
tidy(ax, "Collection year", "Mean lag (years)")
save(fig, "fig2_reporting_lag.png",
     "Mean collection-to-release lag by collection year")

# ── Figure 3: scalability ────────────────────────────────────────────
sp = [x for x in SCALE if x["jalur"] == "Spark ML"]
sk = [x for x in SCALE if x["jalur"] != "Spark ML"]
rows = [int(float(x["n_latih"])) for x in sp]
fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.3))
ax = axes[0]
ax.plot(rows, [float(x["detik"]) for x in sp], marker="o", color=D1,
        linewidth=2.2, label="Spark ML")
sk_rows = [int(float(x["n_latih"])) for x in sk if x["n_latih"]]
sk_sec = [float(x["detik"]) for x in sk if x["detik"]]
ax.plot(sk_rows, sk_sec, marker="o", color=D2, linewidth=2.2,
        label="scikit-learn, single node")
for i, x in enumerate(sk):
    if not x["detik"]:
        ax.plot(rows[i], 8, marker="x", markersize=10, markeredgewidth=2.4,
                color=D2, clip_on=False, zorder=5)
        ax.annotate("failed", (rows[i], 8), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=8, color=D2,
                    annotation_clip=False)
ax.set_xscale("log")
ax.set_ylim(bottom=0)
tidy(ax, "Training rows", "Wall-clock time (s)")
lg = ax.legend(frameon=False, fontsize=8.5)
for t_ in lg.get_texts():
    t_.set_color(INK)
ax = axes[1]
ax.plot(rows, [float(x["throughput_baris_per_detik"]) for x in sp],
        marker="o", color=D1, linewidth=2.2, label="Spark ML")
ax.plot(sk_rows, [float(x["throughput_baris_per_detik"]) for x in sk
                  if x["throughput_baris_per_detik"]],
        marker="o", color=D2, linewidth=2.2, label="scikit-learn, single node")
ax.set_xscale("log")
ax.set_ylim(bottom=0)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(thousands))
tidy(ax, "Training rows", "Throughput (rows/s)")
fig.tight_layout()
save(fig, "fig3_scalability.png",
     "Training time and throughput versus training-set size")

# ── Figure 4: F1 by task and algorithm ───────────────────────────────
tasks, algs = [], []
for x in MODEL:
    if x["tugas"] not in tasks:
        tasks.append(x["tugas"])
    if x["algoritma"] not in algs:
        algs.append(x["algoritma"])
TASK_EN = {t: t.split(":")[0] for t in tasks}


def get(t, a, col):
    for x in MODEL:
        if x["tugas"] == t and x["algoritma"] == a:
            return float(x[col])
    return np.nan


fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.4))
ax = axes[0]
w = 0.78 / len(algs)
xs = np.arange(len(tasks))
for i, a in enumerate(algs):
    ax.bar(xs + (i - (len(algs) - 1) / 2) * w,
           [get(t, a, "f1_makro") for t in tasks], width=w * 0.92,
           color=[D1, D2, D3][i % 3], label=a)
ax.set_xticks(xs)
ax.set_xticklabels([TASK_EN[t] for t in tasks], fontsize=9)
ax.set_ylim(0, 1.05)
ax.grid(axis="x", visible=False)
tidy(ax, None, "Macro F1")
lg = ax.legend(frameon=False, fontsize=8.3)
for t_ in lg.get_texts():
    t_.set_color(INK)
ax = axes[1]
for i, a in enumerate(algs):
    ax.bar(xs + (i - (len(algs) - 1) / 2) * w,
           [get(t, a, "detik_latih") / 60 for t in tasks], width=w * 0.92,
           color=[D1, D2, D3][i % 3], label=a)
ax.set_xticks(xs)
ax.set_xticklabels([TASK_EN[t] for t in tasks], fontsize=9)
ax.grid(axis="x", visible=False)
tidy(ax, None, "Training time (min)")
fig.tight_layout()
save(fig, "fig4_model_comparison.png",
     "Macro F1 and training time by task and algorithm")

# ── Figure 5: similarity edges per segment ───────────────────────────
gs = INS["graf_per_segmen"]
hbar("fig5_edges_per_segment.png",
     "Similarity edges per genome segment",
     ["%d %s" % (x["segmen"], SEG[x["segmen"]]) for x in gs],
     [x["tepi"] for x in gs], ACCENT)

# ── Figure 6: host enrichment ────────────────────────────────────────
EN = {"babi": "Swine (Sus)", "unggas": "Avian", "manusia": "Human"}
rows_ = [x for x in STRAT["kasar"] if x["kelas_inang"] in EN]
rows_.sort(key=lambda x: -x["pengayaan"])
fig, ax = plt.subplots(figsize=(7.0, 3.2))
xs = np.arange(len(rows_))
ax.bar(xs - 0.19, [x["pangsa_pop"] for x in rows_], width=0.36, color=D1,
       label="Share of scored population")
ax.bar(xs + 0.19, [x["pangsa_kand"] for x in rows_], width=0.36, color=D2,
       label="Share of flagged candidates")
for i, x in enumerate(rows_):
    ax.text(i, max(x["pangsa_pop"], x["pangsa_kand"]) + 2.2,
            "%.2f\u00d7" % x["pengayaan"], ha="center", fontsize=9,
            color=INK, fontweight="bold")
ax.set_xticks(xs)
ax.set_xticklabels([EN[x["kelas_inang"]] for x in rows_], fontsize=9.5)
ax.set_ylim(0, 82)
ax.grid(axis="x", visible=False)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda v, p: "%d%%" % v))
ax.set_yticks([0, 10, 20, 30, 40, 50, 60])
tidy(ax, None, "Percentage")
lg = ax.legend(frameon=False, fontsize=8.5, loc="upper center",
               ncol=2, bbox_to_anchor=(0.5, 1.02))
for t_ in lg.get_texts():
    t_.set_color(INK)
save(fig, "fig6_host_enrichment.png",
     "Host composition of the scored population versus flagged candidates, "
     "with enrichment ratios")

io.open(os.path.join(OUT, "FIGURES.txt"), "w", encoding="utf-8").write(
    "Figures for the manuscript\n" + "=" * 46 + "\n\n"
    + "\n".join("%-30s %s" % (n, c) for n, c in made) + "\n")
print("\n%d figures written to %s" % (len(made), OUT))
