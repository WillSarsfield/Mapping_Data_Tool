import plotly.graph_objects as go
from plotly.colors import sequential
import pandas as pd

def create_placeholder_fig():
    fig = go.Figure()
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        width=800,  # Match the width of your actual figure
        height=550,  # Match the height of your actual figure
        margin=dict(l=0, r=0, t=50, b=0),  # Reduce margins
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
    )
    return [fig]

def make_choropleths(data, map_df, geo_level, colorscale=sequential.Viridis[::-1]):
    maps = []
    for column in data.columns:
        temp = data[column]
        temp = (temp.astype(str).str.replace(r"[^\d.-]", "", regex=True))
        temp = pd.to_numeric(temp, errors="coerce")

        # Merge GeoDataFrame with data
        merged_df = map_df.merge(temp, on=geo_level)

        # Add the choropleth map
        fig = go.Figure(go.Choropleth(
            geojson=merged_df.__geo_interface__,
            featureidkey=f"properties.{geo_level}",  # Match with GeoJSON properties
            locations=merged_df[geo_level],  # Geographic identifiers in data
            z=merged_df[column],  # Use precomputed indices for color
            colorscale=colorscale,  # Reverse the Viridis colour scale
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

        if geo_level[:3] == 'itl':
            geo_title = geo_level.upper()
        elif geo_level == 'la':
            geo_title = 'Local Authority'
        elif geo_level == 'mca':
            geo_title = 'Combined Authority'

        fig.update_layout(
            title=f"Choropleth Map of {geo_title} regions: {column}",
            margin={"r":0,"t":50,"l":0,"b":0},  # Adjust margins
            height = 550,
            width = 800
        )
        maps.append(fig)
    return maps