# Urban Land Intelligence Pipeline: Ahmedabad Town Planning (TP) Scheme 🏙️🌍

## 📌 Executive Summary

This repository contains an enterprise-grade, highly scalable Geospatial ETL (Extract, Transform, Load) pipeline designed to generate 3D urban land intelligence from Town Planning (TP) schemes.

Built specifically for the city of Ahmedabad, this system demonstrates a **Cloud-Native Architecture**. It completely bypasses manual GIS software and heavy local raster processing. Instead, it utilizes strict Object-Oriented Python to programmatically extract open-source infrastructure data, perform mathematically rigorous topological transformations, and offload massive raster zonal statistics directly to Google Earth Engine's distributed servers.

## 🏗️ Geospatial Architecture & Design Rationale

The system architecture is decoupled into distinct vertical slices (Extraction, Transformation, Visualization) adhering strictly to **Dependency Injection** and **SOLID** principles. The orchestration is handled by the TPPipelineProcessor, acting as a central Facade to coordinate data flow without tight coupling to the underlying geometric operations.

### Spatial Data Handling

- **Strict CRS Management:** Geographic coordinates (WGS84 / EPSG:4326) are inherently distorted for metric measurements. The pipeline immediately projects incoming data to the local Cartesian plane: **UTM Zone 43N (EPSG:32643)**. All topological alignments, affine translations (via shapely.affinity), and area calculations occur in this strict metric space before being re-projected for web visualization.
- **Spatial Indexing & Enrichment:** The pipeline dynamically fetches real-world infrastructure (roads, buildings) via the Overpass API (OSMClient). It utilizes **R-Tree spatial indexing** (gpd.sjoin) to rapidly intersect thousands of TP plots with this infrastructure, deterministically classifying is_built status and road access.
- **Distributed Raster Compute:** To maintain a zero-disk footprint and avoid local I/O bottlenecks with heavy .tif files, the pipeline offloads elevation processing to the cloud. Local vector data is serialized to ee.FeatureCollection, and earthengine-api executes distributed ee.Reducer.mean() and ee.Reducer.minMax() algorithms against the Copernicus 30m Global DEM (GLO-30) directly on Google's clusters.

## 📂 Production Folder Structure
```cmd
ahmedabad_tp_intelligence/  
├── data/  
│ ├── input/  
│ │ └── tp_scheme.geojson # Input TP Boundaries (WGS84)  
│ └── output/ # Auto-generated enriched layers & 3D HTML  
├── src/  
│ ├── \__init_\_.py  
│ ├── core/  
│ │ ├── config.py # Immutable Dataclasses for CRS and thresholds  
│ │ └── spatial_utils.py # Affine transformation & low-level geometric utilities  
│ ├── extract/  
│ │ ├── osm_client.py # OSMnx API wrappers & Overpass querying  
│ │ └── gee_client.py # Google Earth Engine API integration  
│ ├── transform/  
│ │ ├── enrichment.py # R-Tree Spatial joins (is_built, road_access)  
│ │ ├── elevation.py # Cloud-dispatched zonal stats execution  
│ │ └── geometry.py # UTM Area calculation & spatial validation/alignment  
│ └── visualize/  
│ └── deckgl_viewer.py # Pydeck WebGL 3D HTML generator  
├── main.py # The Orchestrator (Dependency Injection)  
├── template.py # Enterprise project scaffolder  
└── requirements.txt # Pipeline dependencies
```

## 🚀 The Execution Pipeline (main.py)

When executed, the orchestrator routes data through the following deterministic stages:

- **Ingestion & Projection:** Loads standard GeoJSON and projects to UTM 43N for mathematical integrity.
- **Automated Alignment:** Fetches OSM road infrastructure and utilizes affine transformations to correct datum shifts and positional alignment errors via the SpatialUtils class.
- **Metric Calculation:** Computes highly accurate plot areas (sq.m) on the Cartesian plane.
- **Infrastructure Enrichment:** Assigns built/vacant classifications based on precise building footprint intersections.
- **Serverless Elevation:** Dispatches the vectors to Google Earth Engine to retrieve statistical elevation metadata without downloading rasters.
- **Zero-Backend 3D WebGIS:** Transforms enriched 2D polygons into extruded 3D WebGL geometries using pydeck. Exports a lightweight, standalone index.html requiring zero backend servers to render.

## ⚙️ Installation & Deployment Setup

**1\. Clone the repository:**
```cmd
git clone \[<https://github.com/omkarjadhav296/urban_land_intelligence_pipeline.git\>](<https://github.com/omkarjadhav296/urban_land_intelligence_pipeline.git>)
  
cd urban_land_intelligence_pipeline
```

**2\. Setup isolated Python Environment:**
```cmd

python3 -m venv .venv  

# On Windows:  
.venv\\Scripts\\activate

\# On Mac/Linux:  
source .venv/bin/activate
```

**3\. Install Core Geospatial Dependencies:**
```cmd
pip install -r requirements.txt
```

**4\. Authenticate Google Earth Engine:** 

You must authenticate your machine with a Google Cloud Project to utilize the serverless elevation module.

```cmd
earthengine authenticate --force  

python -c "import ee; ee.Initialize(project='&lt;YOUR_GCP_PROJECT_ID&gt;'); print('GEE Cloud Connection Successful!')"
```

**5\. Execute the Pipeline:**

Ensure your target TP scheme (tp_scheme.geojson) is located in the data/input/ directory.
```cmd
python main.py
```

## 📈 Enterprise Scaling Roadmap

To scale this architecture from a single TP scheme to state-wide processing:

- **Event-Driven Execution:** Mount the ingestion layer to an AWS S3 bucket. New .geojson uploads will automatically trigger an Apache Airflow DAG.
- **Database Materialization:** Transition in-memory GeoPandas operations to a distributed PostGIS cluster, leveraging scalable ST_Intersects queries.
- **Dynamic Serving:** Serve enriched vector artifacts as Vector Tiles (.mvt) via an asynchronous FastAPI backend to an interactive React mapping client (e.g., MapboxGL / Deck.gl).


---





*Engineered & Developed by:*<br>

**Mr. Omkar Arvind Jadhav** <br>Geospatial Data Scientist & Cloud Architect

