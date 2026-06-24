"""
Copernicus Climate Data Store (CDS) — Soil Climate Service

Provides independent validation of soil conditions against ERA5-Land
reanalysis data (Copernicus C3S, ~9km resolution, 1950-present).

Variables implemented:
  stl1 — Soil Temperature Level 1 (0-7cm, Kelvin)
  swvl1 — Soil Water Volume Level 1 (0-7cm, m³/m³)

Impact on biochar permanence (Fdurable):
  Temperature: primary parameter in Isometric/Woolf 2021 equation
  Moisture:    high moisture (> 0.35) → increased microbial activity → faster decomposition
               very dry (< 0.10)   → increased fire risk → reversal risk

Dataset: ERA5-Land Monthly Means
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

# Threshold for flagging soil temperature divergence (°C)
DIVERGENCE_THRESHOLD_C = 2.0

# Soil moisture thresholds (m³/m³) for permanence risk assessment
# Reference: field capacity ~0.30-0.45, wilting point ~0.10-0.15
MOISTURE_HIGH_RISK   = 0.35   # > 0.35 → high microbial activity → faster decomposition
MOISTURE_MEDIUM_RISK = 0.20   # 0.20-0.35 → moderate risk
MOISTURE_FIRE_RISK   = 0.10   # < 0.10 → very dry → increased fire risk


def _round_grid(lat: float, lon: float) -> Tuple[float, float]:
    """Round coordinates to nearest ERA5-Land grid cell."""
    glat = round(round(lat / GRID_RES) * GRID_RES, 1)
    glon = round(round(lon / GRID_RES) * GRID_RES, 1)
    return glat, glon



# Location lookup — cidades específicas de projetos biochar + centróides de países
# Ordem: mais específico primeiro (cidades antes de países/regiões)
# Format: (regex_pattern, lat, lon)
_KNOWN_LOCATIONS = [

    # ── Projetos Puro.Earth conhecidos ────────────────────────────────────────
    (r"riberalta",                  -11.00,  -66.00),   # ExomadGreen — Bolivia
    (r"capelinha",                  -17.69,  -42.52),   # Aperam Bioenergia — MG
    (r"wakefield",                   43.60,  -70.66),   # Accend Wakefield — EUA
    (r"georgiana|georgia.*usa|georgia.*united",  32.16, -82.90),

    # ── Brasil — cidades e estados ────────────────────────────────────────────
    (r"nova\s*espe[rn]an[çc]a",    -22.90,  -43.17),
    (r"par[aá]\s*de\s*minas",      -19.87,  -44.61),
    (r"capelinha",                  -17.69,  -42.52),
    (r"minas\s*gerais|mg\b",        -18.50,  -44.00),
    (r"s[ãa]o\s*paulo",            -23.55,  -46.63),
    (r"mato\s*grosso",             -12.64,  -55.42),
    (r"par[aá]\b",                  -3.79,  -52.48),
    (r"bah[ií]a\b",               -12.96,  -38.51),
    (r"goi[aá]s\b",               -15.83,  -49.84),
    (r"rio\s*de\s*janeiro",        -22.91,  -43.17),
    (r"bras[ií]lia",               -15.78,  -47.93),
    (r"\bbrazil\b|brasil\b",       -14.24,  -51.93),   # centróide BR

    # ── América do Sul ────────────────────────────────────────────────────────
    (r"\bbolivia\b",               -16.29,  -63.59),
    (r"\bcolombia\b",                4.57,  -74.30),
    (r"\bperu\b",                   -9.19,  -75.02),
    (r"\bchile\b",                 -35.68,  -71.54),
    (r"\bargentina\b",             -38.42,  -63.62),
    (r"\becuador\b",                -1.83,  -78.18),
    (r"\bvenezuela\b",               6.42,  -66.59),
    (r"\bparaguay\b",              -23.44,  -58.44),
    (r"\buruguay\b",               -32.52,  -55.77),

    # ── América do Norte ──────────────────────────────────────────────────────
    (r"humboldt\s*county|scotia\s*,?\s*ca",  40.60, -124.10),
    (r"\boregon\b",                 44.00, -120.50),
    (r"washington\s*state",         47.40, -120.50),
    (r"\bcalifornia\b",             36.78, -119.42),
    (r"british\s*columbia",         53.73, -127.65),
    (r"\bcanada\b",                 56.13,  -106.35),
    (r"\bmexico\b|méxico\b",        23.63,  -102.55),
    (r"\busa\b|united\s*states|u\.s\.a",  37.09,  -95.71),

    # ── Europa ────────────────────────────────────────────────────────────────
    (r"\bfinland\b|finland",        64.00,   26.00),
    (r"\bnorway\b|norge",           64.56,   17.89),
    (r"\bsweden\b|sverige",         60.13,   18.64),
    (r"\bdenmark\b|danmark",        56.00,   10.00),
    (r"\bnetherlands\b|holland",    52.37,    4.89),
    (r"\bgermany\b|deutschland",    51.17,   10.45),
    (r"\baustria\b|österreich",     47.52,   14.55),
    (r"\bswitzerland\b|schweiz",    46.82,    8.23),
    (r"\bfrance\b|frankreich",      46.23,    2.21),
    (r"\buk\b|united\s*kingdom|england|britain",  52.36,  -1.17),
    (r"\bspain\b|españa",           40.46,   -3.75),
    (r"\bportugal\b",               39.40,   -8.22),
    (r"\bitaly\b|italia",           41.87,   12.57),
    (r"\bpoland\b|polska",          51.92,   19.14),
    (r"\bestonia\b",                58.60,   25.01),
    (r"\blatvia\b",                 56.88,   24.60),

    # ── África ────────────────────────────────────────────────────────────────
    (r"\bghana\b",                   7.95,   -1.02),
    (r"\bkenya\b",                  -0.02,   37.91),
    (r"\btanzania\b",               -6.37,   34.89),
    (r"\buganda\b",                  1.37,   32.29),
    (r"\bnigeria\b",                 9.08,    8.68),
    (r"\bsouth\s*africa\b",        -30.56,   22.94),

    # ── Ásia / Pacífico ───────────────────────────────────────────────────────
    (r"\bindia\b",                  20.59,   78.96),
    (r"\bindonesia\b",              -0.79,  113.92),
    (r"\bmalaysia\b",                4.21,  101.98),
    (r"\bthailand\b",               15.87,  100.99),
    (r"\bvietnam\b|viet\s*nam",     14.06,  108.28),
    (r"\bchina\b",                  35.86,  104.20),
    (r"\bjapan\b|japan",            36.20,  138.25),
    (r"\baustralia\b",             -25.27,  133.78),
    (r"\bnew\s*zealand\b",         -40.90,  174.89),
]


def _parse_coordinates(locations: Any) -> Optional[Tuple[float, float]]:
    """
    Extrai (lat, lon) de project.locations em múltiplos formatos:
      1. Coordenadas GPS decimais explícitas: "40.7128, -74.006"
      2. Coordenadas DMS: "11°01'S 66°04'W"
      3. Nome de cidade/região/país — lookup em _KNOWN_LOCATIONS
      4. Apenas país mencionado — centróide do país
    """
    if not locations:
        return None

    if isinstance(locations, list):
        text = " ".join(str(x) for x in locations)
    else:
        text = str(locations)

    text_lower = text.lower()

    # 1. GPS decimal: "lat, lon" ou "lat lon"
    m = re.search(r"(-?\d{1,3}\.\d+)[,\s]+(-?\d{1,3}\.\d+)", text)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon

    # 2. DMS pattern: "11°01'00\"S 66°04'00\"W" ou "11° 1' S, 66° 4' W"
    dms = re.search(
        r"(\d{1,3})[°\s]+(\d{1,2})'?\s*(?:(\d{1,2})[\"\s]*)?\s*([NS])"
        r"[,\s]+"
        r"(\d{1,3})[°\s]+(\d{1,2})'?\s*(?:(\d{1,2})[\"\s]*)?\s*([EW])",
        text, re.IGNORECASE
    )
    if dms:
        lat_d, lat_m = int(dms.group(1)), int(dms.group(2))
        lat_s = int(dms.group(3) or 0)
        lat = lat_d + lat_m/60 + lat_s/3600
        if dms.group(4).upper() == 'S':
            lat = -lat
        lon_d, lon_m = int(dms.group(5)), int(dms.group(6))
        lon_s = int(dms.group(7) or 0)
        lon = lon_d + lon_m/60 + lon_s/3600
        if dms.group(8).upper() == 'W':
            lon = -lon
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon

    # 3. Nome de cidade / região / país — lookup (mais específico primeiro)
    for pattern, lat, lon in _KNOWN_LOCATIONS:
        if re.search(pattern, text_lower):
            return lat, lon

    return None


def _query_era5_variable(
    variable: str,
    short_name: str,
    grid_lat: float,
    grid_lon: float,
    year: int,
) -> Dict[str, Any]:
    """
    Generic ERA5-Land query helper.
    Downloads one variable for all 12 months and returns the annual mean.
    Returns: {"mean_value": float, "monthly": list[float]} or {"error": str}
    """
    try:
        os.environ["CDSAPI_URL"] = COPERNICUS_URL
        os.environ["CDSAPI_KEY"] = COPERNICUS_API_KEY

        import cdsapi
        import xarray as xr
        import numpy as np
        import zipfile

        client = cdsapi.Client(quiet=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = os.path.join(tmpdir, f"{short_name}.nc")

            client.retrieve(
                "reanalysis-era5-land-monthly-means",
                {
                    "product_type": "monthly_averaged_reanalysis",
                    "variable":     variable,
                    "year":         str(year),
                    "month":        [f"{m:02d}" for m in range(1, 13)],
                    "time":         "00:00",
                    "area": [
                        grid_lat + GRID_RES, grid_lon - GRID_RES,
                        grid_lat - GRID_RES, grid_lon + GRID_RES,
                    ],
                    "format": "netcdf",
                },
                outfile,
            )

            # Handle ZIP wrapper
            actual_nc = outfile
            if zipfile.is_zipfile(outfile):
                with zipfile.ZipFile(outfile, "r") as zf:
                    nc_names = [n for n in zf.namelist() if n.endswith(".nc")]
                    if nc_names:
                        actual_nc = os.path.join(tmpdir, nc_names[0])
                        zf.extract(nc_names[0], tmpdir)

            ds = xr.open_dataset(actual_nc, engine="netcdf4")
            arr = ds[short_name].values  # shape: (12, lat, lon)

            # Monthly spatial means (filter NaN = ocean pixels)
            monthly = []
            for t in range(arr.shape[0]):
                slab = arr[t].flatten()
                valid = slab[~np.isnan(slab)]
                if len(valid) > 0:
                    monthly.append(float(valid.mean()))
            ds.close()

        if not monthly:
            return {"error": f"Todos NaN para {variable} — coordenadas no oceano?"}

        return {
            "mean_value": float(sum(monthly) / len(monthly)),
            "monthly":    [round(v, 4) for v in monthly],
            "n_months":   len(monthly),
        }

    except ImportError as e:
        return {"error": f"Dependência faltando: {e}"}
    except Exception as e:
        return {"error": f"Erro CDS ({variable}): {e}"}


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
        raw = _query_era5_variable(
            variable="soil_temperature_level_1",
            short_name="stl1",
            grid_lat=grid_lat, grid_lon=grid_lon, year=year,
        )
        if "error" in raw:
            return raw

        # stl1 in Kelvin → Celsius
        temp_celsius = round(raw["mean_value"] - 273.15, 2)

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


def get_soil_moisture(
    lat: float,
    lon: float,
    year: Optional[int] = None,
    db_conn=None,
) -> Dict[str, Any]:
    """
    Return the annual average volumetric soil water content (m³/m³) at 0-7cm depth.

    ERA5-Land variable: swvl1 (soil_volumetric_water_content_level_1)
    Range: 0.0 (bone dry) → ~0.45 (saturated / field capacity)

    Permanence risk thresholds:
      > 0.35  → HIGH microbial activity → faster biochar decomposition
      0.20-0.35 → MODERATE risk
      < 0.10  → FIRE risk (very dry conditions)
    """
    if not COPERNICUS_API_KEY:
        return {"error": "COPERNICUS_API_KEY não configurada."}

    if year is None:
        year = datetime.now().year - 1

    grid_lat, grid_lon = _round_grid(lat, lon)
    cache_key = f"era5land_swvl1_{grid_lat}_{grid_lon}_{year}"

    # ── Check cache ────────────────────────────────────────────────────────
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
            pass

    # ── Query CDS ──────────────────────────────────────────────────────────
    raw = _query_era5_variable(
        variable="volumetric_soil_water_layer_1",
        short_name="swvl1",
        grid_lat=grid_lat, grid_lon=grid_lon, year=year,
    )
    if "error" in raw:
        return raw

    moisture = round(raw["mean_value"], 4)

    # Permanence risk classification
    if moisture > MOISTURE_HIGH_RISK:
        risk = "high"
        risk_note = (
            f"Umidade do solo {moisture:.3f} m³/m³ > {MOISTURE_HIGH_RISK} — "
            "alta atividade microbiana esperada, pode acelerar decomposição do biochar."
        )
    elif moisture < MOISTURE_FIRE_RISK:
        risk = "fire"
        risk_note = (
            f"Umidade do solo {moisture:.3f} m³/m³ < {MOISTURE_FIRE_RISK} — "
            "condições muito secas, risco elevado de incêndio e reversão."
        )
    elif moisture < MOISTURE_MEDIUM_RISK:
        risk = "low"
        risk_note = f"Umidade do solo {moisture:.3f} m³/m³ — condições favoráveis à permanência do biochar."
    else:
        risk = "medium"
        risk_note = f"Umidade do solo {moisture:.3f} m³/m³ — risco moderado de degradação microbiana."

    result = {
        "moisture_m3_m3":  moisture,
        "permanence_risk": risk,
        "risk_note":       risk_note,
        "source":          "c3s_era5_land",
        "year":            year,
        "grid_lat":        grid_lat,
        "grid_lon":        grid_lon,
        "variable":        "swvl1 (volumetric_soil_water_layer_1)",
        "depth_cm":        "0-7",
        "retrieved_at":    datetime.utcnow().isoformat() + "Z",
    }

    # ── Cache ──────────────────────────────────────────────────────────────
    if db_conn:
        try:
            with db_conn:
                with db_conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO ca_copernicus_cache (cache_key, data, created_at)
                           VALUES (%s, %s, NOW())
                           ON CONFLICT (cache_key) DO UPDATE SET data = EXCLUDED.data""",
                        (cache_key, json.dumps(result)),
                    )
        except Exception:
            pass

    return result


def validate_project_soil_conditions(
    project_data: Dict[str, Any],
    db_conn=None,
) -> Dict[str, Any]:
    """
    Comprehensive soil conditions validator using both stl1 (temperature)
    and swvl1 (moisture) from ERA5-Land.

    Returns combined assessment for permanence risk scoring.
    """
    storage = project_data.get("storage", {})
    soil    = storage.get("soil", {})
    proj    = project_data.get("project", {})

    reported_temp = soil.get("annual_avg_temp_celsius")
    locations     = proj.get("locations")
    coords        = _parse_coordinates(locations)

    if not coords:
        return {
            "status":  "no_coordinates",
            "message": "Coordenadas GPS do projeto não disponíveis para validação via Copernicus.",
            "temperature": None,
            "moisture":    None,
        }

    lat, lon = coords

    # ── Query both variables in parallel (sequential for simplicity) ───────
    temp_result     = get_soil_temperature(lat, lon, db_conn=db_conn)
    moisture_result = get_soil_moisture(lat, lon, db_conn=db_conn)

    c3s_temp     = temp_result.get("temp_celsius")
    c3s_moisture = moisture_result.get("moisture_m3_m3")
    moist_risk   = moisture_result.get("permanence_risk", "unknown")

    # ── Temperature validation ─────────────────────────────────────────────
    if c3s_temp is not None and reported_temp is not None:
        divergence = abs(float(reported_temp) - c3s_temp)
        temp_status  = "validated" if divergence <= DIVERGENCE_THRESHOLD_C else "divergence_flag"
        temp_message = (
            f"Temperatura: reportada {reported_temp}°C vs C3S {c3s_temp}°C "
            f"(divergência {divergence:.1f}°C{'✓' if temp_status == 'validated' else ' ⚠ excede threshold'})"
        )
    elif c3s_temp is not None:
        temp_status  = "c3s_only"
        temp_message = f"Temperatura do solo C3S: {c3s_temp}°C (não reportada pelo projeto)"
    else:
        temp_status  = "api_error"
        temp_message = temp_result.get("error", "Erro desconhecido")

    # ── Overall permanence risk ────────────────────────────────────────────
    risk_flags = []
    if temp_status == "divergence_flag":
        risk_flags.append("temperatura_diverge")
    if moist_risk == "high":
        risk_flags.append("umidade_alta_degradacao")
    if moist_risk == "fire":
        risk_flags.append("umidade_baixa_incendio")

    overall_risk = "flagged" if risk_flags else "clear"

    return {
        "status":       overall_risk,
        "risk_flags":   risk_flags,
        "temperature": {
            "c3s_temp":      c3s_temp,
            "reported_temp": reported_temp,
            "status":        temp_status,
            "message":       temp_message,
        },
        "moisture": {
            "c3s_moisture":      c3s_moisture,
            "permanence_risk":   moist_risk,
            "risk_note":         moisture_result.get("risk_note", ""),
        },
        "lat":    lat,
        "lon":    lon,
        "source": "ERA5-Land C3S (Copernicus Climate Change Service)",
    }


# Backward-compatible alias
def validate_project_soil_temp(project_data, db_conn=None):
    """Legacy alias → calls validate_project_soil_conditions."""
    return validate_project_soil_conditions(project_data, db_conn=db_conn)
