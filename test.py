import geopandas as gpd
import pandas as pd

# Load the GeoJSON files
itl3_shapes_df_2025 = gpd.read_file("src/International_Territorial_Level_3_(January_2025)_Boundaries_UK_BUC_V2.geojson")
itl3_shapes_df_2021 = gpd.read_file("src/International_Territorial_Level_3_(January_2021)_UK_BUC_V3.geojson")

# Ensure both datasets have a valid CRS
if itl3_shapes_df_2025.crs is None:
    itl3_shapes_df_2025.set_crs(epsg=27700, inplace=True)  # Adjust CRS if needed

if itl3_shapes_df_2021.crs is None:
    itl3_shapes_df_2021.set_crs(itl3_shapes_df_2025.crs, inplace=True)

# Find missing region codes from 2021 that are not in 2025
missing_codes = set(itl3_shapes_df_2021["ITL321CD"]) - set(itl3_shapes_df_2025["ITL325CD"])

# Ensure missing regions have the correct CRS before merging
missing_regions = itl3_shapes_df_2021[itl3_shapes_df_2021["ITL321CD"].isin(missing_codes)].copy()

if missing_regions.crs != itl3_shapes_df_2025.crs:
    missing_regions = missing_regions.to_crs(itl3_shapes_df_2025.crs)

# Rename columns to match 2025 structure
column_mapping = {
    "ITL321CD": "ITL325CD",
    "ITL321NM": "ITL325NM",
    "SHAPE_Area": "Shape__Area",
    "SHAPE_Length": "Shape__Length",
    "OBJECTID": "FID",  # Assuming FID is an identifier
}

missing_regions.rename(columns=column_mapping, inplace=True)

# Add missing columns with default values (None for unknown values)
for col in itl3_shapes_df_2025.columns:
    if col not in missing_regions.columns:
        missing_regions[col] = None

# Ensure missing regions have updated area and length calculations
projected_crs = "EPSG:27700"  # British National Grid (meters)
missing_regions_projected = missing_regions.to_crs(projected_crs)

# Compute correct area and length in meters
missing_regions["Shape__Area"] = missing_regions_projected.geometry.area
missing_regions["Shape__Length"] = missing_regions_projected.geometry.length


# Ensure columns are in the same order
missing_regions = missing_regions[itl3_shapes_df_2025.columns]

# Append missing regions to the 2025 dataset and reindex
itl3_shapes_df_updated = pd.concat([itl3_shapes_df_2025, missing_regions], ignore_index=True)

# Ensure the index structure matches
itl3_shapes_df_updated.index = range(len(itl3_shapes_df_updated))

# Drop 'GlobalID' column if it exists
if "GlobalID" in itl3_shapes_df_updated.columns:
    itl3_shapes_df_updated.drop(columns=["GlobalID"], inplace=True)

# Save the updated map as a new GeoJSON file
itl3_shapes_df_updated.to_file("src/International_Territorial_Level_3_Updated.geojson", driver="GeoJSON")

print("Updated GeoJSON file saved successfully.")

# Load the CSV files and select relevant columns
itlmapping_new = pd.read_csv("src/la-itlmapping.csv")[["itl1", "itl1name", "itl2", "itl2name", "itl3", "itl3name"]]
itlmapping_old = pd.read_csv("src/itlmapping.csv")[["itl1", "itl1name", "itl2", "itl2name", "itl3", "itl3name"]]

# Find ITL3 codes that are in the old mapping but missing in the new one
missing_itl3_codes = set(itlmapping_old["itl3"]) - set(itlmapping_new["itl3"])

# Extract missing rows from the old mapping
missing_rows = itlmapping_old[itlmapping_old["itl3"].isin(missing_itl3_codes)].copy()

# Append missing rows to the new mapping
itlmapping_updated = pd.concat([itlmapping_new, missing_rows], ignore_index=True)

# Save the updated mapping
itlmapping_updated.to_csv("src/itlmapping-updated.csv", index=False)

print("Updated mapping file saved successfully.")

