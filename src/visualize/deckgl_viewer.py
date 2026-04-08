"""
Advanced WebGIS Visualization Engine.

Generates a fully interactive, mobile-friendly WebGIS dashboard.
Features:
- Real-time WebGL Transparency Controls
- OSM Building Context Layer & Road Infrastructure
- Right-side Project Information Panel
- Client-side GeoJSON Upload
- Built vs Vacant Plot Highlighting
"""
import os
import logging
import geopandas as gpd

logger = logging.getLogger(__name__)

class Viewer3D:
    def __init__(self, config):
        self.config = config

    def generate_3d_viewer(self, gdf: gpd.GeoDataFrame, roads_gdf: gpd.GeoDataFrame, buildings_gdf: gpd.GeoDataFrame, output_dir: str):
        """Generates the advanced WebGIS HTML dashboard with buildings, roads, and plots."""
        logger.info("Generating WebGIS Dashboard with Buildings, Roads, and Opacity Controls...")
        
        gdf_wgs84 = gdf.to_crs(self.config.WGS84)
        
        if gdf_wgs84.empty:
            logger.warning("Empty dataframe provided to 3D Viewer.")
            return
            
        centroid = gdf_wgs84.geometry.unary_union.centroid
        center_coords = [centroid.x, centroid.y]
        
        # Serialize all 3 spatial layers
        geojson_data = gdf_wgs84.to_json()
        
        roads_geojson = '{"type": "FeatureCollection", "features": []}'
        if roads_gdf is not None and not roads_gdf.empty:
            roads_geojson = roads_gdf.to_crs(self.config.WGS84).to_json()
            
        buildings_geojson = '{"type": "FeatureCollection", "features": []}'
        if buildings_gdf is not None and not buildings_gdf.empty:
            buildings_geojson = buildings_gdf.to_crs(self.config.WGS84).to_json()

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Urban Land Intelligence | Omkar Arvind Jadhav</title>
    
    <!-- MapLibre GL JS -->
    <script src="https://unpkg.com/maplibre-gl@3.3.1/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.3.1/dist/maplibre-gl.css" rel="stylesheet" />
    
    <!-- Mapbox Draw & Turf.js -->
    <script src="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-draw/v1.4.3/mapbox-gl-draw.js"></script>
    <link rel="stylesheet" href="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-draw/v1.4.3/mapbox-gl-draw.css" type="text/css" />
    <script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>

    <!-- MapLibre Geocoder -->
    <script src="https://unpkg.com/@maplibre/maplibre-gl-geocoder@1.5.0/dist/maplibre-gl-geocoder.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/@maplibre/maplibre-gl-geocoder@1.5.0/dist/maplibre-gl-geocoder.css" type="text/css" />

    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; overflow: hidden; background: #e0e0e0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        
        /* Shared Glassmorphism Panel Styles */
        .glass-panel {{
            position: absolute; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(12px);
            border-radius: 12px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15); z-index: 10;
            display: flex; flex-direction: column; transition: transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}
        
        .panel-header {{ padding: 12px 18px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; background: #f8f9fa; border-radius: 12px 12px 0 0; }}
        .panel-header h2 {{ margin: 0; font-size: 1.05rem; color: #2c3e50; display: flex; align-items: center; gap: 8px; }}
        
        .toggle-btn {{ background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #7f8c8d; transition: 0.3s; padding: 0; display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; }}
        .toggle-btn:hover {{ color: #3498db; }}
        
        .panel-content {{ padding: 15px 20px; overflow-y: auto; }}
        .panel-section {{ margin-bottom: 15px; }}
        .panel-section label {{ display: block; font-weight: bold; margin-bottom: 5px; font-size: 0.8rem; color: #34495e; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        #control-panel {{ top: 15px; left: 15px; width: 340px; max-height: 95vh; }}
        #info-panel {{ top: 15px; right: 15px; width: 320px; max-height: 95vh; }}
        
        .info-text {{ font-size: 0.85rem; color: #444; line-height: 1.35; text-align: justify; margin-bottom: 5px; }}
        .info-text ul {{ margin-top: 5px; margin-bottom: 5px; padding-left: 20px; }}
        .info-text li {{ margin-bottom: 4px; }}
        
        .developer-tag {{ margin-top: 15px; padding-top: 12px; border-top: 1px solid #eee; font-size: 0.85rem; color: #7f8c8d; text-align: center; }}
        .developer-tag strong {{ color: #2c3e50; font-size: 0.95rem; display: block; margin-top: 3px; }}
        
        select, button, input[type="file"], input[type="range"] {{ width: 100%; padding: 8px 10px; border-radius: 6px; border: 1px solid #bdc3c7; background: #fff; cursor: pointer; transition: 0.2s; font-size: 0.85rem; box-sizing: border-box; }}
        select:hover, button:hover {{ border-color: #3498db; }}
        
        .btn-primary {{ background: #3498db; color: white; border: none; font-weight: bold; }}
        .btn-primary:hover {{ background: #2980b9; box-shadow: 0 4px 10px rgba(52,152,219,0.3); }}
        
        .tools-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }}
        .tool-btn {{ padding: 8px 5px; font-size: 0.8rem; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 6px; color: #2c3e50; font-weight: 600; display: flex; flex-direction: column; align-items: center; gap: 5px; }}
        .tool-btn i {{ font-size: 1.1rem; }}
        .tool-btn:hover {{ background: #dcdde1; border-color: #7f8c8d; }}
        .tool-btn.active {{ background: #3498db; color: white; border-color: #2980b9; }}
        .tool-btn.danger:hover {{ background: #e74c3c; color: white; border-color: #c0392b; }}

        .legend-row {{ display: flex; align-items: center; margin-bottom: 4px; font-size: 0.8rem; color: #555; }}
        .legend-color {{ width: 18px; height: 18px; border-radius: 4px; margin-right: 10px; border: 1px solid rgba(0,0,0,0.1); }}
        .legend-line {{ width: 18px; height: 4px; background: #2c3e50; margin-right: 10px; border-radius: 2px; }}
        
        #measurement-results {{ margin-top: 10px; padding: 10px; background: #e8f4f8; border-radius: 6px; color: #2980b9; font-size: 0.85rem; display: none; border-left: 4px solid #3498db; }}
        
        .maplibregl-ctrl-geocoder {{ min-width: 100%; box-shadow: none; border: 1px solid #bdc3c7; border-radius: 6px; font-size: 0.85rem; }}
        .maplibregl-ctrl-geocoder input {{ padding: 8px 30px; }}
        
        .maplibregl-ctrl-bottom-right .maplibregl-ctrl-group {{ position: fixed; bottom: 25px; left: 50%; transform: translateX(-50%); display: flex; flex-direction: row; box-shadow: 0 4px 15px rgba(0,0,0,0.2); border-radius: 8px; z-index: 50; }}
        .maplibregl-ctrl-group > button {{ width: 40px; height: 40px; }}

        .maplibregl-popup-content {{ border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); padding: 12px; font-family: inherit; min-width: 200px; }}
        .popup-title {{ font-weight: bold; border-bottom: 2px solid #3498db; padding-bottom: 4px; margin-bottom: 6px; color: #2c3e50; text-transform: capitalize; font-size: 0.9rem; }}
        .popup-row {{ display: flex; justify-content: space-between; margin-bottom: 3px; font-size: 0.8rem; }}
        .popup-row span:first-child {{ color: #7f8c8d; padding-right: 15px; }}
        .popup-row span:last-child {{ font-weight: 600; color: #2c3e50; text-align: right; }}
        .anomaly-flag {{ color: #e74c3c !important; font-weight: bold; }}

        /* Opacity Slider custom style */
        input[type=range] {{ -webkit-appearance: none; background: transparent; padding: 0; height: 6px; border-radius: 3px; background: #bdc3c7; outline: none; border: none; }}
        input[type=range]::-webkit-slider-thumb {{ -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: #3498db; cursor: pointer; transition: 0.2s; }}
        input[type=range]::-webkit-slider-thumb:hover {{ transform: scale(1.2); }}

        @media (min-width: 769px) {{
            #control-panel.collapsed {{ transform: translateX(calc(-100% + 50px)); }}
            #info-panel.collapsed {{ transform: translateX(calc(100% - 50px)); }}
        }}
        @media (max-width: 768px) {{
            #control-panel {{ width: 92%; left: 4%; top: auto; bottom: 20px; max-height: 50vh; }}
            #info-panel {{ display: none; }}
            #control-panel.collapsed {{ transform: translateY(calc(100% - 50px)); }}
            .maplibregl-ctrl-bottom-right .maplibregl-ctrl-group {{ bottom: 85px; }}
        }}
    </style>
</head>
<body>

<div id="map"></div>

<!-- Left Control Panel (Tools & Layers) -->
<div id="control-panel" class="glass-panel">
    <div class="panel-header">
        <h2><i class="fa-solid fa-layer-group"></i> WebGIS Dashboard</h2>
        <button id="toggle-control-btn" class="toggle-btn" title="Toggle Panel"><i class="fa-solid fa-chevron-left"></i></button>
    </div>
    <div class="panel-content">
        <!-- Search Bar -->
        <div class="panel-section" id="geocoder-container"></div>
        
        <!-- Transparency Slider -->
        <div class="panel-section">
            <label><i class="fa-solid fa-eye"></i> Layer Transparency</label>
            <div style="display: flex; align-items: center; gap: 10px;">
                <input type="range" id="opacity-slider" min="0" max="1" step="0.05" value="0.85" style="flex-grow: 1;">
                <span id="opacity-value" style="font-size: 0.85rem; font-weight: bold; color: #2c3e50;">85%</span>
            </div>
        </div>

        <!-- Custom Drawing Tools -->
        <div class="panel-section">
            <label><i class="fa-solid fa-pen-ruler"></i> Measurement Tools</label>
            <div class="tools-grid">
                <button class="tool-btn" id="btn-draw"><i class="fa-solid fa-draw-polygon"></i> Draw</button>
                <button class="tool-btn danger" id="btn-delete"><i class="fa-solid fa-eraser"></i> Delete</button>
                <button class="tool-btn danger" id="btn-clear"><i class="fa-solid fa-trash-can"></i> Clear All</button>
            </div>
            <div id="measurement-results">
                <strong><i class="fa-solid fa-chart-area"></i> Total Area:</strong><br>
                <span id="calculated-area">Draw a polygon.</span>
            </div>
        </div>

        <!-- Base Map & Legend -->
        <div class="panel-section">
            <label><i class="fa-solid fa-map"></i> Base Map</label>
            <select id="layer-switcher" style="margin-bottom: 10px;">
                <option value="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json">Light Mode (Carto)</option>
                <option value="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json">Dark Mode (Carto)</option>
                <option value="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json">Satellite/Color (Carto)</option>
            </select>
            
            <label style="margin-top: 15px;"><i class="fa-solid fa-chart-line"></i> Land Classification</label>
            <div class="legend-row"><div class="legend-color" style="background:#e67e22;"></div> Built Plot</div>
            <div class="legend-row"><div class="legend-color" style="background:#2ecc71;"></div> Vacant Plot</div>
            <div class="legend-row"><div class="legend-color" style="background:#bdc3c7;"></div> Unclassified</div>
            
            <label style="margin-top: 10px;"><i class="fa-solid fa-city"></i> Infrastructure Context</label>
            <div class="legend-row"><div class="legend-color" style="background:#ecf0f1; border: 1px solid #bdc3c7;"></div> OSM Buildings</div>
            <div class="legend-row"><div class="legend-line"></div> OSM Road Network</div>
        </div>
        
        <!-- Custom Client-Side Upload -->
        <div class="panel-section" style="margin-bottom: 5px;">
            <label><i class="fa-solid fa-cloud-arrow-up"></i> Quick View (Local GeoJSON)</label>
            <input type="file" id="geojson-upload" accept=".geojson,application/geo+json">
        </div>
    </div>
</div>

<!-- Right Project Information Panel -->
<div id="info-panel" class="glass-panel">
    <div class="panel-header" style="flex-direction: row-reverse;">
        <h2>Project Information <i class="fa-solid fa-circle-info"></i></h2>
        <button id="toggle-info-btn" class="toggle-btn" title="Toggle Panel"><i class="fa-solid fa-chevron-right"></i></button>
    </div>
    <div class="panel-content">
        <div class="panel-section">
            <label><i class="fa-solid fa-book-open"></i> Introduction</label>
            <div class="info-text">
                Traditional Town Planning (TP) relies on static 2D boundaries. This Enterprise Spatial ETL Pipeline bridges the gap by fusing flat polygons with global satellite intelligence and urban infrastructure data.
            </div>
        </div>
        
        <div class="panel-section">
            <label><i class="fa-solid fa-bullseye"></i> Scope of Dashboard</label>
            <div class="info-text">
                <ul>
                    <li><strong>Automated Alignment:</strong> Algorithmic snapping to real-world roads.</li>
                    <li><strong>Open Data Fusion:</strong> Topology extraction (Built vs Vacant).</li>
                    <li><strong>Cloud Terrain:</strong> Integration with Google Earth Engine 30m DEM.</li>
                    <li><strong>WebGIS:</strong> Zero-backend 3D topological rendering.</li>
                </ul>
            </div>
        </div>
        
        <div class="panel-section" style="margin-top: 15px; margin-bottom: 5px;">
            <button id="reset-view" class="btn-primary"><i class="fa-solid fa-compress"></i> Reset 3D View</button>
        </div>

        <div class="developer-tag">
            Engineered & Developed by
            <strong>Omkar Arvind Jadhav</strong>
        </div>
    </div>
</div>

<script>
    // Initial Python Injected Data
    const tpGeoJSON = {geojson_data};
    const roadsGeoJSON = {roads_geojson};
    const buildingsGeoJSON = {buildings_geojson};
    let initialCenter = {center_coords};

    // 1. Initialize Map
    const map = new maplibregl.Map({{
        container: 'map', style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
        center: initialCenter, zoom: 15.5, pitch: 45, bearing: -17.6, antialias: true, attributionControl: false
    }});

    map.addControl(new maplibregl.AttributionControl({{ compact: true }}), 'bottom-left');
    map.addControl(new maplibregl.NavigationControl({{ showCompass: true }}), 'bottom-right');

    // 2. Mapbox Draw Setup
    const draw = new MapboxDraw({{ displayControlsDefault: false }});
    map.addControl(draw);

    // 3. UI Actions (Draw & Upload)
    document.getElementById('btn-draw').addEventListener('click', () => {{ draw.changeMode('draw_polygon'); document.getElementById('btn-draw').classList.add('active'); }});
    document.getElementById('btn-delete').addEventListener('click', () => {{ draw.trash(); updateArea(); }});
    document.getElementById('btn-clear').addEventListener('click', () => {{ draw.deleteAll(); updateArea(); document.getElementById('btn-draw').classList.remove('active'); }});
    
    document.getElementById('geojson-upload').addEventListener('change', function(e) {{
        const file = e.target.files[0]; if (!file) return;
        const reader = new FileReader();
        reader.onload = function(e) {{
            try {{
                const customGeoJSON = JSON.parse(e.target.result);
                const opacity = parseFloat(document.getElementById('opacity-slider').value);
                if (map.getSource('custom-upload-source')) {{ map.getSource('custom-upload-source').setData(customGeoJSON); }} 
                else {{
                    map.addSource('custom-upload-source', {{ 'type': 'geojson', 'data': customGeoJSON }});
                    map.addLayer({{
                        'id': 'custom-upload-layer', 'source': 'custom-upload-source', 'type': 'fill-extrusion',
                        'paint': {{ 'fill-extrusion-height': 15, 'fill-extrusion-color': '#9b59b6', 'fill-extrusion-opacity': opacity }}
                    }});
                }}
                map.fitBounds(turf.bbox(customGeoJSON), {{ padding: 40, pitch: 45 }});
            }} catch (err) {{ alert("Invalid GeoJSON file."); }}
        }}; reader.readAsText(file);
    }});

    // 4. Geocoder Setup
    const geocoderApi = {{
        forwardGeocode: async (config) => {{
            const features = [];
            try {{
                const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${{config.query}}&format=geojson&polygon_geojson=1&addressdetails=1`);
                const geojson = await res.json();
                for (const f of geojson.features) {{
                    const center = [ f.bbox[0] + (f.bbox[2] - f.bbox[0]) / 2, f.bbox[1] + (f.bbox[3] - f.bbox[1]) / 2 ];
                    features.push({{ type: 'Feature', geometry: {{ type: 'Point', coordinates: center }}, place_name: f.properties.display_name, properties: f.properties, text: f.properties.display_name, place_type: ['place'], center: center }});
                }}
            }} catch (e) {{}} return {{ features }};
        }}
    }};
    document.getElementById('geocoder-container').appendChild(new MaplibreGeocoder(geocoderApi, {{ maplibregl: maplibregl }}).onAdd(map));

    // 5. Core Rendering Engine
    function renderLayers() {{
        const currentOpacity = parseFloat(document.getElementById('opacity-slider').value);

        // A. Render OSM Roads (Underneath)
        if (!map.getSource('roads-data') && roadsGeoJSON.features.length > 0) {{
            map.addSource('roads-data', {{ 'type': 'geojson', 'data': roadsGeoJSON }});
            map.addLayer({{ 'id': 'osm-roads', 'type': 'line', 'source': 'roads-data', 'paint': {{ 'line-color': '#2c3e50', 'line-width': 2.5, 'line-opacity': currentOpacity }} }});
        }}

        // B. Render OSM Buildings (Context Layer)
        if (!map.getSource('buildings-data') && buildingsGeoJSON.features.length > 0) {{
            map.addSource('buildings-data', {{ 'type': 'geojson', 'data': buildingsGeoJSON }});
            map.addLayer({{
                'id': 'osm-buildings', 'type': 'fill-extrusion', 'source': 'buildings-data',
                'paint': {{
                    // Try to use OSM height, otherwise default to 8 meters
                    'fill-extrusion-height': ['coalesce', ['to-number', ['get', 'height']], 8],
                    'fill-extrusion-color': '#ecf0f1', // Contextual Light Grey
                    'fill-extrusion-opacity': currentOpacity * 0.7 // Make it slightly more transparent than TP plots
                }}
            }});
        }}

        // C. Render TP Plots (Vibrant Analytics Layer on Top)
        if (!map.getSource('tp-data')) {{
            map.addSource('tp-data', {{ 'type': 'geojson', 'data': tpGeoJSON }});
            map.addLayer({{
                'id': 'tp-3d-buildings', 'source': 'tp-data', 'type': 'fill-extrusion',
                'paint': {{
                    'fill-extrusion-height': ['*', ['coalesce', ['get', 'elev_mean'], 10], 2],
                    'fill-extrusion-color': [ 'match', ['get', 'plot_status'], 'Built', '#e67e22', 'Vacant', '#2ecc71', '#bdc3c7' ],
                    'fill-extrusion-opacity': currentOpacity
                }}
            }});
        }}
    }}

    map.on('load', renderLayers);

    // 6. Real-time Opacity Slider Logic
    document.getElementById('opacity-slider').addEventListener('input', (e) => {{
        const val = parseFloat(e.target.value);
        document.getElementById('opacity-value').innerText = Math.round(val * 100) + '%';
        
        if (map.getLayer('tp-3d-buildings')) map.setPaintProperty('tp-3d-buildings', 'fill-extrusion-opacity', val);
        if (map.getLayer('osm-buildings')) map.setPaintProperty('osm-buildings', 'fill-extrusion-opacity', val * 0.7);
        if (map.getLayer('osm-roads')) map.setPaintProperty('osm-roads', 'line-opacity', val);
        if (map.getLayer('custom-upload-layer')) map.setPaintProperty('custom-upload-layer', 'fill-extrusion-opacity', val);
    }});

    // 7. Click Tooltips & Drawing Callbacks
    const popup = new maplibregl.Popup({{ closeButton: true, closeOnClick: true }});
    map.on('click', 'tp-3d-buildings', (e) => {{
        const props = e.features[0].properties;
        const status = props.plot_status || 'Unknown';
        const anomaly = props.road_anomaly || 'Unknown';
        const anomalyClass = anomaly !== 'Adequate' && anomaly !== 'Unknown' ? 'anomaly-flag' : '';
        const elev = props.elev_mean ? props.elev_mean.toFixed(1) + ' m' : 'N/A';
        const area = props.area_sqm ? parseInt(props.area_sqm).toLocaleString() + ' sqm' : 'N/A';
        
        popup.setLngLat(e.lngLat).setHTML(`
            <div class="popup-title">Plot Analytics</div>
            <div class="popup-row"><span>Status:</span> <strong>${{status}}</strong></div>
            <div class="popup-row"><span>Road Access:</span> <span class="${{anomalyClass}}">${{anomaly}}</span></div>
            <div class="popup-row"><span>Area:</span> <span>${{area}}</span></div>
            <div class="popup-row"><span>Elevation:</span> <span>${{elev}}</span></div>
        `).addTo(map);
    }});
    map.on('mouseenter', 'tp-3d-buildings', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'tp-3d-buildings', () => map.getCanvas().style.cursor = '');

    function updateArea() {{
        try {{
            const data = draw.getAll();
            if (data.features.length > 0) {{
                document.getElementById('measurement-results').style.display = 'block';
                document.getElementById('calculated-area').innerHTML = `<strong>${{Math.round(turf.area(data)).toLocaleString()}}</strong> sqm`;
            }} else {{
                document.getElementById('measurement-results').style.display = 'none';
                document.getElementById('btn-draw').classList.remove('active');
            }}
        }} catch (e) {{}}
    }}
    map.on('draw.create', updateArea); map.on('draw.delete', updateArea); map.on('draw.update', updateArea);

    // 8. Base UI Toggles
    document.getElementById('layer-switcher').addEventListener('change', (e) => {{ map.setStyle(e.target.value); map.once('styledata', renderLayers); }});
    document.getElementById('reset-view').addEventListener('click', () => map.flyTo({{ center: initialCenter, zoom: 15.5, pitch: 45, bearing: -17.6, essential: true }}));

    const ctrlBtn = document.getElementById('toggle-control-btn').querySelector('i');
    document.getElementById('toggle-control-btn').addEventListener('click', () => {{
        document.getElementById('control-panel').classList.toggle('collapsed');
        ctrlBtn.classList.toggle('fa-chevron-left'); ctrlBtn.classList.toggle('fa-chevron-right');
    }});

    const infoBtn = document.getElementById('toggle-info-btn').querySelector('i');
    document.getElementById('toggle-info-btn').addEventListener('click', () => {{
        document.getElementById('info-panel').classList.toggle('collapsed');
        infoBtn.classList.toggle('fa-chevron-right'); infoBtn.classList.toggle('fa-chevron-left');
    }});
</script>
</body>
</html>"""

        projectRoot= os.getcwd()
        output_path = os.path.join(projectRoot, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"Advanced WebGIS Viewer generated successfully at: {output_path}")