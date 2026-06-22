import sys, os, tempfile, zipfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

os.environ["COPERNICUS_API_KEY"] = "8bd9e97f-61ca-4ea4-9edd-f0a0e799fc53"
os.environ["CDSAPI_URL"] = "https://cds.climate.copernicus.eu/api"
os.environ["CDSAPI_KEY"] = "8bd9e97f-61ca-4ea4-9edd-f0a0e799fc53"

import cdsapi
import xarray as xr
import numpy as np

# Scotia, CA (Pacific Biochar location) — mais inland que 40.8/-124.1
# Scotia é a ~40.49°N, -124.10°W mas a terra está por volta de -124.05°W
LAT, LON = 40.5, -124.0   # Ligeiramente mais ao interior

print(f"Testando coordenadas: lat={LAT}, lon={LON}")
print("Baixando ERA5-Land...")

client = cdsapi.Client(quiet=True)

with tempfile.TemporaryDirectory() as tmpdir:
    outfile = os.path.join(tmpdir, "stl1.nc")
    client.retrieve(
        "reanalysis-era5-land-monthly-means",
        {
            "product_type": "monthly_averaged_reanalysis",
            "variable": "soil_temperature_level_1",
            "year": "2023",
            "month": ["01","06","12"],   # 3 meses para teste rápido
            "time": "00:00",
            "area": [LAT + 0.2, LON - 0.2, LAT - 0.2, LON + 0.2],
            "format": "netcdf",
        },
        outfile,
    )

    # Handle ZIP
    actual_nc = outfile
    if zipfile.is_zipfile(outfile):
        with zipfile.ZipFile(outfile, "r") as zf:
            nc_names = [n for n in zf.namelist() if n.endswith(".nc")]
            print(f"ZIP contém: {zf.namelist()}")
            if nc_names:
                actual_nc = os.path.join(tmpdir, nc_names[0])
                zf.extract(nc_names[0], tmpdir)

    ds = xr.open_dataset(actual_nc, engine="netcdf4")
    print("\nDataset info:")
    print(f"  Variáveis: {list(ds.data_vars)}")
    print(f"  Dimensões: {dict(ds.dims)}")
    print(f"  Coords: {list(ds.coords)}")

    # Tentar a variável
    var_name = None
    for candidate in ["stl1", "soil_temperature_level_1", "STL1"]:
        if candidate in ds.data_vars:
            var_name = candidate
            break

    if var_name:
        vals = ds[var_name].values
        print(f"\n  Variável '{var_name}': shape={vals.shape}")
        print(f"  Valores: {vals.flatten()}")
        # Filter NaN
        valid = vals[~np.isnan(vals)]
        if len(valid) > 0:
            mean_k = float(valid.mean())
            print(f"  Média (válidos): {mean_k:.2f} K = {mean_k - 273.15:.2f} °C")
        else:
            print("  Todos NaN — coordenadas no oceano ou sem dados")
    else:
        print(f"  Nenhuma variável de temperatura do solo encontrada. Vars: {list(ds.data_vars)}")

    ds.close()
