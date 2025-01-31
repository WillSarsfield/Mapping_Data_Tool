import streamlit as st
import pandas as pd
import geopandas as gpd
import map
import numpy as np
import plotly.express as px

def make_map_itl(itl_level):
    itlmapping = pd.read_csv('src/itlmapping.csv')
    itl3_shapes_df = gpd.read_file('src/International_Territorial_Level_3_(January_2021)_UK_BUC_V3.geojson')
    map_df = itl3_shapes_df.rename(columns={'ITL321CD': 'itl3'})
    if itl_level != 'itl3':
        map_df = map_df.merge(itlmapping, how='left', on='itl3')
        map_df = map_df.groupby([itl_level, f'{itl_level}name']).geometry.apply(lambda x: x.union_all()).reset_index()
    map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=itl3_shapes_df.crs)
    map_df['geometry'] = map_df['geometry'].simplify(0.0001, preserve_topology=True)
    map_df = map_df.rename(columns={'itl2name': 'region'})
    return map_df

def make_map_authorities(authority_level):
    mcamapping = pd.read_csv('src/mcamapping.csv')
    la_shapes_df = gpd.read_file('src/Local_Authority_Districts_December_2024_Boundaries_UK_BUC_-2087974657986281540.geojson')
    map_df = la_shapes_df.rename(columns={'LAD24CD': 'la'})
    if authority_level != 'la':  # If MCA data is entered
        # Merge all data with MCA mapping
        mapped_df = map_df.merge(mcamapping, how='left', on='la')
        # Split into MCA and non-MCA dataframes
        mca_df = mapped_df[mapped_df['mca'].notna()].copy()
        non_mca_df = mapped_df[mapped_df['mca'].isna()].copy()
        # Process MCA regions
        mca_regions = mca_df.groupby(['mca', 'mcaname']).geometry.apply(lambda x: x.union_all()).reset_index()
        mca_regions = gpd.GeoDataFrame(mca_regions, geometry='geometry', crs=la_shapes_df.crs)
        mca_regions['region_type'] = 'mca'
        # Process non-MCA regions
        non_mca_geometry = non_mca_df.geometry.union_all()
        non_mca_regions = gpd.GeoDataFrame({
            'mca': ['non_mca_all'],
            'mcaname': ['Non-MCA Regions'],
            'geometry': [non_mca_geometry],
            'region_type': ['non_mca']
        }, geometry='geometry', crs=la_shapes_df.crs)
        # Merge MCA and non-MCA regions
        map_df = pd.concat([mca_regions, non_mca_regions], ignore_index=True)
        map_df = map_df.rename(columns={'mcaname': 'region'})
    else:
        # Merge the mca mapping to the map df so the region names can be displayed on the map
        map_df = map_df.merge(mcamapping[['la', 'laname']], how='left', on='la')
        map_df = map_df.rename(columns={'laname': 'region'})
    map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=la_shapes_df.crs)
    map_df['geometry'] = map_df['geometry'].simplify(0.0001, preserve_topology=True)
    return map_df

# Generate the colour scale
def generate_colour_scale(colours, n=256):
    # Interpolate between colours
    colour_scale = []
    for i in range(len(colours) - 1):
        start = np.array(px.colors.hex_to_rgb(colours[i]))
        end = np.array(px.colors.hex_to_rgb(colours[i + 1]))
        steps = np.linspace(0, 1, n // (len(colours) - 1))
        interpolated = (1 - steps)[:, None] * start + steps[:, None] * end
        colour_scale.extend([f"rgb({int(r)},{int(g)},{int(b)})" for r, g, b in interpolated])
    return colour_scale[::-1]

@st.cache_data
def get_figures(df, colorscale=None, show_missing_values=False, labels = False, units='%', dp=2):    
    if df.iloc[:, 0][0][:2] == 'TL':
        geo_level = f'itl{str(len(df.iloc[:, 0][0]) - 2)}'
        map_df = make_map_itl(geo_level)
        df = df.rename(columns={df.columns[0]: geo_level})
    elif len(df.iloc[:, 0][0]) == 9:
        if df.iloc[:, 0][0][:3] == 'E47' or df.iloc[:, 0][0][:3] == 'E61':  # E47 = MCA, E61 = GLA
            geo_level = 'mca'
        else:
            geo_level = 'la'
        map_df = make_map_authorities(geo_level)
        df = df.rename(columns={df.columns[0]: geo_level})
    mapnames = list(df.set_index(geo_level).columns)
    fig = map.make_choropleths(df.set_index(geo_level), map_df, geo_level, colorscale, show_missing_values, labels, units, dp)
    return fig, mapnames
    
def main():
    st.set_page_config(layout="wide")

    st.sidebar.html("<a href='https://lab.productivity.ac.uk' alt='The Productivity Lab'></a>")
    st.logo("static/logo.png", link="https://lab.productivity.ac.uk/", icon_image=None)

    st.sidebar.markdown("---")  # This creates a basic horizontal line (divider)

    if 'fig' in st.session_state:
        fig = st.session_state.fig
    else:
        fig = []

    if 'mapname' in st.session_state:
        mapname = st.session_state.mapname
    else:
        mapname = []

    if 'index' in st.session_state:
        index = st.session_state.index
    else:
        index = 0

    if 'df' in st.session_state:
        df = st.session_state.df
    else:
        df = pd.DataFrame()

    # Intro to tool above tool itself

    with st.expander(label="**About this tool**", expanded=False):

        st.markdown(
            """

            ###### Developed by the [TPI Productivity Lab](https://www.productivity.ac.uk/the-productivity-lab/), this tool allows for the quick creation of custom choropleth maps of regions in the United Kingdom, allowing for visual comparisons of different metrics across different geographic areas.

            ##### This tool can produce multiple maps in 3 simple steps:
            - **Construct your custom data file**: First construct a CSV file containing your data alongside relevant region codes. Examples are provided on how to do this.
            - **Upload your data**: Click *Browse Files* below, locate your file, and then press *Generate Maps*.
            - **Customise your map**: Use the options on the sidebar to alter the colour, labels, and units.
            """
            )

    figure = st.empty()

    # Beginning of tool body

    upload_file = st.file_uploader("Upload a file", type=["csv"])

    if mapname:
        index = mapname.index(st.sidebar.selectbox("Select map", options=mapname))
    else:
        st.sidebar.selectbox("Select map", options=mapname)
    # Sidebar updates after upload
    st.sidebar.markdown("---")  # This creates a basic horizontal line (divider)
    unit_options = ['%', '£', '$', '€', 'None']
    unit = st.sidebar.selectbox("Select units", options=unit_options)
    dp = st.sidebar.select_slider("Select decimal places", options=list(range(5)), value=0)
    show_missing_values = st.sidebar.toggle(label='Hide the rest of the UK', value=False)
    labels = st.sidebar.toggle(label='Show region names', value=False)
    st.sidebar.markdown("---")  # This creates a basic horizontal line (divider)
    # Colour change options
    num_colours = st.sidebar.slider("Number of Colours", min_value=2, max_value=6, value=5)

    # Colour pickers
    colours = []
    # Create two columns in the sidebar using container
    with st.sidebar.container():
        colour_column1, colour_column2 = st.columns([1, 1])  # Create two columns
        
        for i in range(num_colours):
            if i > 2:
                with colour_column2:  # Use the second column for colours after index 2
                    if i == 3:
                        colour = st.color_picker(f"Pick Colour {i+1}", "#47be6d")
                    elif i == 4:
                        colour = st.color_picker(f"Pick Colour {i+1}", "#f4e625")
                    else:
                        colour = st.color_picker(f"Pick Colour {i+1}", "#FFFFFF")
                    colours.append(colour)
            else:
                with colour_column1:  # Use the first column for the first 3 colours
                    if i == 0:
                        colour = st.color_picker(f"Pick Colour {i+1}", "#440255")
                    elif i == 1:
                        colour = st.color_picker(f"Pick Colour {i+1}", "#39538b")
                    elif i == 2:
                        colour = st.color_picker(f"Pick Colour {i+1}", "#26828e")
                    colours.append(colour)

    custom_colour_scale = generate_colour_scale(colours)
    st.sidebar.markdown("---")  # This creates a basic horizontal line (divider)
    
    # Button to confirm the selection
    if st.button("Generate Maps"):
        if upload_file:
            st.success(f"Filepath set to: {upload_file.name}")
            df = pd.read_csv(upload_file)
            fig, mapname = get_figures(df, custom_colour_scale, show_missing_values, labels, unit, dp)
        else:
            st.error("No file uploaded yet.")

    # Labeling options
    if fig:
        # Save session state variables and load figure
        st.session_state.fig, st.session_state.mapname = get_figures(df, custom_colour_scale, show_missing_values, labels, unit, dp)
        st.session_state.df = df
        figure.plotly_chart(st.session_state.fig[index], use_container_width=True)
        st.session_state.index = index


if __name__ == '__main__':
    main()