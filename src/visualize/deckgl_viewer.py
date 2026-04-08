"""
Advanced WebGIS Visualization Engine.

Generates a fully interactive, mobile-friendly WebGIS dashboard.
Features include: Collapsible Control Panel, Data Hover Tooltips,
Elevation Legends, and robust Mapbox Draw/Turf.js integration.
"""
import os
import logging
import geopandas as gpd

logger = logging.getLogger(__name__)

class Viewer3D:
    def __init__(self, config):
        self.config = config

    def generate_3d_viewer(self, gdf: gpd.GeoDataFrame, output_dir: str):
        """Generates the advanced WebGIS HTML dashboard."""
        logger.info("Generating Mobile-Friendly Advanced WebGIS Dashboard...")
        
        gdf_wgs84 = gdf.to_crs(self.config.WGS84)
        
        if gdf_wgs84.empty:
            logger.warning("Empty dataframe provided to 3D Viewer.")
            return
            
        centroid = gdf_wgs84.geometry.unary_union.centroid
        center_coords = [centroid.x, centroid.y]
        geojson_data = gdf_wgs84.to_json()

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Advanced 3D Urban Intelligence Dashboard</title>
    
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
        body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; overflow: hidden; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        
        /* Glassmorphism Panel */
        #control-panel {{
            position: absolute;
            top: 15px; left: 15px;
            width: 320px; max-height: 90vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            z-index: 10;
            transition: transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            display: flex; flex-direction: column;
        }}
        
        .panel-header {{
            padding: 15px 20px; border-bottom: 1px solid #eee;
            display: flex; justify-content: space-between; align-items: center;
        }}
        .panel-header h2 {{ margin: 0; font-size: 1.1rem; color: #2c3e50; }}
        
        /* Collapse Toggle Button */
        #toggle-panel-btn {{
            background: none; border: none; font-size: 1.2rem;
            cursor: pointer; color: #7f8c8d; transition: 0.3s;
        }}
        #toggle-panel-btn:hover {{ color: #3498db; }}
        
        .panel-content {{ padding: 20px; overflow-y: auto; }}
        .panel-section {{ margin-bottom: 15px; }}
        .panel-section label {{ display: block; font-weight: bold; margin-bottom: 8px; font-size: 0.85rem; color: #34495e; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        select, button {{ width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #bdc3c7; background: #fff; cursor: pointer; transition: 0.2s; font-size: 0.9rem; }}
        select:hover, button:hover {{ border-color: #3498db; box-shadow: 0 2px 5px rgba(52,152,219,0.2); }}
        button {{ background: #3498db; color: white; border: none; font-weight: bold; margin-top: 5px; }}
        button:hover {{ background: #2980b9; }}

        /* Legend Styling */
        .legend-row {{ display: flex; align-items: center; margin-bottom: 5px; font-size: 0.85rem; color: #555; }}
        .legend-color {{ width: 20px; height: 20px; border-radius: 4px; margin-right: 10px; border: 1px solid rgba(0,0,0,0.1); }}
        
        #measurement-results {{ margin-top: 10px; padding: 12px; background: #e8f4f8; border-radius: 6px; color: #2980b9; font-size: 0.9rem; display: none; border-left: 4px solid #3498db; }}
        .maplibregl-ctrl-geocoder {{ min-width: 100%; box-shadow: none; border: 1px solid #bdc3c7; border-radius: 6px; }}

        /* Hover Popup Styling */
        .maplibregl-popup-content {{ border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); padding: 15px; font-family: inherit; }}
        .popup-title {{ font-weight: bold; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-bottom: 8px; color: #2c3e50; }}
        .popup-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 0.85rem; }}
        .popup-row span:first-child {{ color: #7f8c8d; padding-right: 15px; }}
        .popup-row span:last-child {{ font-weight: 600; color: #2c3e50; }}

        /* Responsive Mobile Design */
        @media (max-width: 768px) {{
            #control-panel {{ width: 92%; left: 4%; top: auto; bottom: 20px; max-height: 60vh; }}
            /* When collapsed on mobile, slide down */
            #control-panel.collapsed {{ transform: translateY(calc(100% - 60px)); }}
            /* When collapsed on desktop, slide left */
            @media (min-width: 769px) {{
                #control-panel.collapsed {{ transform: translateX(-calc(100% - 15px)); }}
            }}
        }}
    </style>
</head>
<body>

<div id="map"></div>

<!-- Control Panel -->
<div id="control-panel">
    <div class="panel-header">
        <h2><i class="fa-solid fa-layer-group"></i> Urban Hub</h2>
        <button id="toggle-panel-btn" title="Toggle Panel"><i class="fa-solid fa-chevron-down"></i></button>
    </div>
    
    <div class="panel-content" id="panel-content-body">
        <div class="panel-section" id="geocoder-container"></div>

        <div class="panel-section">
            <label><i class="fa-solid fa-map"></i> Base Map</label>
            <select id="layer-switcher">
                <option value="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json">Light Mode (Carto)</option>
                <option value="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json">Dark Mode (Carto)</option>
                <option value="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json">Satellite/Color (Carto)</option>
            </select>
        </div>
        
        <!-- Elevation Legend -->
        <div class="panel-section">
            <label><i class="fa-solid fa-chart-line"></i> Elevation Legend</label>
            <div class="legend-row"><div class="legend-color" style="background:#f1eef6;"></div> 0m - 20m</div>
            <div class="legend-row"><div class="legend-color" style="background:#bdc9e1;"></div> 20m - 40m</div>
            <div class="legend-row"><div class="legend-color" style="background:#74a9cf;"></div> 40m - 60m</div>
            <div class="legend-row"><div class="legend-color" style="background:#2b8cbe;"></div> 60m - 100m</div>
            <div class="legend-row"><div class="legend-color" style="background:#045a8d;"></div> 100m+</div>
        </div>

        <div class="panel-section">
            <label><i class="fa-solid fa-video"></i> Camera</label>
            <button id="reset-view"><i class="fa-solid fa-compress"></i> Reset 3D View</button>
        </div>

        <div id="measurement-results">
            <strong><i class="fa-solid fa-ruler-combined"></i> Area Measure:</strong><br>
            <span id="calculated-area">Draw a polygon.</span>
        </div>
    </div>
</div>

<script>
    const tpGeoJSON = {geojson_data};
    const centerCoords = {center_coords};

    // 1. Initialize Map
    const map = new maplibregl.Map({{
        container: 'map',
        style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
        center: centerCoords,
        zoom: 15.5, pitch: 45, bearing: -17.6, antialias: true
    }});

    // 2. Add Standard Controls
    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    // 3. Robust Mapbox Draw Setup
    const draw = new MapboxDraw({{
        displayControlsDefault: false,
        controls: {{ polygon: true, trash: true }},
        defaultMode: 'draw_polygon'
    }});
    map.addControl(draw, 'top-right');

    // 4. Geocoder Setup
    const geocoderApi = {{
        forwardGeocode: async (config) => {{
            const features = [];
            try {{
                const req = `https://nominatim.openstreetmap.org/search?q=${{config.query}}&format=geojson&polygon_geojson=1&addressdetails=1`;
                const res = await fetch(req);
                const geojson = await res.json();
                for (const f of geojson.features) {{
                    const center = [ f.bbox[0] + (f.bbox[2] - f.bbox[0]) / 2, f.bbox[1] + (f.bbox[3] - f.bbox[1]) / 2 ];
                    features.push({{ type: 'Feature', geometry: {{ type: 'Point', coordinates: center }}, place_name: f.properties.display_name, properties: f.properties, text: f.properties.display_name, place_type: ['place'], center: center }});
                }}
            }} catch (e) {{ console.error("Geocoder error:", e); }}
            return {{ features }};
        }}
    }};
    const geocoder = new MaplibreGeocoder(geocoderApi, {{ maplibregl: maplibregl }});
    document.getElementById('geocoder-container').appendChild(geocoder.onAdd(map));

    // 5. Data Rendering & Interactivity
    function add3DTpLayer() {{
        if(map.getSource('tp-data')) return; // Prevent duplicate sources
        
        map.addSource('tp-data', {{ 'type': 'geojson', 'data': tpGeoJSON }});
        map.addLayer({{
            'id': 'tp-3d-buildings',
            'source': 'tp-data',
            'type': 'fill-extrusion',
            'paint': {{
                'fill-extrusion-height': ['*', ['get', 'elev_mean'], 2],
                'fill-extrusion-color': [
                    'interpolate', ['linear'], ['get', 'elev_mean'],
                    0, '#f1eef6', 20, '#bdc9e1', 40, '#74a9cf', 60, '#2b8cbe', 100, '#045a8d'
                ],
                'fill-extrusion-opacity': 0.85
            }}
        }});
    }}

    map.on('load', add3DTpLayer);

    // --- HOVER TOOLTIP LOGIC ---
    const popup = new maplibregl.Popup({{ closeButton: false, closeOnClick: false }});
    
    map.on('mousemove', 'tp-3d-buildings', (e) => {{
        map.getCanvas().style.cursor = 'pointer';
        const props = e.features[0].properties;
        
        // Format properties safely
        const elev = props.elev_mean ? props.elev_mean.toFixed(1) + ' m' : 'N/A';
        const area = props.area_sqm ? parseInt(props.area_sqm).toLocaleString() + ' sqm' : 'N/A';
        const bldgs = props.building_count ? props.building_count : 0;
        
        const html = `
            <div class="popup-title">Plot Details</div>
            <div class="popup-row"><span>Plot ID:</span> <span>${{props.plot_id || 'Unknown'}}</span></div>
            <div class="popup-row"><span>Area:</span> <span>${{area}}</span></div>
            <div class="popup-row"><span>Elevation:</span> <span>${{elev}}</span></div>
            <div class="popup-row"><span>Buildings:</span> <span>${{bldgs}}</span></div>
        `;
        popup.setLngLat(e.lngLat).setHTML(html).addTo(map);
    }});

    map.on('mouseleave', 'tp-3d-buildings', () => {{
        map.getCanvas().style.cursor = '';
        popup.remove();
    }});

    // --- DRAWING TOOL CALCULATION FIX ---
    function updateArea() {{
        try {{
            const data = draw.getAll();
            const resultsDiv = document.getElementById('measurement-results');
            const areaSpan = document.getElementById('calculated-area');
            
            if (data.features.length > 0) {{
                const area = turf.area(data);
                resultsDiv.style.display = 'block';
                areaSpan.innerHTML = `<strong>${{Math.round(area).toLocaleString()}}</strong> sqm`;
            }} else {{
                resultsDiv.style.display = 'none';
            }}
        }} catch (error) {{
            console.error("Turf.js Calculation Error: ", error);
        }}
    }}
    map.on('draw.create', updateArea);
    map.on('draw.delete', updateArea);
    map.on('draw.update', updateArea);

    // --- UI EVENT LISTENERS ---
    // Layer Switcher
    document.getElementById('layer-switcher').addEventListener('change', (e) => {{
        map.setStyle(e.target.value);
        map.once('styledata', add3DTpLayer); // Re-add data after style change
    }});

    // Reset View
    document.getElementById('reset-view').addEventListener('click', () => {{
        map.flyTo({{ center: centerCoords, zoom: 15.5, pitch: 45, bearing: -17.6, essential: true }});
    }});

    // Panel Collapse Toggle
    const panel = document.getElementById('control-panel');
    const toggleBtn = document.getElementById('toggle-panel-btn');
    const toggleIcon = toggleBtn.querySelector('i');
    
    toggleBtn.addEventListener('click', () => {{
        panel.classList.toggle('collapsed');
        if (panel.classList.contains('collapsed')) {{
            toggleIcon.classList.remove('fa-chevron-down');
            toggleIcon.classList.add('fa-chevron-up');
        }} else {{
            toggleIcon.classList.remove('fa-chevron-up');
            toggleIcon.classList.add('fa-chevron-down');
        }}
    }});
</script>
</body>
</html>"""

        projectRoot = os.getcwd()
        output_path = os.path.join(projectRoot, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"Advanced WebGIS Viewer successfully generated at: {output_path}")