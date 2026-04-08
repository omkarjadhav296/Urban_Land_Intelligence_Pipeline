"""
Advanced WebGIS Visualization Engine.

Generates a fully interactive, mobile-friendly WebGIS dashboard.
Features:
- Dynamic GeoJSON File Uploads (Client-Side Rendering)
- Custom Drawing & Measurement Tools (Turf.js)
- 3D Extrusion with Fallback Logic
- Collapsible Glassmorphism UI
"""
import os
import logging
import geopandas as gpd

logger = logging.getLogger(__name__)

class Viewer3D:
    def __init__(self, config):
        self.config = config

    def generate_3d_viewer(self, gdf: gpd.GeoDataFrame, output_dir2: str):
        """Generates the advanced WebGIS HTML dashboard."""
        logger.info("Generating WebGIS Dashboard with Dynamic Upload Capabilities...")
        
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
    <title>Enterprise Urban Intelligence Dashboard</title>
    
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
        
        /* Glassmorphism Panel */
        #control-panel {{
            position: absolute; top: 15px; left: 15px;
            width: 340px; max-height: 95vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(12px);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            z-index: 10;
            display: flex; flex-direction: column;
            transition: transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}
        
        .panel-header {{ padding: 15px 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; background: #f8f9fa; border-radius: 12px 12px 0 0; }}
        .panel-header h2 {{ margin: 0; font-size: 1.1rem; color: #2c3e50; }}
        
        #toggle-panel-btn {{ background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #7f8c8d; transition: 0.3s; }}
        #toggle-panel-btn:hover {{ color: #3498db; }}
        
        .panel-content {{ padding: 20px; overflow-y: auto; }}
        .panel-section {{ margin-bottom: 20px; }}
        .panel-section label {{ display: block; font-weight: bold; margin-bottom: 8px; font-size: 0.85rem; color: #34495e; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        select, button {{ width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #bdc3c7; background: #fff; cursor: pointer; transition: 0.2s; font-size: 0.9rem; }}
        select:hover, button:hover {{ border-color: #3498db; }}
        
        .btn-primary {{ background: #3498db; color: white; border: none; font-weight: bold; }}
        .btn-primary:hover {{ background: #2980b9; box-shadow: 0 4px 10px rgba(52,152,219,0.3); }}
        
        /* Custom Tool Buttons Grid */
        .tools-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }}
        .tool-btn {{ padding: 8px 5px; font-size: 0.8rem; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 6px; color: #2c3e50; font-weight: 600; display: flex; flex-direction: column; align-items: center; gap: 5px; }}
        .tool-btn i {{ font-size: 1.1rem; }}
        .tool-btn:hover {{ background: #dcdde1; border-color: #7f8c8d; }}
        .tool-btn.active {{ background: #3498db; color: white; border-color: #2980b9; }}
        .tool-btn.danger:hover {{ background: #e74c3c; color: white; border-color: #c0392b; }}

        /* File Upload Styling */
        .file-upload-wrapper {{ position: relative; overflow: hidden; display: inline-block; width: 100%; }}
        .file-upload-wrapper input[type=file] {{ font-size: 100px; position: absolute; left: 0; top: 0; opacity: 0; cursor: pointer; height: 100%; }}
        .btn-upload {{ background: #27ae60; color: white; border: none; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 8px; }}
        .btn-upload:hover {{ background: #2ecc71; box-shadow: 0 4px 10px rgba(46, 204, 113, 0.3); }}

        /* Legend Styling */
        .legend-row {{ display: flex; align-items: center; margin-bottom: 5px; font-size: 0.85rem; color: #555; }}
        .legend-color {{ width: 20px; height: 20px; border-radius: 4px; margin-right: 10px; border: 1px solid rgba(0,0,0,0.1); }}
        
        #measurement-results {{ margin-top: 10px; padding: 12px; background: #e8f4f8; border-radius: 6px; color: #2980b9; font-size: 0.9rem; display: none; border-left: 4px solid #3498db; }}
        
        .maplibregl-ctrl-geocoder {{ min-width: 100%; box-shadow: none; border: 1px solid #bdc3c7; border-radius: 6px; }}

        /* Hover Popup Styling */
        .maplibregl-popup-content {{ border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); padding: 15px; font-family: inherit; min-width: 200px; }}
        .popup-title {{ font-weight: bold; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-bottom: 8px; color: #2c3e50; text-transform: capitalize; }}
        .popup-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 0.85rem; }}
        .popup-row span:first-child {{ color: #7f8c8d; padding-right: 15px; }}
        .popup-row span:last-child {{ font-weight: 600; color: #2c3e50; text-align: right; }}

        /* Mobile Adjustments */
        @media (max-width: 768px) {{
            #control-panel {{ width: 92%; left: 4%; top: auto; bottom: 20px; max-height: 60vh; }}
            #control-panel.collapsed {{ transform: translateY(calc(100% - 60px)); }}
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
        <h2><i class="fa-solid fa-layer-group"></i> WebGIS Dashboard</h2>
        <button id="toggle-panel-btn" title="Toggle Panel"><i class="fa-solid fa-chevron-down"></i></button>
    </div>
    
    <div class="panel-content" id="panel-content-body">
        
        <!-- Search Bar -->
        <div class="panel-section" id="geocoder-container"></div>

        <!-- File Upload Section -->
        <div class="panel-section">
            <label><i class="fa-solid fa-cloud-arrow-up"></i> Load Custom GeoJSON</label>
            <div class="file-upload-wrapper">
                <button class="btn-upload"><i class="fa-solid fa-file-import"></i> Choose File</button>
                <input type="file" id="geojson-upload" accept=".geojson,.json" />
            </div>
            <div id="upload-status" style="font-size: 0.75rem; color: #7f8c8d; margin-top: 5px; text-align: center;">No file selected</div>
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

        <!-- Base Map -->
        <div class="panel-section">
            <label><i class="fa-solid fa-map"></i> Base Map</label>
            <select id="layer-switcher">
                <option value="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json">Light Mode (Carto)</option>
                <option value="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json">Dark Mode (Carto)</option>
                <option value="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json">Satellite/Color (Carto)</option>
            </select>
        </div>
        
        <!-- Legend -->
        <div class="panel-section">
            <label><i class="fa-solid fa-chart-line"></i> Elevation Legend</label>
            <div class="legend-row"><div class="legend-color" style="background:#f1eef6;"></div> 0m - 20m</div>
            <div class="legend-row"><div class="legend-color" style="background:#bdc9e1;"></div> 20m - 40m</div>
            <div class="legend-row"><div class="legend-color" style="background:#74a9cf;"></div> 40m - 60m</div>
            <div class="legend-row"><div class="legend-color" style="background:#2b8cbe;"></div> 60m - 100m</div>
            <div class="legend-row"><div class="legend-color" style="background:#045a8d;"></div> 100m+</div>
        </div>

        <!-- Reset Camera -->
        <div class="panel-section">
            <button id="reset-view" class="btn-primary"><i class="fa-solid fa-compress"></i> Reset 3D View</button>
        </div>
    </div>
</div>

<script>
    // Initial Python Injected Data
    let currentGeoJSON = {geojson_data};
    let initialCenter = {center_coords};

    // 1. Initialize Map
    const map = new maplibregl.Map({{
        container: 'map',
        style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
        center: initialCenter,
        zoom: 15.5, pitch: 45, bearing: -17.6, antialias: true
    }});

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    // 2. Mapbox Draw Setup (Hidden default UI, controlled by our custom buttons)
    const draw = new MapboxDraw({{
        displayControlsDefault: false
    }});
    map.addControl(draw);

    // Custom Tool Button Logic
    document.getElementById('btn-draw').addEventListener('click', () => {{
        draw.changeMode('draw_polygon');
        document.getElementById('btn-draw').classList.add('active');
    }});
    
    document.getElementById('btn-delete').addEventListener('click', () => {{
        draw.trash();
        updateArea();
    }});
    
    document.getElementById('btn-clear').addEventListener('click', () => {{
        draw.deleteAll();
        updateArea();
        document.getElementById('btn-draw').classList.remove('active');
    }});

    // 3. Geocoder Setup
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

    // 4. Core Rendering Engine
    function render3DLayer(data) {{
        // If source exists, update data. Otherwise, create it.
        if (map.getSource('tp-data')) {{
            map.getSource('tp-data').setData(data);
        }} else {{
            map.addSource('tp-data', {{ 'type': 'geojson', 'data': data }});
            map.addLayer({{
                'id': 'tp-3d-buildings',
                'source': 'tp-data',
                'type': 'fill-extrusion',
                'paint': {{
                    // Fallback to a height of 10 if elev_mean is missing
                    'fill-extrusion-height': ['*', ['coalesce', ['get', 'elev_mean'], 10], 2],
                    'fill-extrusion-color': [
                        'interpolate', ['linear'], ['coalesce', ['get', 'elev_mean'], 0],
                        0, '#f1eef6', 20, '#bdc9e1', 40, '#74a9cf', 60, '#2b8cbe', 100, '#045a8d'
                    ],
                    'fill-extrusion-opacity': 0.85
                }}
            }});
        }}
    }}

    map.on('load', () => render3DLayer(currentGeoJSON));

    // 5. Dynamic File Upload Logic
    document.getElementById('geojson-upload').addEventListener('change', function(e) {{
        const file = e.target.files[0];
        if (!file) return;
        
        document.getElementById('upload-status').innerText = `Loading: ${{file.name}}...`;
        
        const reader = new FileReader();
        reader.onload = function(event) {{
            try {{
                const uploadedGeoJSON = JSON.parse(event.target.result);
                
                // Validate it's a FeatureCollection
                if(uploadedGeoJSON.type !== 'FeatureCollection' && uploadedGeoJSON.type !== 'Feature') {{
                    throw new Error("Invalid GeoJSON Format");
                }}

                currentGeoJSON = uploadedGeoJSON;
                render3DLayer(currentGeoJSON);
                
                // Use Turf.js to calculate bounding box and fly to new data
                const bbox = turf.bbox(currentGeoJSON);
                map.fitBounds(bbox, {{ padding: 50, pitch: 45, maxZoom: 17 }});
                
                document.getElementById('upload-status').innerText = `Success: ${{file.name}}`;
                document.getElementById('upload-status').style.color = '#27ae60';
                
            }} catch (err) {{
                console.error("Upload Error:", err);
                document.getElementById('upload-status').innerText = "Error: Invalid GeoJSON file.";
                document.getElementById('upload-status').style.color = '#e74c3c';
            }}
        }};
        reader.readAsText(file);
    }});

    // 6. Hover Tooltip Logic
    const popup = new maplibregl.Popup({{ closeButton: false, closeOnClick: false }});
    
    map.on('mousemove', 'tp-3d-buildings', (e) => {{
        map.getCanvas().style.cursor = 'pointer';
        const props = e.features[0].properties;
        
        // Dynamically build HTML based on whatever properties the uploaded file has
        let html = `<div class="popup-title">Feature Details</div>`;
        
        // Prioritize our known fields if they exist
        if (props.elev_mean !== undefined) html += `<div class="popup-row"><span>Elevation:</span> <span>${{props.elev_mean.toFixed(1)}} m</span></div>`;
        if (props.area_sqm !== undefined) html += `<div class="popup-row"><span>Area:</span> <span>${{parseInt(props.area_sqm).toLocaleString()}} sqm</span></div>`;
        
        // Loop through remaining unknown properties (up to 5 to prevent huge popups)
        let count = 0;
        for (const [key, value] of Object.entries(props)) {{
            if (key !== 'elev_mean' && key !== 'area_sqm' && count < 5) {{
                const displayVal = typeof value === 'number' && !Number.isInteger(value) ? value.toFixed(2) : value;
                html += `<div class="popup-row"><span>${{key.replace(/_/g, ' ')}}:</span> <span>${{displayVal}}</span></div>`;
                count++;
            }}
        }}
        
        popup.setLngLat(e.lngLat).setHTML(html).addTo(map);
    }});

    map.on('mouseleave', 'tp-3d-buildings', () => {{
        map.getCanvas().style.cursor = '';
        popup.remove();
    }});

    // 7. Turf.js Drawing Measurement
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
                document.getElementById('btn-draw').classList.remove('active');
            }}
        }} catch (error) {{
            console.error("Turf.js Calculation Error:", error);
        }}
    }}
    
    map.on('draw.create', updateArea);
    map.on('draw.delete', updateArea);
    map.on('draw.update', updateArea);

    // 8. UI Interactions
    document.getElementById('layer-switcher').addEventListener('change', (e) => {{
        map.setStyle(e.target.value);
        map.once('styledata', () => render3DLayer(currentGeoJSON));
    }});

    document.getElementById('reset-view').addEventListener('click', () => {{
        map.flyTo({{ center: initialCenter, zoom: 15.5, pitch: 45, bearing: -17.6, essential: true }});
    }});

    const panel = document.getElementById('control-panel');
    const toggleBtn = document.getElementById('toggle-panel-btn');
    const toggleIcon = toggleBtn.querySelector('i');
    
    toggleBtn.addEventListener('click', () => {{
        panel.classList.toggle('collapsed');
        if (panel.classList.contains('collapsed')) {{
            toggleIcon.classList.replace('fa-chevron-down', 'fa-chevron-up');
        }} else {{
            toggleIcon.classList.replace('fa-chevron-up', 'fa-chevron-down');
        }}
    }});
</script>
</body>
</html>"""

        projectRoot= os.getcwd()
        output_path = os.path.join(projectRoot, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"Advanced WebGIS Viewer generated successfully at: {output_path}")