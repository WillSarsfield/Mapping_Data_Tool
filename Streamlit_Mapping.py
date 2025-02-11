import streamlit as st
import pandas as pd
import geopandas as gpd
import map
import numpy as np
import plotly.express as px
import base64
import re
import math

def make_map_itl(itl_level):
    itlmapping = pd.read_csv('src/itlmapping.csv')
    itl3_shapes_df = gpd.read_file('src/International_Territorial_Level_3_(January_2021)_UK_BUC_V3.geojson')
    map_df = itl3_shapes_df.rename(columns={'ITL321CD': 'itl3'})
    # Merge up from ITL3 level to target level
    map_df = map_df.merge(itlmapping, how='left', on='itl3')
    if itl_level != 'itl3':
        map_df = map_df.groupby([itl_level, f'{itl_level}name']).geometry.apply(lambda x: x.union_all()).reset_index()
    map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=itl3_shapes_df.crs)
    map_df['geometry'] = map_df['geometry'].simplify(0.0001, preserve_topology=True)
    map_df = map_df.rename(columns={f'{itl_level}name': 'region'})
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

# Determine itl code level
def assign_itl_level(code):
    length = len(code)
    if length == 3:
        return 'ITL1'
    elif length == 4:
        return 'ITL2'
    elif length == 5:
        return 'ITL3'
    else:
        return ''

# Determine authority code level
def assign_ca_level(code):
    if code[:3] == 'E47' or code[:3] == 'E61':
        return 'MCA'
    elif len(code) == 9:
        return 'LA'
    else:
        return ''

# Convert image to base 64 (streamlit only displays base 64), these codes are put in styles.css
def get_image_as_base64(file_path):
    with open(file_path, "rb") as file:
        data = base64.b64encode(file.read()).decode("utf-8")
    return data

# Load css styling
@st.cache_data(show_spinner=False)
def load_css(filepath):
    with open(filepath) as f:
        st.html(f"<style>{f.read()}</style>")

# Select ITL or authority, get the respective map file, construct the map figures
@st.cache_data(show_spinner=False)
def get_figures(df, colorscale=None, show_missing_values=False, units='%', dp=2, thresholds=[]):
    if df.iloc[0, 0][:2] == 'TL':
        geo_level = assign_itl_level(df.iloc[0, 0]).lower()
        map_df = make_map_itl(geo_level)
    elif len(df.iloc[0, 0]) == 9:
        geo_level = assign_ca_level(df.iloc[0, 0]).lower()
        map_df = make_map_authorities(geo_level)
    else:
        return [], []
    df = df.rename(columns={df.columns[0]: geo_level})
    mapnames = list(df.set_index(geo_level).columns)
    fig = map.make_choropleths(df.set_index(geo_level), map_df, geo_level, colorscale, show_missing_values, units, dp, thresholds)
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

    if 'levels' in st.session_state:
        levels = st.session_state.levels
    else:
        levels = []

    if 'level' in st.session_state:
        level = st.session_state.level
    else:
        level = ''

    # Load CSS from assets
    load_css('assets/styles.css')
    # Intro to tool above tool itself

    with st.expander(label="**About this tool**", expanded=False):

        st.markdown(
            """
            ### Intro
            ###### Developed by the [TPI Productivity Lab](https://www.productivity.ac.uk/the-productivity-lab/), this tool allows for the quick creation of custom choropleth maps of regions in the United Kingdom, allowing for visual comparisons of different metrics across different geographic areas.

            ##### This tool can produce custom maps in 3 simple steps:
            - **Construct your custom data file**: First construct a CSV file containing your data alongside relevant region codes. Examples are provided on how to do this [here](https://www.lab.productivity.ac.uk/tools/custom-maps).
            - **Upload your data**: Click *Browse Files* below, locate your file, and then press *Upload File*.
            - **Customise your map**: Use the options on the sidebar to alter the colour, view, and units.

            ##### If you want to see some examples of what this tool can do, select one of the pre-existing data sets below.

            ### Customisation Options
            #### Map navigation
            - **Select map**: shows the list of maps produced from the data selected. The names of the maps are the respective column names in the data file.
            - **Change title**: rename the map you are currently working on. (Character limit: 70)
            - **Select geography level**: if your map has 2 or more different types of region codes in the first column, these types will show up in this menu allowing you to choose which type to use.
            #### Formatting
            - **Select units**: choose the units you wish to use from this menu. The selected unit will format the hover data and colourscale/key.
            - **Select decimal places**: choose the number of decimal places you would like your data to be rounded to. The selected number of decimal places will format the hover data and colourscale/key.
            - **Hide the rest of the UK**: enabling this will remove any regions missing data in the map.
            #### Colour options
            - **Use discrete colouring**: enable this to use solid colouring within specified bounds. Here you will be given the option to classify your data into coloured categories based on the bounds you select.
            - **Number of colours**: choose the number of colours used to define the colour scale/colour categories. (minimum 2, maximum 6)
            - **Pick colours**: pick a colour from the colour selection interface or enter a hex code for a specific colour in your scale/categorisations. If using discrete colouring, you can also specify a range in which this colour categorises data on the map.
            """
            )

    # Placeholders for the maps
    figure = st.empty()
    figure_loading = st.empty()
    # Save space for the map while it is switching states
    if fig:
        figure.markdown(
        """
        <div style="border: 0px #ccc; height: 550px; width: 1000px; display: flex; align-items: center; justify-content: center; background-color: #ffffff;">
            <p style="color: #aaa;"></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Beginning of tool body
    with st.expander(label="Pre-existing datasets from **The Productivity Institute Data Lab**", expanded=True):
        # Create buttons with associated images
        col1, col2, col3, col4 = st.columns(4)
        #print(get_image_as_base64('static/ONS_logo_subnationaltrade2022.png'))
        # Image button for Dataset 1
        with col1:
            if st.button(label='', key='Example_button1'):
                df = pd.read_csv("examples/LA_example.csv")
                fig, mapname = get_figures(df)

            if st.button(label='', key='Example_button5'):
                df = pd.read_csv("examples/MCA_digitalisation_innovation.csv")
                fig, mapname = get_figures(df)

        # Image button for Dataset 2
        with col2:
            if st.button(label='', key='Example_button2'):
                df = pd.read_csv("examples/ITL1_Scorecard_input_data_percentage.csv")
                fig, mapname = get_figures(df)
            if st.button(label='', key='Example_button6'):
                df = pd.read_csv("examples/ITL2_example.csv")
                fig, mapname = get_figures(df)

        with col3:
            if st.button(label='', key='Example_button3'):
                df = pd.read_csv("examples/MCA-ITL3_scorecards_data_file_modified.csv")
                fig, mapname = get_figures(df)
            if st.button(label='', key='Example_button7'):
                df = pd.read_csv("examples/ITL_trade_2022.csv")
                levels = ['ITL1', 'ITL2', 'ITL3']
                st.session_state.levels = levels
                level = levels[0]
                st.session_state.level = levels[0]
                fig, mapname = get_figures(df)

        # Image button for Dataset 2
        with col4:
            if st.button(label='', key='Example_button4'):
                df = pd.read_csv("examples/ITL3_scorecards_data_file_modified.csv")
                fig, mapname = get_figures(df)
        

    upload_file = st.file_uploader("Upload a file", type=["csv"])

    # Button to confirm the selection
    if st.button("Upload File"):
        if upload_file:
            st.success(f"Filepath set to: {upload_file.name}")
            df = pd.read_csv(upload_file)
            # Find the levels in the first column
            levels = df.iloc[:, 0]
            levels['ITL_Level'] = df[df.columns[0]].apply(assign_itl_level)
            levels['CA_Level'] = df[df.columns[0]].apply(assign_ca_level)
            levels = list(levels['ITL_Level'].drop_duplicates()) + list(levels['CA_Level'].drop_duplicates())
            if '' in levels:
                levels.remove('')
            if len(levels) > 1:
                st.session_state.levels = levels
                level = levels[0]
                st.session_state.level = levels[0]
            st.session_state.index = 0
            # Generate maps for options in menu
            fig, mapname = get_figures(df)
            if not fig:
                st.error("Region code not recognised.")
        else:
            st.error("No file uploaded yet.")

    # If there are maps to switch between then display the select box
    if mapname:
        st.session_state.index = mapname.index(st.sidebar.selectbox("Select map", options=mapname, index=index))
        # Text box to change current map title
        new_title = st.sidebar.text_input('Change title',value=mapname[st.session_state.index])
        # Validate input: must not be empty, must be the characters in the regex, cannot be longer than 70 characters
        valid_input = True
        if not df.empty:
            if not new_title:
                st.sidebar.error("Cannot accept empty title.")
                valid_input = False
            if not re.match(r"^[A-Za-z0-9 _\-\[\]\{\}\(\),.%*&:£$€]*$", new_title) and valid_input:
                st.sidebar.error("Invalid characters, please do not include special characters.")
                valid_input = False
            if len(new_title) > 70 and valid_input:
                st.sidebar.error("Exceeded character limit, please use no more than 50 characters.")
                valid_input = False
            if valid_input:
                df = df.rename(columns={df.columns[st.session_state.index + 1]: new_title})
                
            if mapname != list(df.columns[1:]):
                st.session_state.df = df
                st.session_state.mapname = list(df.columns[1:])
                st.rerun()
    else:
        # Otherwise show empty select box
        st.sidebar.selectbox("Select map", options=mapname)
    # If there is more than one geography level in the data then allow the user to select
    if len(levels) > 1:
        level = st.sidebar.selectbox("Select geography level", options=levels, index=levels.index(level))
        if 'ITL' == level[:3]:
            level_to_length = {'ITL1': 3, 'ITL2': 4, 'ITL3': 5}
            st.session_state.df = df
            df = df.loc[df[df.columns[0]].str.len() == level_to_length[level]].copy()
        else:
            st.session_state.df = df
            if level == 'MCA':
                df = df.loc[df[df.columns[0]].str[:3].isin(['E47', 'E61'])].copy()
            else:
                df = df.loc[~df[df.columns[0]].str[:3].isin(['E47', 'E61'])].copy()
    else:
        st.session_state.df = df
    # Sidebar updates after upload
    st.sidebar.markdown("---")  # This creates a basic horizontal line (divider)
    unit_options = ['None', '%', '£', '$', '€']
    unit = st.sidebar.selectbox("Select units", options=unit_options)
    dp = st.sidebar.select_slider("Select decimal places", options=list(range(5)), value=0)
    show_missing_values = st.sidebar.toggle(label='Hide the rest of the UK', value=False)
    st.sidebar.markdown("---")  # This creates a basic horizontal line (divider)
    # Colour change options
    discrete_colours = st.sidebar.toggle(label='Use discrete colouring')
    num_colours = st.sidebar.slider("Number of Colours", min_value=2, max_value=6, value=5)

    if not df.empty and 'index' in st.session_state and mapname:
        df[mapname[st.session_state.index]] = (df[mapname[st.session_state.index]].astype(str).str.replace(r"[^\d.-]", "", regex=True))
        df[mapname[st.session_state.index]] = pd.to_numeric(df[mapname[st.session_state.index]], errors="coerce")

    # Colour pickers
    colours = []
    # Create two columns in the sidebar using container
    with st.sidebar.container():
        colour_column1, colour_column2 = st.columns([1, 1])  # Create two columns
        if discrete_colours:
            # Create evenly spaced thresholds
            if not df.empty and mapname:
                min_val = df[mapname[st.session_state.index]].min()
                max_val = df[mapname[st.session_state.index]].max()
                thresholds = np.linspace(min_val, max_val, num_colours+1)
            else:
                thresholds = np.linspace(0, 100, num_colours+1)
                min_val = 0
                max_val = 100
            if any(np.isnan(x) for x in thresholds):
                thresholds = np.linspace(0, 100, num_colours+1)
                min_val = 0
                max_val = 100
            if thresholds[-1] > 10000:
                st.markdown("""
                    <style>
                        /* Increase the sidebar width */
                        [data-testid="stSidebar"] {
                            min-width: 500px;  /* Minimum width */
                            max-width: 500px;  /* Maximum width */
                        }
                    </style>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <style>
                        /* Increase the sidebar width */
                        [data-testid="stSidebar"] {
                            min-width: 300px;  /* Minimum width */
                            max-width: 300px;  /* Maximum width */
                        }
                    </style>
                """, unsafe_allow_html=True)
            # Discrete colouring needs to get thresholds too
            step = float(10 ** -dp)
            non_zero_thresholds = [abs(x) for x in thresholds if x != 0]
            step = min([10 ** (-len(str(val).split('.')[-1].rstrip('0'))) if '.' in str(val) else 1 for val in non_zero_thresholds] + [step])
            for i in range(1, num_colours + 1):
                if thresholds[i-1] == thresholds[i]:
                    thresholds[i] += step
                if i > 3:
                    with colour_column2:  # Use the second column for colours after index 2
                        if i == 4:
                            colour = st.color_picker(f"Pick Colour {i}", "#47be6d")
                            if num_colours != i:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=min(float(thresholds[i+1]), float(thresholds[-1]) - 0.02), value=float(thresholds[i]), step=step)
                            else:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=float(thresholds[i]), value=float(thresholds[i]), step=step)
                        elif i == 5:
                            colour = st.color_picker(f"Pick Colour {i}", "#f4e625")
                            if num_colours != i:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=min(float(thresholds[i+1]), float(thresholds[-1]) - 0.02), value=float(thresholds[i]), step=step)
                            else:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=float(thresholds[i]), value=float(thresholds[i]), step=step)
                        else:
                            colour = st.color_picker(f"Pick Colour {i}", "#ffffff")
                            if num_colours != i:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=min(float(thresholds[i+1]), float(thresholds[-1]) - 0.02), value=float(thresholds[i]), step=step)
                            else:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=float(thresholds[i]), value=float(thresholds[i]), step=step)
                        colours.append(colour)
                else:
                    with colour_column1:  # Use the first column for the first 3 colours
                        if i == 1:
                            colour = st.color_picker(f"Pick Colour {i}", "#440255")
                            thresholds[i-1], thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1]), max_value=min(float(thresholds[i+1]), float(thresholds[-1]) - 0.02), value=[float(thresholds[i-1]), float(thresholds[i])], step=step)
                        elif i == 2:
                            colour = st.color_picker(f"Pick Colour {i}", "#39538b")
                            if num_colours != i:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=min(float(thresholds[i+1]), float(thresholds[-1]) - 0.02), value=float(thresholds[i]), step=step)
                            else:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=float(thresholds[i]), value=float(thresholds[i]), step=step)
                        elif i == 3:
                            colour = st.color_picker(f"Pick Colour {i}", "#26828e")
                            if num_colours != i:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=min(float(thresholds[i+1]), float(thresholds[-1]) - 0.02), value=float(thresholds[i]), step=step)
                            else:
                                thresholds[i] = st.slider(f'Colour {i} range:', float(thresholds[i-1] + step), max_value=float(thresholds[i]), value=float(thresholds[i]), step=step)
                        colours.append(colour)
            custom_colour_scale = colours
        else:
            thresholds=[]
            for i in range(num_colours):
                if i > 2:
                    with colour_column2:  # Use the second column for colours after index 2
                        if i == 3:
                            colour = st.color_picker(f"Pick Colour {i+1}", "#47be6d")
                        elif i == 4:
                            colour = st.color_picker(f"Pick Colour {i+1}", "#f4e625")
                        else:
                            colour = st.color_picker(f"Pick Colour {i+1}", "#ffffff")
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
    

    # Labeling options
    if fig:
        # Save session state variables and load figure
        with figure_loading.container():
            with st.spinner('Loading map...'):
                st.session_state.fig, st.session_state.mapname = get_figures(df, custom_colour_scale, show_missing_values, unit, dp, thresholds)
                figure.plotly_chart(st.session_state.fig[st.session_state.index], use_container_width=True)
        st.session_state.index = index


if __name__ == '__main__':
    pd.options.mode.copy_on_write = True
    main()