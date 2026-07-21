import cdsapi
import xarray as xr
import json
import numpy as np

print("Connecting to CDS API...")
client = cdsapi.Client()

dataset = "reanalysis-era5-pressure-levels"
request = {
    "product_type": ["reanalysis"],
    "variable": [
        "geopotential",
        "relative_humidity",
        "specific_rain_water_content",
        "temperature",
        "u_component_of_wind",
        "v_component_of_wind"
    ],
    "month": ["06"], 
    "day": [
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", 
        "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", 
        "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"
    ],
    "time": [
        "00:00", "01:00", "02:00", "03:00", "04:00", "05:00",
        "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
        "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"
    ],
    "pressure_level": ["850"],
    "data_format": "netcdf",
    "download_format": "unarchived"
}

output_file = "monthly_data.nc"
print("Downloading data (this may take a while)...")
client.retrieve(dataset, request, output_file)

print("Processing NetCDF file...")
ds = xr.open_dataset(output_file)

# Align longitudes for standard web mapping (0 to 360)
ds = ds.assign_coords(longitude=(ds.longitude % 360)).sortby('longitude')

# Extract ONLY the first time step (index 0) for U and V wind to keep the web map fast
u_wind = ds['u'].values[0, 0, :, :] 
v_wind = ds['v'].values[0, 0, :, :]

# Clean up invalid data points
u_wind = np.nan_to_num(u_wind, nan=0.0)
v_wind = np.nan_to_num(v_wind, nan=0.0)

print("Formatting JSON for Leaflet...")
header = {
    "lo1": float(ds.longitude.min()),
    "la1": float(ds.latitude.max()),
    "dx": float(abs(ds.longitude[1] - ds.longitude[0])),
    "dy": float(abs(ds.latitude[0] - ds.latitude[1])),
    "nx": int(len(ds.longitude)),
    "ny": int(len(ds.latitude)),
    "refTime": str(ds.valid_time.values[0])
}

output_json = [
    {
        "header": {**header, "parameterCategory": 2, "parameterNumber": 2},
        "data": u_wind.flatten().tolist()
    },
    {
        "header": {**header, "parameterCategory": 2, "parameterNumber": 3},
        "data": v_wind.flatten().tolist()
    }
]

with open("data.json", "w") as f:
    json.dump(output_json, f)

print("Processing complete. Saved to data.json")
