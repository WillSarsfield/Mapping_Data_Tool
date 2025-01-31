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

def make_choropleths(data, map_df, geo_level, colorscale=sequential.Viridis[::-1], show_missing_values=False, units='%', dp=2):
    maps = []
    if units == '%':
        data_format = f".{dp}%"  # Significant figures with '%' appended
        unit = ''
    elif units == 'None':
        data_format = f".{dp}f"  # Significant figures with no unit
        unit = ''
    else:
        data_format = f".{dp}f"  # Units before the value
        unit = units
    
    for column in data.columns:
        temp = data[column]
        temp = (temp.astype(str).str.replace(r"[^\d.-]", "", regex=True))
        temp = pd.to_numeric(temp, errors="coerce")

        hovertemplate = '%{location}<br>' + column + f': {unit}'+'%{z:' + data_format + '}<extra></extra>'

        # Merge GeoDataFrame with data
        merged_df = map_df.merge(temp, on=geo_level, how='left')

        if geo_level == 'mca':
            non_mca = merged_df[merged_df['region_type'] == 'non_mca'].copy()
            mca = merged_df[merged_df['region_type'] == 'mca'].copy()
            
            # Show MCA regions
            fig = go.Figure(go.Choropleth(
                geojson=mca.__geo_interface__,
                featureidkey="id",  # Changed from properties.mca
                locations=mca.index,  # Using index instead of mca column
                z=mca[column],
                colorscale=colorscale,
                colorbar=dict(
                    tickformat=data_format, # Add percent sign to the colour scale
                    tickprefix = unit
                ),
                showscale=True,
                name='MCA Regions',
                hovertemplate=hovertemplate
            ))

            # If show_missing_values is True, add trace to show non-MCA regions in light grey
            if not show_missing_values:
                fig.add_trace(go.Choropleth(
                            geojson=non_mca.__geo_interface__,
                            featureidkey="id",  # Changed from properties.mca
                            locations=non_mca.index,  # Using index instead of mca column
                            z=non_mca[column].fillna(0),  # Fill NA with 0 for consistent coloring
                            colorscale=[[0, '#e0e0e0'], [1, '#e0e0e0']],  # Light grey
                            showscale=False,
                            name='Non-MCA Regions',
                            hovertemplate='%{location}<extra></extra>'
                        ))

        else:  # If not MCA data
            fig = go.Figure(go.Choropleth(
                geojson=merged_df.__geo_interface__,
                featureidkey=f"properties.{geo_level}",  # Match with GeoJSON properties
                locations=merged_df[geo_level],  # Geographic identifiers in data
                z=merged_df[column],  # Use precomputed indices for color
                colorscale=colorscale,  # Reverse the Viridis colour scale
                colorbar=dict(
                    tickformat=data_format, # Add percent sign to the colour scale
                    tickprefix = unit
                ),
                showscale=True,  # Show the colour scale
                hovertemplate='%{location}<br>' +
                            column + ': %{z:.1%}<extra></extra>'
            ))
            
            if not show_missing_values:
                last_col = merged_df.columns[-1]
                missing_values_df = merged_df[merged_df[last_col].isna()]
                fig.add_trace(go.Choropleth(
                    geojson=missing_values_df.__geo_interface__,
                    featureidkey=f"properties.{geo_level}",  # Match with GeoJSON properties
                    locations=missing_values_df[geo_level],  # Geographic identifiers in data
                    z=missing_values_df[column].fillna(0),  # Fill NA with 0 for consistent coloring
                    colorscale=[[0, '#e0e0e0'], [1, '#e0e0e0']],  # Light grey
                    showscale=False,  # Show the colour scale
                    hovertemplate=hovertemplate
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