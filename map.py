import plotly.graph_objects as go
from plotly.colors import sequential
import pandas as pd
import geopandas as gpd

pd.set_option('future.no_silent_downcasting', True)  # Prevents deprecation warning from Pandas when using fillna

# Assigning each value to a bin
def assign_bin(value, thresholds):
    for i in range(len(thresholds) - 1):
        if thresholds[i] <= value < thresholds[i + 1]:
            return i
    return len(thresholds) - 2  # For values equal to the max threshold

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

def wrap_title(title, max_length=100):
    # Split title into words
    words = title.split()
    
    # Initialize variables
    wrapped_title = ""
    current_line = ""
    
    # Loop through words and split them into lines
    for word in words:
        if len(current_line + " " + word) <= max_length:  # Check if the word fits in the current line
            current_line += " " + word if current_line else word
        else:
            # If it doesn't fit, add the current line to wrapped_title and start a new line with <br>
            wrapped_title += current_line + "<br>"
            current_line = word
    
    # Add the last line to the wrapped_title
    wrapped_title += current_line
    
    return wrapped_title

def make_choropleths(data, map_df, geo_level, colorscale=sequential.Viridis[::-1], show_missing_values=False, units='%', dp=2, thresholds=[], height=550, index=0):
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

    if len(thresholds) > 0:
        colorscale = [[i / (len(colorscale) - 1), color] for i, color in enumerate(colorscale)]
    
    column = data.columns[index]
    temp = data[column]
    temp = (temp.astype(str).str.replace(r"[^\d.-]", "", regex=True))
    temp = pd.to_numeric(temp, errors="coerce")

    hovertemplate = '%{text}<br>' + column + f': {unit}'+'%{customdata[0]:' + data_format + '}<extra></extra>'
    if geo_level == 'mca':
        # Merge GeoDataFrame with data
        merged_df = map_df.merge(temp, on=geo_level, how='left')
    else:
        # Merge GeoDataFrame with data
        merged_df = map_df.merge(temp, on=geo_level, how='left').dropna()

    if len(thresholds) > 0:
        inc_thresholds = thresholds.copy()
        inc_thresholds[0] -= (10 ** -dp)
        inc_thresholds[-1] += (10 ** -dp)
        merged_df['category'] = pd.cut(
            merged_df[column],
            bins=inc_thresholds,
            labels=list(range(len(colorscale)))
        )
        metric = 'category'
    else:
        metric = column

    if geo_level == 'mca':
        non_mca = merged_df[merged_df['region_type'] == 'non_mca'].copy()
        mca = merged_df[merged_df['region_type'] == 'mca'].copy()
        
        # Show MCA regions
        fig = go.Figure(go.Choropleth(
            geojson=mca.__geo_interface__,
            featureidkey="id",  # Changed from properties.mca
            locations=mca.index,  # Using index instead of mca column
            z=mca[metric],
            text=mca['region'], # Used to show the region name in the hovertemplate
            colorscale=colorscale,
            colorbar=dict(
                tickformat=data_format, # Add percent sign to the colour scale
                tickprefix = unit  # Adds the unit (£/$/€) to the colour scale
            ),
            showscale=len(thresholds) == 0,
            name='MCA Regions',
            customdata=merged_df[[column]],
            hovertemplate=hovertemplate
        ))

        # If show_missing_values is True, add trace to show non-MCA regions in light grey
        if not show_missing_values:
            last_col = mca.columns[-1]
            # Store missing data from MCA dataframe
            missing_values_df = mca[mca[last_col].isna()]
            # Merge missing data with non-mca data
            non_mca = pd.concat([non_mca, missing_values_df]).reset_index(drop=True)
            # Merge geometries of missing MCA regions and non-MCA regions
            gdf = gpd.GeoDataFrame(non_mca, geometry="geometry", crs="EPSG:4326")
            merged_geometry = gdf.geometry.unary_union
            non_mca = gpd.GeoDataFrame({
                "mca": ["all_regions"], 
                "mcaname": ["All Regions"], 
                "geometry": [merged_geometry],
                last_col: [None]  # Add back column of NaN values for the choropleth
            }, geometry="geometry", crs=gdf.crs)

            fig.add_trace(go.Choropleth(
                        geojson=non_mca.__geo_interface__,
                        featureidkey="id",  # Changed from properties.mca
                        locations=non_mca.index,  # Using index instead of mca column
                        z=non_mca[metric].fillna(0),  # Fill NA with 0 for consistent coloring
                        colorscale=[[0, '#e0e0e0'], [1, '#e0e0e0']],  # Light grey
                        showscale=False,
                        name='Non-MCA Regions',
                        hoverinfo='skip'
                    ))

    else:  # If not MCA data
        fig = go.Figure(go.Choropleth(
            geojson=merged_df.__geo_interface__,
            featureidkey=f"properties.{geo_level}",  # Match with GeoJSON properties
            locations=merged_df[geo_level],  # Geographic identifiers in data
            z=merged_df[metric],  # Use precomputed indices for color
            text=merged_df['region'], # Used to show the region name in the hovertemplate
            colorscale=colorscale,  # Reverse the Viridis colour scale
            colorbar=dict(
                tickformat=data_format, # Add percent sign to the colour scale
                tickprefix = unit
            ),
            showscale=len(thresholds) == 0,  # Show the colour scale
            customdata=merged_df[[column]],
            hovertemplate=hovertemplate
        ))
        
        if not show_missing_values:
            last_col = merged_df.columns[-1]
            missing_values_df = merged_df[merged_df[last_col].isna()]
            fig.add_trace(go.Choropleth(
                geojson=missing_values_df.__geo_interface__,
                featureidkey=f"properties.{geo_level}",  # Match with GeoJSON properties
                locations=missing_values_df[geo_level],  # Geographic identifiers in data
                z=missing_values_df[metric].fillna(0),  # Fill NA with 0 for consistent coloring
                colorscale=[[0, '#e0e0e0'], [1, '#e0e0e0']],  # Light grey
                showscale=False,  # Show the colour scale
                hoverinfo='skip'
            ))
    
    if len(thresholds) > 0:
        # Legend positioning
        legend_x = 0.9
        legend_y_start = 1
        box_width = 0.03
        spacing = 0.08

        shapes = []
        annotations = []

        for i in range(len(thresholds) - 1):
            y_position = legend_y_start - i * spacing

            # Add colour box (rectangle)
            shapes.append(dict(
                type="rect",
                xref="paper", yref="paper",
                x0=legend_x - 0.015, x1=legend_x + box_width - 0.015,
                y0=y_position - 0.04, y1=y_position,
                fillcolor=colorscale[i][1],
                line=dict(width=1, color="black")
            ))

            if i == 5:
                y_position -= 0.013
            if i == 0:
                bounds_text = f"{unit}{thresholds[i]:{data_format}} ≤"
            else:
                bounds_text = f"{unit}{thresholds[i]:{data_format}} <"
            # Left label (threshold1 <)
            annotations.append(dict(
                x=legend_x - 0.02,  # Left of the colour box
                y=y_position,
                xref="paper", yref="paper",
                text=bounds_text,
                showarrow=False,
                align="right",
                xanchor="right",
                font=dict(size=12, color="black")
            ))

            # Right label (< threshold2)
            annotations.append(dict(
                x=legend_x + box_width - 0.01,  # Right of the colour box
                y=y_position,
                xref="paper", yref="paper",
                text=f"≤ {unit}{thresholds[i + 1]:{data_format}}",
                showarrow=False,
                align="left",
                xanchor="left",
                font=dict(size=12, color="black")
            ))

        # Update layout
        fig.update_layout(
            shapes=shapes,
            annotations=annotations,
            margin=dict(r=200)  # Extra space for legend
        )


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
        title=wrap_title(column, max_length=100),
        margin={"r":0,"t":50,"l":0,"b":0},  # Adjust margins
        height = height,
        width = 800
    )
    return fig