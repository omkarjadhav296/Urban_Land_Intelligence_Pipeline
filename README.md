# Urban Land Intelligence Pipeline: Ahmedabad TP Scheme 🏙️🌍
## 📌 Executive Summary

This repository contains a highly scalable, automated Geospatial ETL (Extract, Transform, Load) pipeline designed to generate 3D urban land intelligence from Town Planning (TP) schemes.

Built for the city of Ahmedabad, this pipeline demonstrates a **Cloud-Native Architecture**. It completely avoids manual GIS software and local heavy raster processing. Instead, it utilizes strict Object-Oriented Python to programmatically extract open-source infrastructure data, perform mathematically rigorous topological transformations, and offload massive raster zonal statistics directly to Google Earth Engine's distributed servers.

## 🏗️ Enterprise Architecture & Tech Stack

The pipeline is decoupled into distinct vertical slices (Extraction, Transformation, Visualization) adhering to **Dependency Injection** and **SOLID** principles.

- **Core Spatial Engine:** GeoPandas, Shapely, pyproj
- **Dynamic Vector Extraction:** OSMnx (Overpass API for automated infrastructure topology)
- **Cloud-Native Raster Compute:** earthengine-api (Google Earth Engine for serverless Zonal Statistics)
- **3D Rendering Engine:** pydeck (Deck.GL WebGL wrapper)

## 🚀 Key Engineering Achievements (The Workflow)

### 1\. Strict CRS Management & Spatial Integrity

- **The Problem:** Calculating land area or performing spatial buffers on unprojected WGS84 (EPSG:4326) geographic coordinates results in massive geometric distortions.
- **The Solution:** The pipeline immediately projects incoming data to the local **UTM Zone 43N (EPSG:32643)** Cartesian plane. All metric calculations (Plot Area in sq.m, 10m road access buffers) happen in UTM, ensuring strict mathematical accuracy.

### 2\. Automated OSM Infrastructure Enrichment

- Dynamically extracts building footprints and road networks via the Overpass API based on the convex hull of the input TP scheme.
- Utilizes **R-Tree spatial indexing** (gpd.sjoin) to rapidly intersect thousands of TP plots with infrastructure to determine is_built status and road_access.

### 3\. Serverless Elevation Processing (Google Earth Engine)

- **Zero-Disk Footprint:** Eliminates the need to download massive .tif files to local memory.
- Converts local vector data to ee.FeatureCollection and pushes the computation to Google's cloud. It utilizes the **Copernicus 30m Global DEM (GLO-30)** and executes combined ee.Reducer.mean() and ee.Reducer.minMax() algorithms on Google's clusters, returning only the final statistical metadata back to Python.

### 4\. Zero-Backend 3D Web Visualization

- Transforms the enriched 2D polygons into extruded 3D WebGL geometries using Pydeck.
- Exports a lightweight, standalone tp_3d_viewer.html that requires zero backend servers to render, making it instantly shareable with non-technical stakeholders.

## 📂 Project Structure

ahmedabad_tp_intelligence/  
├── data/  
│ ├── input/  
│ │ └── tp_scheme.geojson # Input TP Boundaries (WGS84)  
│ └── output/ # Auto-generated enriched layers & 3D HTML  
├── src/  
│ ├── \__init_\_.py  
│ ├── core/  
│ │ ├── config.py # Immutable Dataclasses for CRS and thresholds  
│ │ └── spatial_utils.py # Affine transformation utilities  
│ ├── extract/  
│ │ ├── osm_client.py # OSMnx API wrappers  
│ │ └── gee_client.py # Google Earth Engine API integration  
│ ├── transform/  
│ │ ├── enrichment.py # R-Tree Spatial joins (is_built, road_access)  
│ │ ├── elevation.py # Cloud-dispatched zonal stats  
│ │ └── geometry.py # UTM Area calculation & spatial validation  
│ └── visualize/  
│ └── deckgl_viewer.py # Pydeck 3D HTML generator  
├── main.py # The Orchestrator (Dependency Injection)  
├── template.py # Enterprise project scaffolder  
└── requirements.txt

## ⚙️ Installation & Execution

**1\. Clone the repository:**
```cmd
git clone [<https://github.com/YourUsername/urban-land-intelligence-pipeline.git\>](<https://github.com/YourUsername/urban-land-intelligence-pipeline.git>)  

cd urban-land-intelligence-pipeline
```

**2\. Setup isolated Python 3.10+ Environment:**
```cmd
python3.10 -m venv .venv  

\# On Windows:  
.venv\\Scripts\\activate  

\# On Mac/Linux:  
source .venv/bin/activate
```

**3\. Install Dependencies:**
```cmd
pip install -r requirements.txt
```

**4\. Authenticate Google Earth Engine:**

You must authenticate your machine with a Google Cloud Project to run the serverless elevation module.

```cmd
earthengine authenticate
```

**5\. Add Input Data & Execute:**

Ensure tp_scheme.geojson is placed in data/input/.

```cmd
python main.py
```
## 📈 Designing for City-Scale Automation (Beyond the Script)

To scale this pipeline from a single TP scheme to the entire state of Gujarat, the architecture should be migrated from a local script to a **Directed Acyclic Graph (DAG)** running on the cloud:

- **Event-Driven Ingestion:** Watch an AWS S3 bucket for new TP GeoJSON uploads to automatically trigger an **Apache Airflow** DAG.
- **Database Materialization:** Replace in-memory GeoPandas joins with an **Enterprise PostGIS** database, utilizing highly scalable ST_Intersects queries.
- **Serving Layer:** Serve the enriched vector data as dynamic Vector Tiles (.mvt) via an asynchronous **FastAPI** backend to an interactive React dashboard.

---
**Author:** Omkar Arvind Jadhav

_Geospatial Data Scientist & Cloud GIS Architect_ | [LinkedIn](https://www.google.com/search?q=https://www.linkedin.com/in/omkar-jadhav) | [Portfolio](https://www.google.com/search?q=%23)


earthengine authenticate --force
python -c "import ee; ee.Initialize(project='ee-omkarjadhavsrf'); print('GEE Cloud Connection Successful!')"
python main.py