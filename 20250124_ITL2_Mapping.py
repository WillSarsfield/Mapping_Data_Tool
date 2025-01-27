import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from plotly.colors import sequential

# Read map file
df_itl3 = gpd.read_file('International_Territorial_Level_3_(January_2021)_UK_BUC_V3.geojson')

# Simplify map
# Merge ITL3 regions together to make ITL1
itl_mapping = pd.read_csv('itlmapping.csv')[['itl2', 'itl2name', 'itl3']]
map_df = df_itl3.rename(columns={'ITL321CD': 'itl3'})
map_df = map_df.merge(itl_mapping, how='left', on='itl3')
map_df = map_df.groupby(['itl2', 'itl2name']).geometry.apply(lambda x: x.union_all()).reset_index()
map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=df_itl3.crs)
map_df['geometry'] = map_df['geometry'].simplify(0.0001, preserve_topology=True)
print(map_df['itl2name'])

# Load data
comparisons = pd.read_csv('map_data.csv').set_index('itl2')
for column in comparisons.columns:
    temp = comparisons[column]
    print(column)

    # Merge GeoDataFrame with data
    merged_df = map_df.merge(temp, on='itl2')

    # Add the choropleth map
    fig = go.Figure(go.Choropleth(
        geojson=merged_df.__geo_interface__,
        featureidkey="properties.itl2",  # Match with GeoJSON properties
        locations=merged_df['itl2'],  # Geographic identifiers in data
        z=merged_df[column],  # Use precomputed indices for color
        colorscale=sequential.Viridis[::-1],  # Reverse the Viridis colour scale
        colorbar=dict(
        tickformat=".0%"  # Add percent sign to the colour scale
    ),
        showscale=True  # Show the colour scale
    ))

    # Update layout
    fig.update_geos(
        resolution=50,
        projection_type= "mercator", #orthographic", #play with this, note that for some projection types, the height/width ratio is fixed    
        framewidth = 1,
        showframe = False, #shows border around subplots
        coastlinecolor = '#d9d9d9',
        fitbounds="locations",  
        visible=False  # Hide default geographic features              
        )

    fig.update_layout(
        title=f"Choropleth Map of ITL2 regions: {column}",
        margin={"r":0,"t":50,"l":0,"b":0},  # Adjust margins
    )

    fig.show()