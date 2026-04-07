"""
Advanced WebGIS Visualization Engine.

Generates a fully interactive, zero-backend WebGIS dashboard using MapLibre GL JS, 
Mapbox Draw, and Turf.js. Injects Python-processed GeoJSON directly into the 
JavaScript execution context for seamless static hosting.
"""
import os
import json
import logging
import geopandas as gpd

logger = logging.getLogger(__name__)

class Viewer3D:
    def __init__(self, config):
        self.config = config

    def generate_3d_viewer(self, gdf: gpd.GeoDataFrame, output_dir: str):
        """Generates the advanced WebGIS HTML dashboard."""
        logger.info("Generating Advanced WebGIS Dashboard...")
        
        gdf_wgs84 = gdf.to_crs(self.config.WGS84)
        
        if gdf_wgs84.empty:
            logger.warning("Empty dataframe provided to 3D Viewer.")
            return
            
        # Calculate center for initial camera view
        centroid = gdf_wgs84.geometry.unary_union.centroid
        center_coords = [centroid.x, centroid.y]
        
        # Serialize the GeoPandas dataframe to a raw JSON string
        geojson_data = gdf_wgs84.to_json()

        # The Advanced WebGIS HTML Template
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced 3D Urban Intelligence Dashboard</title>
    
    <!-- MapLibre GL JS -->
    <script src="https://unpkg.com/maplibre-gl@3.3.1/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.3.1/dist/maplibre-gl.css" rel="stylesheet" />
    
    <!-- Mapbox Draw & Turf.js (For drawing and measurement) -->
    <script src="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-draw/v1.4.3/mapbox-gl-draw.js"></script>
    <link rel="stylesheet" href="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-draw/v1.4.3/mapbox-gl-draw.css" type="text/css" />
    <script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>

    <!-- MapLibre Geocoder (Search Bar) -->
    <script src="https://unpkg.com/@maplibre/maplibre-gl-geocoder@1.5.0/dist/maplibre-gl-geocoder.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/@maplibre/maplibre-gl-geocoder@1.5.0/dist/maplibre-gl-geocoder.css" type="text/css" />

    <style>
        body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        
        /* Modern Glassmorphism Control Panel */
        #control-panel {{
            position: absolute;
            top: 15px;
            left: 15px;
            width: 320px;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            z-index: 1;
            border: 1px solid rgba(255,255,255,0.5);
        }}
        h2 {{ margin-top: 0; font-size: 1.2rem; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .panel-section {{ margin-bottom: 15px; }}
        .panel-section label {{ display: block; font-weight: bold; margin-bottom: 5px; font-size: 0.9rem; color: #34495e; }}
        
        select, button {{
            width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #bdc3c7;
            background: #f9f9f9; cursor: pointer; transition: 0.3s;
        }}
        select:hover, button:hover {{ border-color: #3498db; }}
        
        #measurement-results {{
            margin-top: 15px; padding: 10px; background: #e8f4f8; 
            border-radius: 6px; font-family: monospace; color: #2980b9;
            font-size: 0.95rem; display: none;
        }}
        
        /* Position Geocoder */
        .maplibregl-ctrl-geocoder {{ min-width: 100%; }}
    </style>
</head>
<body>

<div id="map"></div>

<div id="control-panel">
    <h2>🌍 Urban Intelligence Hub</h2>
    
    <!-- Search Bar Container -->
    <div class="panel-section" id="geocoder-container"></div>

    <!-- Base Layer Toggle -->
    <div class="panel-section">
        <label>🗺️ Base Map Style</label>
        <select id="layer-switcher">
            <option value="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json">Light Mode (Carto)</option>
            <option value="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json">Dark Mode (Carto)</option>
            <option value="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json">Color / Streets (Carto)</option>
        </select>
    </div>
    
    <!-- Camera Controls -->
    <div class="panel-section">
        <label>🎥 Camera Actions</label>
        <button id="reset-view">Reset 3D View</button>
    </div>

    <!-- Live Measurement Output -->
    <div id="measurement-results">
        <strong>Measurement:</strong><br>
        <span id="calculated-area">Draw a polygon to calculate area.</span>
    </div>
</div>

<script>
    // --- 1. DATA INJECTION ---
    // Python directly injects the spatial data here to bypass any server/CORS issues
    const tpGeoJSON = {geojson_data};
    const centerCoords = {center_coords};

    // --- 2. MAP INITIALIZATION ---
    const map = new maplibregl.Map({{
        container: 'map',
        style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
        center: centerCoords,
        zoom: 15.5,
        pitch: 45,
        bearing: -17.6,
        antialias: true
    }});

    // --- 3. UI CONTROLS ---
    // Add Navigation Controls (Zoom/Rotate)
    map.addControl(new maplibregl.NavigationControl(), 'bottom-right');

    // Add Search Bar (Nominatim API - Free/Open Source)
    const geocoderApi = {{
        forwardGeocode: async (config) => {{
            const features = [];
            try {{
                const request = `https://nominatim.openstreetmap.org/search?q=${{config.query}}&format=geojson&polygon_geojson=1&addressdetails=1`;
                const response = await fetch(request);
                const geojson = await response.json();
                for (const feature of geojson.features) {{
                    const center = [ feature.bbox[0] + (feature.bbox[2] - feature.bbox[0]) / 2, feature.bbox[1] + (feature.bbox[3] - feature.bbox[1]) / 2 ];
                    features.push({{ type: 'Feature', geometry: {{ type: 'Point', coordinates: center }}, place_name: feature.properties.display_name, properties: feature.properties, text: feature.properties.display_name, place_type: ['place'], center: center }});
                }}
            }} catch (e) {{ console.error("Failed to forwardGeocode", e); }}
            return {{ features }};
        }}
    }};
    const geocoder = new MaplibreGeocoder(geocoderApi, {{ maplibregl: maplibregl }});
    document.getElementById('geocoder-container').appendChild(geocoder.onAdd(map));

    // Add Drawing Tools
    const draw = new MapboxDraw({{
        displayControlsDefault: false,
        controls: {{ polygon: true, trash: true }}
    }});
    map.addControl(draw, 'bottom-right');

    // --- 4. MAP EVENT LISTENERS ---
    map.on('load', () => {{
        add3DTpLayer();
    }});

    // Draw Event: Calculate Area using Turf.js
    map.on('draw.create', updateArea);
    map.on('draw.delete', updateArea);
    map.on('draw.update', updateArea);

    function updateArea(e) {{
        const data = draw.getAll();
        const resultsDiv = document.getElementById('measurement-results');
        const areaSpan = document.getElementById('calculated-area');
        
        if (data.features.length > 0) {{
            const area = turf.area(data);
            const roundedArea = Math.round(area * 100) / 100;
            resultsDiv.style.display = 'block';
            areaSpan.innerHTML = `<strong>${{roundedArea.toLocaleString()}}</strong> square meters`;
        }} else {{
            resultsDiv.style.display = 'none';
        }}
    }}

    // --- 5. RENDER 3D DATA ---
    function add3DTpLayer() {{
        // Add the Python-injected GeoJSON as a map source
        map.addSource('tp-data', {{
            'type': 'geojson',
            'data': tpGeoJSON
        }});

        // Add the 3D Fill Extrusion Layer
        map.addLayer({{
            'id': 'tp-3d-buildings',
            'source': 'tp-data',
            'type': 'fill-extrusion',
            'paint': {{
                // Extrude height based on the elev_mean property
                'fill-extrusion-height': ['*', ['get', 'elev_mean'], 2],
                
                // Color ramp based on elevation
                'fill-extrusion-color': [
                    'interpolate', ['linear'], ['get', 'elev_mean'],
                    0, '#f1eef6',
                    20, '#bdc9e1',
                    40, '#74a9cf',
                    60, '#2b8cbe',
                    100, '#045a8d'
                ],
                'fill-extrusion-opacity': 0.85
            }}
        }});
    }}

    // --- 6. CONTROL PANEL LOGIC ---
    // Handle Base Map Switching
    document.getElementById('layer-switcher').addEventListener('change', (e) => {{
        map.setStyle(e.target.value);
        // We must wait for the new style to load before re-adding our 3D data
        map.once('styledata', () => {{ add3DTpLayer(); }});
    }});

    // Handle Camera Reset
    document.getElementById('reset-view').addEventListener('click', () => {{
        map.flyTo({{
            center: centerCoords,
            zoom: 15.5,
            pitch: 45,
            bearing: -17.6,
            essential: true
        }});
    }});
</script>
</body>
</html>"""

        # Ensure we write safely using utf-8 encoding
        project_root= os.getcwd()
        output_path = os.path.join(project_root, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"Advanced WebGIS Viewer successfully generated at: {output_path}")