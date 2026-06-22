"""
Copernicus Climate Data Store (CDS) — Soil Temperature Service

Provides independent validation of project-reported soil temperatures
against ERA5-Land reanalysis data (Copernicus C3S, ~9km resolution).

This enables the "independent data validation" that distinguishes
professional rating agencies (Sylvera, BeZero) from document-only audits.

Dataset: ERA5-Land Monthly Means
Variable: soil_temperature_level_1 (0-7cm depth, Kelvin)
Source: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-monthly-means
"""

import json
import os
import re
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from backend.config import COPERNICUS_API_KEY, COPERNICUS_URL

# Cache grid resolution: 0.1° ≈ 11km (matches ERA5-Land native resolution)
GRID_RES = 0.1

# Threshold for flagging divergence (°C)
DIVERGENCE_THRESHOLD_C = 2.0


def _round_grid(lat: float, lon: float) -> Tuple[float, float]:
    """Round coordinates to nearest ERA5-Land grid cell."""
    glat = round(round(lat / GRID_RES) * GRID_RES, 1)
    glon = round(round(lon / GRID_RES) * GRID_RES, 1)
    return glat, glon


def _parse_coordinates(locations: Any) -> Optional[Tuple[float, float]]:
    """
    Extract (lat, lon) from project.locations in various formats:
      - List: ["40.7128, -74.006"] or ["40.7128,-74.006"]
      - String: "40.7128, -74.006"
      - GPS patterns from addresses
    """
    if not locations:
        return None

    # Normalise to string
    if isinstance(locations, list):
        text = " ".join(str(x) for x in locations)
    else:
        text = str(locations)

    # GPS decimal degrees pattern — 1+ decimal digit
    m = re.search(r"(-?\d{1,3}\.\d+)[,\s]+(-?\d{1,3}\.\d+)", text)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon

    # DMS pattern (e.g. "40°42'46\"N 74°0'22\"W") — not implemented yet
    return None


def get_soil_temperature(
    lat: float,
    lon: float,
    year: Optional[int] = None,
    db_conn=None,        # psycopg2 connection for cache
) -> Dict[str, Any]:
    """
    Return the annual average soil temperature (°C) at the given coordinates.

    Flow:
    1. Round to ERA5-Land grid cell
    2. Check Supabase cache (ca_copernicus_cache table)
    3. If miss: download from CDS API → extract mean → cache result

    Returns dict with keys:
      temp_celsius, source, year, grid_lat, grid_lon, dataset, variable
      OR: error (str) if something went wrong
    """
    if not COPERNICUS_API_KEY:
        return {"error": "COPERNICUS_API_KEY não configurada. Adicione ao .env e ao Render."}

    if year is None:
        year = datetime.now().year - 1  # Use previous complete year

    grid_lat, grid_lon = _round_grid(lat, lon)
    cache_key = f"era5land_stl1_{grid_lat}_{grid_lon}_{year}"

    # ── 1. Check cache ──────────────────────────────────────────────────────
    if db_conn:
        try:
            with db_conn.cursor() as cur:
                cur.execute(
                    "SELECT data FROM ca_copernicus_cache WHERE cache_key = %s",
                    (cache_key,),
                )
                row = cur.fetchone()
                if row:
                    cached = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    return {**cached, "source": "cache"}
        except Exception:
            pass  # Cache miss — proceed to API

    # ── 2. Download from Copernicus CDS ────────────────────────────────────
    try:
        os.environ["CDSAPI_URL"] = COPERNICUS_URL
        os.environ["CDSAPI_KEY"] = COPERNICUS_API_KEY

        import cdsapi
        import xarray as xr

        client = cdsapi.Client(quiet=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = os.path.join(tmpdir, "stl1.nc")

            client.retrieve(
                "reanalysis-era5-land-monthly-means",
                {
                    "product_type": "monthly_averaged_reanalysis",
                    "variable": "soil_temperature_level_1",
                    "year": str(year),
                    "month": [f"{m:02d}" for m in range(1, 13)],
                    "time": "00:00",
                    "area": [
                        grid_lat + GRID_RES,
                        grid_lon - GRID_RES,
                        grid_lat - GRID_RES,
                        grid_lon + GRID_RES,
                    ],
                    "format": "netcdf",
                },
                outfile,
            )

            # CDS may return a zip containing the .nc file
            import zipfile
            actual_nc = outfile
            if zipfile.is_zipfile(outfile):
                with zipfile.ZipFile(outfile, "r") as zf:
                    nc_names = [n for n in zf.namelist() if n.endswith(".nc")]
                    if nc_names:
                        actual_nc = os.path.join(tmpdir, nc_names[0])
                        zf.extract(nc_names[0], tmpdir)

            import numpy as np
            ds = xr.open_dataset(actual_nc, engine="netcdf4")

            # Variable is 'stl1', values in Kelvin
            # Filter NaN (ocean/no-data pixels) before averaging
            vals = ds["stl1"].values.flatten()
            valid = vals[~np.isnan(vals)]
            if len(valid) == 0:
                ds.close()
                return {"error": "Todos os pixels NaN — coordenadas podem estar no oceano ou sem cobertura ERA5-Land."}
            stl1_k = float(valid.mean())
            ds.close()

        temp_celsius = round(stl1_k - 273.15, 2)

        result = {
            "temp_celsius":   temp_celsius,
            "source":         "c3s_era5_land",
            "year":           year,
            "grid_lat":       grid_lat,
            "grid_lon":       grid_lon,
            "dataset":        "reanalysis-era5-land-monthly-means",
            "variable":       "soil_temperature_level_1",
            "depth_cm":       "0-7",
            "retrieved_at":   datetime.utcnow().isoformat() + "Z",
        }

        # ── 3. Save to cache ─────────────────────────────────────────────────
        if db_conn:
            try:
                with db_conn:
                    with db_conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO ca_copernicus_cache (cache_key, data, created_at)
                            VALUES (%s, %s, NOW())
                            ON CONFLICT (cache_key) DO UPDATE SET data = EXCLUDED.data
                            """,
                            (cache_key, json.dumps(result)),
                        )
            except Exception:
                pass  # Cache write failure is non-fatal

        return result

    except ImportError as e:
        return {"error": f"Dependência faltando: {e}. Execute: pip install cdsapi xarray netcdf4"}
    except Exception as e:
        return {"error": f"Erro ao consultar Copernicus CDS: {e}"}


def validate_project_soil_temp(
    project_data: Dict[str, Any],
    db_conn=None,
) -> Dict[str, Any]:
    """
    High-level validator: extract project coordinates + reported temperature,
    query C3S, compare, and return a structured validation result.

    Used by eval_durability_soil_temp_v1() in operational mode.
    """
    storage  = project_data.get("storage", {})
    soil     = storage.get("soil", {})
    proj     = project_data.get("project", {})

    reported_temp = soil.get("annual_avg_temp_celsius")
    locations     = proj.get("locations")

    coords = _parse_coordinates(locations)

    if not coords:
        return {
            "status": "no_coordinates",
            "message": "Coordenadas GPS do projeto não disponíveis para validação via Copernicus.",
            "c3s_temp": None,
            "reported_temp": reported_temp,
        }

    lat, lon = coords
    c3s_result = get_soil_temperature(lat, lon, db_conn=db_conn)

    if "error" in c3s_result:
        return {
            "status": "api_error",
            "message": c3s_result["error"],
            "c3s_temp": None,
            "reported_temp": reported_temp,
        }

    c3s_temp = c3s_result["temp_celsius"]

    # Assess divergence
    if reported_temp is not None:
        divergence = abs(float(reported_temp) - c3s_temp)
        if divergence <= DIVERGENCE_THRESHOLD_C:
            status = "validated"
            message = (
                f"Temperatura reportada ({reported_temp}°C) é consistente com "
                f"ERA5-Land C3S ({c3s_temp}°C). Divergência: {divergence:.1f}°C ≤ {DIVERGENCE_THRESHOLD_C}°C."
            )
        else:
            status = "divergence_flag"
            message = (
                f"Temperatura reportada ({reported_temp}°C) diverge {divergence:.1f}°C "
                f"da ERA5-Land C3S ({c3s_temp}°C). Threshold: {DIVERGENCE_THRESHOLD_C}°C. "
                f"Revisar método de obtenção da temperatura do solo."
            )
    else:
        status = "c3s_only"
        message = (
            f"Temperatura do solo não reportada pelo projeto. "
            f"ERA5-Land C3S indica {c3s_temp}°C para as coordenadas do projeto."
        )

    return {
        "status":        status,
        "message":       message,
        "c3s_temp":      c3s_temp,
        "reported_temp": reported_temp,
        "divergence_c":  abs(float(reported_temp) - c3s_temp) if reported_temp is not None else None,
        "lat":           lat,
        "lon":           lon,
        "c3s_source":    c3s_result.get("source"),
        "c3s_year":      c3s_result.get("year"),
    }
