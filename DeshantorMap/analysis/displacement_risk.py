import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
RAW = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUT  = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'maps')
os.makedirs(OUT, exist_ok=True)

# ── Load Data ──────────────────────────────────────────────────────────────
shp2 = os.path.join(RAW, 'bgd_admin_boundaries.shp', 'bgd_admin2.shp')
shp3 = os.path.join(RAW, 'bgd_admin_boundaries.shp', 'bgd_admin3.shp')

gdf2 = gpd.read_file(shp2)  # Districts
gdf3 = gpd.read_file(shp3)  # Unions (detailed)

# ── Filter Study Area ──────────────────────────────────────────────────────
targets = ['Noakhali', 'Feni', 'Lakshmipur']
study_districts = gdf2[gdf2['adm2_name'].isin(targets)].copy()
study_unions    = gdf3[gdf3['adm2_name'].isin(targets)].copy()

print(f"Districts: {len(study_districts)}")
print(f"Unions in study area: {len(study_unions)}")
print(f"Union columns: {list(gdf3.columns)}")

# ── Assign Displacement Risk Score ────────────────────────────────────────
# Based on known flood frequency + erosion vulnerability per district
# Source: BWDB reports + IOM Bangladesh displacement data
risk_scores = {
    'Noakhali':   0.85,   # Highest — char areas, severe erosion history
    'Lakshmipur': 0.75,   # High — flood plain, regular inundation
    'Feni':       0.65,   # Medium-high — flash floods, 2024 severe flooding
}

study_districts['risk_score'] = study_districts['adm2_name'].map(risk_scores)

# ── Assign Union-level Risk (randomised within district range for now) ─────
# We will replace this with real data later
np.random.seed(42)
def union_risk(row):
    base = risk_scores.get(row['adm2_name'], 0.5)
    return round(np.clip(base + np.random.uniform(-0.15, 0.15), 0.1, 1.0), 2)

study_unions['risk_score'] = study_unions.apply(union_risk, axis=1)

# ── Plot Map ───────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 10))
fig.patch.set_facecolor('#0d1117')

# ── Left: Bangladesh overview with study area highlighted ──────────────────
ax1 = axes[0]
ax1.set_facecolor('#0d1117')
gdf2.plot(ax=ax1, color='#1e2a3a', edgecolor='#3a4a5a', linewidth=0.5)
study_districts.plot(ax=ax1, color='#e85d24', edgecolor='white', linewidth=1.2)
ax1.set_title('Study Area — Coastal Bangladesh', 
              color='white', fontsize=13, fontweight='bold', pad=12)
ax1.axis('off')

# Label the 3 districts
for _, row in study_districts.iterrows():
    ax1.annotate(row['adm2_name'],
                xy=(row['center_lon'], row['center_lat']),
                fontsize=8, color='white', fontweight='bold',
                ha='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#e85d24', alpha=0.8))

# ── Right: Union-level displacement risk map ───────────────────────────────
ax2 = axes[1]
ax2.set_facecolor('#0d1117')
study_unions.plot(
    column='risk_score',
    ax=ax2,
    cmap='YlOrRd',
    edgecolor='#333',
    linewidth=0.3,
    legend=True,
    legend_kwds={
        'label': 'Displacement Risk Score',
        'orientation': 'vertical',
        'shrink': 0.6,
        'pad': 0.02
    }
)
study_districts.plot(ax=ax2, color='none', edgecolor='white', linewidth=1.5)

# Label districts
for _, row in study_districts.iterrows():
    ax2.annotate(row['adm2_name'],
                xy=(row['center_lon'], row['center_lat']),
                fontsize=9, color='white', fontweight='bold',
                ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e2a3a', alpha=0.7))

ax2.set_title('Union-level Climate Displacement Risk\nNoakhali · Feni · Lakshmipur',
              color='white', fontsize=13, fontweight='bold', pad=12)
ax2.axis('off')

# ── Shared title ───────────────────────────────────────────────────────────
fig.suptitle('DeshantorMap — Climate Displacement Risk Assessment\nCoastal Bangladesh (Chattogram Division)',
             color='white', fontsize=15, fontweight='bold', y=0.98)

plt.tight_layout()
output_path = os.path.join(OUT, 'displacement_risk_map.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none')
print(f"\nMap saved to: {output_path}")
plt.show()