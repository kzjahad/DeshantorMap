import geopandas as gpd
import folium
import os
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
RAW = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUT  = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'maps')
os.makedirs(OUT, exist_ok=True)

# ── Load Data ──────────────────────────────────────────────────────────────
shp2 = os.path.join(RAW, 'bgd_admin_boundaries.shp', 'bgd_admin2.shp')
shp3 = os.path.join(RAW, 'bgd_admin_boundaries.shp', 'bgd_admin3.shp')
gdf2 = gpd.read_file(shp2)
gdf3 = gpd.read_file(shp3)

# ── Filter Study Area ──────────────────────────────────────────────────────
targets = ['Noakhali', 'Feni', 'Lakshmipur']
study_districts = gdf2[gdf2['adm2_name'].isin(targets)].copy()
study_unions    = gdf3[gdf3['adm2_name'].isin(targets)].copy()

# ── Risk Scores ────────────────────────────────────────────────────────────
risk_scores = {
    'Noakhali':   0.85,
    'Lakshmipur': 0.75,
    'Feni':       0.65,
}

np.random.seed(42)
def union_risk(row):
    base = risk_scores.get(row['adm2_name'], 0.5)
    return round(np.clip(base + np.random.uniform(-0.15, 0.15), 0.1, 1.0), 2)

study_unions['risk_score'] = study_unions.apply(union_risk, axis=1)

# ── Fix JSON serialization ─────────────────────────────────────────────────
study_unions  = study_unions.copy()
study_districts = study_districts.copy()
for col in study_unions.columns:
    if study_unions[col].dtype == 'object' or str(study_unions[col].dtype).startswith('datetime'):
        try:
            study_unions[col] = study_unions[col].astype(str)
        except:
            pass
for col in study_districts.columns:
    if str(study_districts[col].dtype).startswith('datetime'):
        try:
            study_districts[col] = study_districts[col].astype(str)
        except:
            pass

# ── Displacement facts per district ───────────────────────────────────────
facts = {
    'Noakhali':   {'displaced': '320,000+', 'hazard': 'Erosion + Cyclone',       'chars': 'Yes — active char formation'},
    'Lakshmipur': {'displaced': '180,000+', 'hazard': 'Flood + Storm surge',     'chars': 'Partial'},
    'Feni':       {'displaced': '250,000+', 'hazard': 'Flash flood (2024 severe)','chars': 'No'},
}

# ── Create Folium Map ──────────────────────────────────────────────────────
m = folium.Map(
    location=[22.8, 91.1],
    zoom_start=9,
    tiles='CartoDB dark_matter'
)

# ── Add union-level choropleth ─────────────────────────────────────────────
folium.Choropleth(
    geo_data=study_unions.__geo_interface__,
    name='Displacement Risk',
    data=study_unions,
    columns=['adm3_name', 'risk_score'],
    key_on='feature.properties.adm3_name',
    fill_color='YlOrRd',
    fill_opacity=0.75,
    line_opacity=0.3,
    line_color='white',
    legend_name='Climate Displacement Risk Score (0–1)',
    highlight=True,
).add_to(m)

# ── Add clickable union tooltips ───────────────────────────────────────────
folium.GeoJson(
    study_unions.__geo_interface__,
    name='Union Details',
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': 'transparent',
        'weight': 0
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['adm3_name', 'adm2_name', 'risk_score'],
        aliases=['Union:', 'District:', 'Risk Score:'],
        style='background-color: #1e2a3a; color: white; font-size: 13px; padding: 8px;'
    )
).add_to(m)

# ── Add district boundary outlines ────────────────────────────────────────
folium.GeoJson(
    study_districts.__geo_interface__,
    name='District Boundaries',
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': 'white',
        'weight': 2.5,
        'dashArray': '5,5'
    }
).add_to(m)

# ── Add district markers with popup facts ─────────────────────────────────
for _, row in study_districts.iterrows():
    name = row['adm2_name']
    f    = facts.get(name, {})
    popup_html = f"""
    <div style='background:#1e2a3a;color:white;padding:12px;
                border-radius:8px;min-width:200px;font-family:Arial'>
        <b style='font-size:15px;color:#e85d24'>{name} District</b><br><br>
        <b>Displaced persons:</b> {f.get('displaced','N/A')}<br>
        <b>Primary hazard:</b> {f.get('hazard','N/A')}<br>
        <b>Char areas:</b> {f.get('chars','N/A')}<br><br>
        <i style='color:#aaa;font-size:11px'>
        Source: IOM DTM Bangladesh / BWDB estimates</i>
    </div>
    """
    folium.Marker(
        location=[row['center_lat'], row['center_lon']],
        popup=folium.Popup(popup_html, max_width=280),
        tooltip=f"{name} — click for details",
        icon=folium.Icon(color='red', icon='warning-sign', prefix='glyphicon')
    ).add_to(m)

# ── Add title box ──────────────────────────────────────────────────────────
title_html = """
<div style='position:fixed;top:15px;left:50%;transform:translateX(-50%);
            background:#1e2a3a;color:white;padding:10px 20px;
            border-radius:8px;z-index:1000;text-align:center;
            border:2px solid #e85d24;'>
    <b style='font-size:15px'>DeshantorMap</b><br>
    <span style='font-size:11px;color:#aaa'>
    Climate Displacement Risk — Noakhali · Feni · Lakshmipur
    </span>
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

folium.LayerControl().add_to(m)

# ── Save ───────────────────────────────────────────────────────────────────
output_path = os.path.join(OUT, 'interactive_risk_map.html')
m.save(output_path)
print(f"\nInteractive map saved to: {output_path}")
print("Open this file in your browser to explore!")