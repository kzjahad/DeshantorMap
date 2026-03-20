import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as FancyArrowPatch
import numpy as np
import os
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D

# ── Paths ──────────────────────────────────────────────────────────────────
RAW = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUT  = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'maps')
os.makedirs(OUT, exist_ok=True)

# ── Load Bangladesh district map ───────────────────────────────────────────
shp2 = os.path.join(RAW, 'bgd_admin_boundaries.shp', 'bgd_admin2.shp')
gdf  = gpd.read_file(shp2)

# ── Define origin & destination districts ─────────────────────────────────
origins = ['Noakhali', 'Feni', 'Lakshmipur']
destinations = ['Dhaka', 'Chattogram', 'Narsingdi', 'Munshiganj']

origin_gdf = gdf[gdf['adm2_name'].isin(origins)].copy()
dest_gdf   = gdf[gdf['adm2_name'].isin(destinations)].copy()

# ── Migration flow data (IOM/BBS estimates) ────────────────────────────────
# Format: (origin, destination, estimated_migrants)
flows = [
    ('Noakhali',   'Chattogram',  85000),
    ('Noakhali',   'Dhaka',      120000),
    ('Noakhali',   'Narsingdi',   25000),
    ('Feni',       'Chattogram',  70000),
    ('Feni',       'Dhaka',       95000),
    ('Feni',       'Munshiganj',  18000),
    ('Lakshmipur', 'Dhaka',       80000),
    ('Lakshmipur', 'Chattogram',  45000),
    ('Lakshmipur', 'Narsingdi',   22000),
]

# ── Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(14, 16))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

# Draw all districts (background)
gdf.plot(ax=ax, color='#1a2332', edgecolor='#2a3a4a', linewidth=0.4)

# Highlight destinations
dest_gdf.plot(ax=ax, color='#1a3a5c', edgecolor='#4a8abf', linewidth=1.2)

# Highlight origins
origin_gdf.plot(ax=ax, color='#5c1a1a', edgecolor='#e85d24', linewidth=1.5)

# ── Draw migration flow arrows ─────────────────────────────────────────────
max_flow = max(f[2] for f in flows)

for origin_name, dest_name, count in flows:
    o_row = gdf[gdf['adm2_name'] == origin_name]
    d_row = gdf[gdf['adm2_name'] == dest_name]

    if o_row.empty or d_row.empty:
        continue

    ox = float(o_row['center_lon'].values[0])
    oy = float(o_row['center_lat'].values[0])
    dx = float(d_row['center_lon'].values[0])
    dy = float(d_row['center_lat'].values[0])

    # Scale arrow width by migration volume
    width = 0.5 + (count / max_flow) * 3.5
    alpha = 0.4 + (count / max_flow) * 0.5

    ax.annotate(
        '',
        xy=(dx, dy),
        xytext=(ox, oy),
        arrowprops=dict(
            arrowstyle='-|>',
            color='#f5a623',
            lw=width,
            alpha=alpha,
            connectionstyle='arc3,rad=0.2'
        )
    )

    # Label midpoint with migrant count
    mid_x = (ox + dx) / 2 + 0.15
    mid_y = (oy + dy) / 2
    ax.text(mid_x, mid_y,
            f'{count//1000}k',
            fontsize=7, color='#f5a623',
            alpha=0.85, fontweight='bold')

# ── Label origin districts ─────────────────────────────────────────────────
for _, row in origin_gdf.iterrows():
    ax.annotate(
        row['adm2_name'],
        xy=(row['center_lon'], row['center_lat']),
        fontsize=9, color='white', fontweight='bold',
        ha='center',
        bbox=dict(boxstyle='round,pad=0.3',
                  facecolor='#e85d24', alpha=0.9, edgecolor='none')
    )

# ── Label destination districts ────────────────────────────────────────────
for _, row in dest_gdf.iterrows():
    ax.annotate(
        row['adm2_name'],
        xy=(row['center_lon'], row['center_lat']),
        fontsize=9, color='white', fontweight='bold',
        ha='center',
        bbox=dict(boxstyle='round,pad=0.3',
                  facecolor='#1a5c8a', alpha=0.9, edgecolor='none')
    )

# ── Legend ─────────────────────────────────────────────────────────────────
legend_elements = [
    Line2D([0], [0], marker='s', color='w',
           markerfacecolor='#e85d24', markersize=12,
           label='Origin — Climate displacement zone'),
    Line2D([0], [0], marker='s', color='w',
           markerfacecolor='#1a5c8a', markersize=12,
           label='Destination — Urban migration hotspot'),
    Line2D([0], [0], color='#f5a623', linewidth=2.5,
           label='Migration flow (arrow width = volume)'),
]
ax.legend(handles=legend_elements,
          loc='lower left',
          facecolor='#1e2a3a',
          edgecolor='#3a4a5a',
          labelcolor='white',
          fontsize=9,
          framealpha=0.95)

# ── Title & stats ──────────────────────────────────────────────────────────
total = sum(f[2] for f in flows)
ax.set_title(
    f'DeshantorMap — Climate Migration Flow\n'
    f'Coastal Bangladesh → Urban Centres  |  Est. {total:,} displaced persons tracked',
    color='white', fontsize=13, fontweight='bold', pad=15
)
ax.axis('off')

plt.tight_layout()
out_path = os.path.join(OUT, 'migration_flow_map.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none')
print(f"Migration flow map saved to: {out_path}")
plt.show()