import plotly.graph_objects as go
from plotly.colors import sequential

def make_choropleths(data, map_df):
    maps = []
    for column in data.columns:
        temp = data[column]

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
        maps.append(fig)
    return maps