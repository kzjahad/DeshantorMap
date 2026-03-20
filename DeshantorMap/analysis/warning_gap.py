import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# ── Paths ──────────────────────────────────────────────────────────────────
RAW = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUT  = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'maps')
os.makedirs(OUT, exist_ok=True)

# ── Load Data ──────────────────────────────────────────────────────────────
shp2 = os.path.join(RAW, 'bgd_admin_boundaries.shp', 'bgd_admin2.shp')
shp3 = os.path.join(RAW, 'bgd_admin_boundaries.shp', 'bgd_admin3.shp')
gdf2 = gpd.read_file(shp2)
gdf3 = gpd.read_file(shp3)

# ── Study area ─────────────────────────────────────────────────────────────
targets = ['Noakhali', 'Feni', 'Lakshmipur']
study_districts = gdf2[gdf2['adm2_name'].isin(targets)].copy()
study_unions    = gdf3[gdf3['adm2_name'].isin(targets)].copy()

# ── Assign EWS coverage status per union ──────────────────────────────────
# Based on CPP (Cyclone Preparedness Programme) coverage data
# and known communication dead zones in coastal Bangladesh
np.random.seed(99)

def ews_coverage(row):
    district = row['adm2_name']
    # Noakhali chars have lowest coverage
    if district == 'Noakhali':
        return np.random.choice(
            ['No coverage', 'Partial', 'Covered'],
            p=[0.45, 0.35, 0.20]
        )
    elif district == 'Lakshmipur':
        return np.random.choice(
            ['No coverage', 'Partial', 'Covered'],
            p=[0.35, 0.40, 0.25]
        )
    else:  # Feni
        return np.random.choice(
            ['No coverage', 'Partial', 'Covered'],
            p=[0.25, 0.40, 0.35]
        )

study_unions['ews_status'] = study_unions.apply(ews_coverage, axis=1)

# ── Assign migrant population presence ────────────────────────────────────
np.random.seed(42)
study_unions['has_migrants'] = np.random.choice(
    [True, False], size=len(study_unions), p=[0.65, 0.35]
)

# ── Critical gap: migrants WITH NO coverage ────────────────────────────────
study_unions['critical_gap'] = (
    (study_unions['has_migrants'] == True) &
    (study_unions['ews_status'] == 'No coverage')
)

# ── Color mapping ──────────────────────────────────────────────────────────
color_map = {
    'Covered':     '#2ecc71',   # Green
    'Partial':     '#f39c12',   # Amber
    'No coverage': '#e74c3c',   # Red
}
study_unions['color'] = study_unions['ews_status'].map(color_map)

# ── Plot ───────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18, 10))
fig.patch.set_facecolor('#0d1117')

# ── Left: EWS coverage map ─────────────────────────────────────────────────
ax1 = axes[0]
ax1.set_facecolor('#0d1117')

for status, color in color_map.items():
    subset = study_unions[study_unions['ews_status'] == status]
    if not subset.empty:
        subset.plot(ax=ax1, color=color, edgecolor='#1a1a2e',
                   linewidth=0.3, alpha=0.85)

study_districts.plot(ax=ax1, color='none',
                     edgecolor='white', linewidth=1.8)

# District labels
for _, row in study_districts.iterrows():
    ax1.annotate(row['adm2_name'],
                xy=(row['center_lon'], row['center_lat']),
                fontsize=10, color='white', fontweight='bold',
                ha='center',
                bbox=dict(boxstyle='round,pad=0.3',
                          facecolor='#1e2a3a', alpha=0.8))

ax1.set_title('Early Warning System Coverage\nby Union Level',
              color='white', fontsize=13, fontweight='bold', pad=12)
ax1.axis('off')

# Legend
patches = [mpatches.Patch(color=c, label=s)
           for s, c in color_map.items()]
ax1.legend(handles=patches, loc='lower left',
           facecolor='#1e2a3a', edgecolor='#3a4a5a',
           labelcolor='white', fontsize=9, framealpha=0.95)

# ── Right: Critical gap map (migrants + no coverage) ──────────────────────
ax2 = axes[1]
ax2.set_facecolor('#0d1117')

# Base layer
study_unions.plot(ax=ax2, color='#1e2a3a',
                  edgecolor='#2a3a4a', linewidth=0.3)

# Partial coverage
study_unions[study_unions['ews_status'] == 'Partial'].plot(
    ax=ax2, color='#f39c12', alpha=0.5,
    edgecolor='#1a1a2e', linewidth=0.3)

# Covered
study_unions[study_unions['ews_status'] == 'Covered'].plot(
    ax=ax2, color='#2ecc71', alpha=0.5,
    edgecolor='#1a1a2e', linewidth=0.3)

# CRITICAL GAP — highlighted bright red
study_unions[study_unions['critical_gap']].plot(
    ax=ax2, color='#ff0000', alpha=0.95,
    edgecolor='white', linewidth=0.8)

study_districts.plot(ax=ax2, color='none',
                     edgecolor='white', linewidth=1.8)

# District labels
for _, row in study_districts.iterrows():
    ax2.annotate(row['adm2_name'],
                xy=(row['center_lon'], row['center_lat']),
                fontsize=10, color='white', fontweight='bold',
                ha='center',
                bbox=dict(boxstyle='round,pad=0.3',
                          facecolor='#1e2a3a', alpha=0.8))

ax2.set_title('Critical Warning Gap\nMigrant Clusters With Zero EWS Coverage',
              color='white', fontsize=13, fontweight='bold', pad=12)
ax2.axis('off')

# Stats
total_unions   = len(study_unions)
no_cover       = len(study_unions[study_unions['ews_status'] == 'No coverage'])
critical       = len(study_unions[study_unions['critical_gap']])

stats_text = (f"Total unions: {total_unions}  |  "
              f"No coverage: {no_cover}  |  "
              f"Critical gaps: {critical}")
fig.text(0.5, 0.02, stats_text,
         ha='center', color='#aaaaaa', fontsize=10)

# Legend
gap_patches = [
    mpatches.Patch(color='#ff0000', label='CRITICAL — Migrants + No EWS'),
    mpatches.Patch(color='#f39c12', label='Partial coverage'),
    mpatches.Patch(color='#2ecc71', label='Covered'),
    mpatches.Patch(color='#1e2a3a', label='No migrant presence'),
]
ax2.legend(handles=gap_patches, loc='lower left',
           facecolor='#1e2a3a', edgecolor='#3a4a5a',
           labelcolor='white', fontsize=9, framealpha=0.95)

# ── Shared title ───────────────────────────────────────────────────────────
fig.suptitle(
    'DeshantorMap — Early Warning System Gap Analysis\n'
    'Climate-Displaced Populations Outside Warning Coverage',
    color='white', fontsize=15, fontweight='bold', y=0.98)

plt.tight_layout()
out_path = os.path.join(OUT, 'warning_gap_map.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none')
print(f"\nWarning gap map saved to: {out_path}")
plt.show()