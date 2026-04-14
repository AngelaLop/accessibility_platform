"""
Generate QC summary figures for BID meeting presentation.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

RESULTS = Path("results")
OUT = Path("figures")
OUT.mkdir(exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────
ours = pd.read_csv(RESULTS / "qc_coordinate_summary.csv")

# Consultant data
from pathlib import Path as _P
cons_rows = []
for f in _P("data/schools/AR").glob("*/summary_issues.csv"):
    iso = f.parent.name
    df = pd.read_csv(f)
    row = {"iso": iso}
    for _, r in df.iterrows():
        issue = str(r["Issue"]).strip().lower()
        count = r["Count"]
        pct = str(r["Percentage"]).replace("%", "")
        if "missing coord" in issue:
            row["c_missing"] = int(count)
        elif "outside" in issue:
            row["c_outside"] = int(count)
        elif "state/county" in issue:
            row["c_adm"] = int(count)
        elif "address" in issue:
            row["c_dup_addr"] = int(count)
        elif "total" in issue.lower():
            row["c_total"] = int(count)
    cons_rows.append(row)
cons = pd.DataFrame(cons_rows).fillna(0)

merged = ours.merge(cons, on="iso", how="outer").fillna(0).sort_values("iso")

# =====================================================================
# FIGURE 1: QC Methodology Flow (what we did step by step)
# =====================================================================
fig1, ax1 = plt.subplots(figsize=(14, 7))
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.axis("off")
ax1.set_title("Coordinate QC Pipeline — Methodology", fontsize=16, fontweight="bold", pad=20)

boxes = [
    # (x, y, w, h, color, title, detail)
    (0.3, 8.0, 2.8, 1.4, "#4472C4", "1. Load Data",
     "CIMA files (15 countries)\n+ Raw ministry files\n+ ADM1 boundaries (OCHA)"),
    (3.6, 8.0, 2.8, 1.4, "#5B9BD5", "2. Extract Addresses",
     "id_centro + provincia +\ndepartamento + dirección\nfrom raw data per country"),
    (6.9, 8.0, 2.8, 1.4, "#70AD47", "3. Bounding Box Check",
     "Is lat/lon within country?\nDetect swapped coords\n→ OUT_OF_BOUNDS"),
    (0.3, 5.5, 2.8, 1.4, "#70AD47", "4. Spatial Join (ADM1)",
     "Point-in-polygon:\nWhich province does the\ncoordinate actually fall in?"),
    (3.6, 5.5, 2.8, 1.4, "#FFC000", "5. Name Comparison",
     "Stated province vs polygon\n+ accent normalization\n+ alias mapping → MATCH/MIS"),
    (6.9, 5.5, 2.8, 1.4, "#ED7D31", "6. Duplicate Coords",
     "Same coords, different\naddress? → Likely centroid\nor copy-pasted coordinate"),
    (2.0, 3.0, 2.8, 1.4, "#C00000", "7. Pipeline Bugs Fixed",
     "HND: wrong id column\nGUY: wrong lat column\nPRY: DMS not converted"),
    (5.2, 3.0, 2.8, 1.4, "#7030A0", "8. Gap-Fill (next)",
     "Geocode ~3,650 schools\nwith address but no coords\nvia Photon/Nominatim"),
]

for x, y, w, h, color, title, detail in boxes:
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                     facecolor=color, edgecolor="white", alpha=0.9)
    ax1.add_patch(rect)
    ax1.text(x + w/2, y + h - 0.25, title, ha="center", va="top",
             fontsize=11, fontweight="bold", color="white")
    ax1.text(x + w/2, y + h/2 - 0.15, detail, ha="center", va="center",
             fontsize=8.5, color="white", linespacing=1.3)

# Arrows
arrow_kw = dict(arrowstyle="->", color="#333", lw=1.5)
from matplotlib.patches import FancyArrowPatch
for (x1, y1), (x2, y2) in [
    ((3.1, 8.7), (3.6, 8.7)),   # 1→2
    ((6.4, 8.7), (6.9, 8.7)),   # 2→3
    ((1.7, 8.0), (1.7, 6.9)),   # 1→4 (down)
    ((3.1, 6.2), (3.6, 6.2)),   # 4→5
    ((6.4, 6.2), (6.9, 6.2)),   # 5→6
    ((3.4, 5.5), (3.4, 4.4)),   # 5→7 (down)
    ((5.2, 3.7), (5.2, 3.7)),   # already positioned
]:
    ax1.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=arrow_kw)

fig1.savefig(OUT / "qc_01_methodology.png")
print(f"  Saved: {OUT / 'qc_01_methodology.png'}")
plt.close(fig1)

# =====================================================================
# FIGURE 2: Match rates by country (our results)
# =====================================================================
fig2, ax2 = plt.subplots(figsize=(12, 5))

plot_data = ours.sort_values("match_rate_pct", ascending=True).copy()
colors = []
for r in plot_data["match_rate_pct"]:
    if r >= 98: colors.append("#70AD47")
    elif r >= 95: colors.append("#FFC000")
    elif r >= 85: colors.append("#ED7D31")
    else: colors.append("#C00000")

bars = ax2.barh(plot_data["iso"], plot_data["match_rate_pct"], color=colors, height=0.7)

# Add value labels
for bar, val in zip(bars, plot_data["match_rate_pct"]):
    ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             f"{val:.1f}%", va="center", fontsize=9)

ax2.set_xlim(0, 108)
ax2.set_xlabel("ADM1 Match Rate (%)")
ax2.set_title("Coordinate-to-Province Match Rate by Country\n(Spatial join: do reported coords fall in the stated province?)")
ax2.axvline(x=95, color="#888", linestyle="--", alpha=0.5, label="95% threshold")

# Legend
legend_patches = [
    mpatches.Patch(color="#70AD47", label="≥98% — Excellent"),
    mpatches.Patch(color="#FFC000", label="95-98% — Good"),
    mpatches.Patch(color="#ED7D31", label="85-95% — Review needed"),
    mpatches.Patch(color="#C00000", label="<85% — Critical"),
]
ax2.legend(handles=legend_patches, loc="lower right", fontsize=9)
ax2.grid(axis="x", alpha=0.3)

fig2.savefig(OUT / "qc_02_match_rates.png")
print(f"  Saved: {OUT / 'qc_02_match_rates.png'}")
plt.close(fig2)

# =====================================================================
# FIGURE 3: Comparison — Our QC vs Consultant (admin mismatch)
# =====================================================================
fig3, ax3 = plt.subplots(figsize=(12, 6))

# Only countries both checked
shared = merged[merged["total"] > 0].copy()
shared = shared.sort_values("iso")

x_pos = np.arange(len(shared))
w = 0.35

# Calculate mismatch % for both
shared["our_mis_pct"] = shared["mismatch"] / shared["with_coords"].replace(0, 1) * 100
shared["c_adm_pct"] = np.where(
    shared["total"] > 0,
    shared["c_adm"] / shared["total"].replace(0, 1) * 100,
    0
)

bars1 = ax3.bar(x_pos - w/2, shared["our_mis_pct"], w, label="Our QC (CIMA, with aliases)",
                color="#4472C4", alpha=0.85)
bars2 = ax3.bar(x_pos + w/2, shared["c_adm_pct"], w, label="Consultant (ISO_total, no aliases)",
                color="#ED7D31", alpha=0.85)

ax3.set_xticks(x_pos)
ax3.set_xticklabels(shared["iso"], fontsize=9)
ax3.set_ylabel("Admin Mismatch (%)")
ax3.set_title("Province Mismatch Rate: Our QC vs Consultant\n(Lower = better. Aliases fix false positives in MEX, GTM, PRY)")
ax3.legend(fontsize=10)
ax3.grid(axis="y", alpha=0.3)

# Annotate the big improvements
for i, row in enumerate(shared.itertuples()):
    if row.iso in ("MEX", "GTM", "PRY") and row.c_adm_pct > 0.5:
        ax3.annotate(f"Alias fix\n{row.c_adm_pct:.1f}%→{row.our_mis_pct:.1f}%",
                     xy=(i, row.c_adm_pct), xytext=(i+0.5, row.c_adm_pct + 1),
                     fontsize=7.5, ha="center", color="#C00000",
                     arrowprops=dict(arrowstyle="->", color="#C00000", lw=0.8))

fig3.savefig(OUT / "qc_03_comparison_consultant.png")
print(f"  Saved: {OUT / 'qc_03_comparison_consultant.png'}")
plt.close(fig3)

# =====================================================================
# FIGURE 4: Duplicate coordinates — DupAll vs DifAddr
# =====================================================================
fig4, ax4 = plt.subplots(figsize=(12, 6))

dup_data = ours.sort_values("iso").copy()
dup_data["dup_all_pct"] = dup_data.get("dup_coord_pct", 0)
dup_data["dup_diff_pct"] = dup_data.get("dup_diff_addr_pct", 0)

x_pos = np.arange(len(dup_data))
w = 0.35

bars1 = ax4.bar(x_pos - w/2, dup_data["dup_all_pct"], w,
                label="Same coordinates (any)", color="#5B9BD5", alpha=0.85)
bars2 = ax4.bar(x_pos + w/2, dup_data["dup_diff_pct"], w,
                label="Same coords + different address (suspicious)", color="#C00000", alpha=0.85)

ax4.set_xticks(x_pos)
ax4.set_xticklabels(dup_data["iso"], fontsize=9)
ax4.set_ylabel("% of georeferenced schools")
ax4.set_title("Duplicate Coordinates Analysis\n(Schools sharing exact same location — co-located vs suspicious)")
ax4.legend(fontsize=10)
ax4.grid(axis="y", alpha=0.3)

fig4.savefig(OUT / "qc_04_duplicate_coords.png")
print(f"  Saved: {OUT / 'qc_04_duplicate_coords.png'}")
plt.close(fig4)

# =====================================================================
# FIGURE 5: Pipeline bugs found and fixed
# =====================================================================
fig5, ax5 = plt.subplots(figsize=(12, 5))
ax5.axis("off")
ax5.set_title("Pipeline Bugs Found and Fixed in _build_cima_v2.py", fontsize=14, fontweight="bold", y=0.95)

table_data = [
    ["Country", "Bug", "Impact", "Root Cause", "Status"],
    ["HND", "id_centro = 'Alcantarillado Público'",
     "11,149 schools unmatched (100%)",
     "'id' in col matched 'residuales'\nbefore 'código_centro' (accent)", "FIXED ✓"],
    ["GUY", "Latitudes = 3, 2, 10 (integers)",
     "0% match, 303 out-of-bounds",
     "'lat' in col matched\n'staff_population' first", "FIXED ✓"],
    ["PRY", "Coords stored as DMS strings",
     "0 georeferenced in CIMA",
     "No DMS→decimal conversion +\n'º' (U+00BA) ≠ '°' (U+00B0)", "FIXED ✓"],
    ["COL", "994 schools at (0°, 0°)",
     "False out-of-bounds flags",
     "(0,0) = no-data placeholder,\nnot treated as missing", "FIXED ✓"],
]

colors_table = [["#4472C4"]*5] + [["#FFF"]*5]*4
table = ax5.table(cellText=table_data, cellLoc="center", loc="center",
                  colWidths=[0.07, 0.25, 0.22, 0.28, 0.08])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2.2)

# Style header
for j in range(5):
    cell = table[0, j]
    cell.set_facecolor("#4472C4")
    cell.set_text_props(color="white", fontweight="bold")

# Style fixed status
for i in range(1, 5):
    table[i, 4].set_text_props(color="#70AD47", fontweight="bold")
    for j in range(5):
        table[i, j].set_facecolor("#F2F2F2" if i % 2 == 0 else "white")

fig5.savefig(OUT / "qc_05_bugs_fixed.png")
print(f"  Saved: {OUT / 'qc_05_bugs_fixed.png'}")
plt.close(fig5)

# =====================================================================
# FIGURE 6: Summary numbers — what we checked
# =====================================================================
fig6, axes = plt.subplots(1, 3, figsize=(14, 4))

# Panel 1: Schools validated
total_schools = int(ours["total"].sum())
total_coords = int(ours["with_coords"].sum())
total_match = int(ours["match"].sum())
total_missing = int(ours["missing_coords"].sum())

ax = axes[0]
ax.pie([total_match, total_coords - total_match, total_missing],
       labels=["Match", "Issues", "No coords"],
       colors=["#70AD47", "#FFC000", "#C00000"],
       autopct=lambda p: f"{p:.1f}%\n({int(p*total_schools/100):,})",
       startangle=90, textprops={"fontsize": 9})
ax.set_title(f"Spatial Validation\n({total_schools:,} schools)", fontsize=11, fontweight="bold")

# Panel 2: Duplicate analysis
total_dup_all = int(ours["dup_coord_schools"].sum())
total_dup_diff = int(ours["dup_diff_addr"].sum())
total_clean = total_coords - total_dup_all

ax = axes[1]
ax.pie([total_clean, total_dup_all - total_dup_diff, total_dup_diff],
       labels=["Unique coords", "Co-located\n(same addr)", "Suspicious\n(diff addr)"],
       colors=["#70AD47", "#FFC000", "#C00000"],
       autopct=lambda p: f"{p:.1f}%\n({int(p*total_coords/100):,})",
       startangle=90, textprops={"fontsize": 9})
ax.set_title(f"Duplicate Coordinates\n({total_coords:,} georeferenced)", fontsize=11, fontweight="bold")

# Panel 3: What's next
ax = axes[2]
ax.axis("off")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
next_items = [
    ("Geocode missing coords", "~3,650 schools", "#4472C4"),
    ("Geocode DifAddr suspects", "~42,100 schools", "#ED7D31"),
    ("Fix pipeline bugs", "HND/GUY/PRY ✓ done", "#70AD47"),
    ("Countries checked", "14 of 15 (URY skip)", "#5B9BD5"),
]
ax.set_title("Status & Next Steps", fontsize=11, fontweight="bold")
for i, (label, detail, color) in enumerate(next_items):
    y = 0.85 - i * 0.22
    ax.add_patch(mpatches.FancyBboxPatch((0.05, y-0.07), 0.9, 0.16,
                 boxstyle="round,pad=0.03", facecolor=color, alpha=0.15, edgecolor=color))
    ax.text(0.1, y, f"{label}", fontsize=10, fontweight="bold", va="center")
    ax.text(0.1, y - 0.06, detail, fontsize=8.5, va="center", color="#555")

fig6.tight_layout()
fig6.savefig(OUT / "qc_06_summary.png")
print(f"  Saved: {OUT / 'qc_06_summary.png'}")
plt.close(fig6)

print("\nAll figures saved to figures/")
