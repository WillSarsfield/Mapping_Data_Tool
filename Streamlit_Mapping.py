import streamlit as st
import pandas as pd
import geopandas as gpd
import map
import numpy as np
import plotly.express as px
import base64
import re
# Experimental
# import deepseek

def make_map_itl(itl_level, nat=False):
    itlmapping = pd.read_csv('src/itlmapping-updated.csv')
    itl3_shapes_df = gpd.read_file('src/International_Territorial_Level_3_Updated.geojson')
    map_df = itl3_shapes_df.rename(columns={'ITL325CD': 'itl3'})
    # Merge up from ITL3 level to target level
    map_df = map_df.merge(itlmapping, how='left', on='itl3')
    if itl_level != 'itl3':
        map_df = map_df.groupby([itl_level, f'{itl_level}name']).geometry.apply(lambda x: x.union_all()).reset_index()
    map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=itl3_shapes_df.crs)
    if nat:
        excluded_itl1 = ["TLN", "TLM", "TLL"]
        remaining_itl1 = itlmapping[~itlmapping['itl1'].isin(excluded_itl1)]['itl1'].unique().tolist()
        # Merge geometries of the remaining ITL1 regions
        merged_geom = map_df[map_df[itl_level].isin(remaining_itl1)].geometry.union_all()
        # Remove individual ITL1 regions and add the merged one
        map_df = map_df[~map_df[itl_level].isin(remaining_itl1)]
        # Create merged row with correct format
        merged_row = gpd.GeoDataFrame({
            'itl1': ['TLB'],  # Assign 'TLB' as the new ITL1 code
            'itl1name': ['England'],  # Provide a name for the merged region
            'geometry': [merged_geom]
        }, crs=map_df.crs)
        map_df = pd.concat([map_df, merged_row], ignore_index=True)

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
def get_figures(df, colorscale=None, show_missing_values=False, units='%', dp=2, thresholds=[], map_height=550):
    if df.iloc[0, 0][:2] == 'TL':
        geo_level = assign_itl_level(df.iloc[0, 0]).lower()
        nat = False
        if 'TLB' in list(df.iloc[:, 0]):
            nat = True
        map_df = make_map_itl(geo_level, nat)
    elif len(df.iloc[0, 0]) == 9:
        geo_level = assign_ca_level(df.iloc[0, 0]).lower()
        map_df = make_map_authorities(geo_level)
    else:
        return [], []
    df = df.rename(columns={df.columns[0]: geo_level})
    mapnames = list(df.set_index(geo_level).columns)
    fig = map.make_choropleths(df.set_index(geo_level), map_df, geo_level, colorscale, show_missing_values, units, dp, thresholds, map_height)
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
    
    if 'selected_button' not in st.session_state:  # Selected button from the example datasets
        st.session_state.selected_button = None

    if 'dataset_info' not in st.session_state:
        st.session_state.dataset_info = None
    
    if 'link' not in st.session_state:
        st.session_state.link = None
    
    if 'insights' not in st.session_state:
        st.session_state.insights = ''

    # Load CSS from assets
    load_css('assets/styles.css')
    # Intro to tool above tool itself

    with st.expander(label="**About this tool**", expanded=False):

        st.markdown(
            """
            ### Intro
            ###### Developed by the [TPI Productivity Lab](https://www.productivity.ac.uk/the-productivity-lab/), this tool allows for the quick creation of custom choropleth maps of regions in the United Kingdom, allowing for visual comparisons of different metrics across different geographic areas.

            ##### This tool can produce custom maps in 3 simple steps:
            - **Construct your custom data file**: First construct a CSV file containing your data alongside relevant region codes. A step by step guide is provided on how to do this [here](https://www.lab.productivity.ac.uk/tools/map-tool).
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
            - **Use discrete colouring**: enable this to use solid colouring within specified bounds. Here you will be given the option to classify your data into coloured categories based on the bounds you select. Precise data will be inflated to account for the small increments.
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
    
    def reset_insights():
        st.session_state.insights = ''

    # Define callback functions that return data
    def button1_callback():
        st.session_state.selected_button = "Subregional productivity data - local authoritites 2022"
        st.session_state.dataset_info = "This dataset contains information about subregional productivity"
        st.session_state.link = "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/labourproductivity/articles/regionalandsubregionalproductivityintheuk/june2023"
        df = pd.read_csv("examples/LA_example.csv")
        if not df.empty:
            fig, mapname = get_figures(df)
            levels = []
            st.session_state.levels = levels
            st.session_state.level = 'LA'
            st.session_state.fig = fig
            st.session_state.mapname = mapname
            st.session_state.df = df

    def button2_click():
        st.session_state.selected_button = "2024 ITL1 Scorecard Data"
        st.session_state.dataset_info = "This dataset includes scorecards for all 12 ITL1 regions in the United Kingdom. These scorecards indicate for each ITL1 region how well the region is performing as compared to the median of all ITL1 regions in the UK, for a broad set of indicators. These indicators are considered to be drivers of productivity and are classified according to five broad categories:  Business performance & characteristics; Skills & training; Policy & institutions; Health & wellbeing; Investment, infrastructure & connectivity."
        st.session_state.link = "https://lab.productivity.ac.uk/data/productivity-datasets/ITl1-scorecards/"
        df = pd.read_csv("examples/ITL1_Scorecard_input_data_percentage.csv")
        if not df.empty:
            fig, mapname = get_figures(df)
            levels = []
            st.session_state.levels = levels
            st.session_state.level = 'ITL1'
            st.session_state.fig = fig
            st.session_state.mapname = mapname
            st.session_state.df = df

    def button3_click():
        st.session_state.selected_button = "2024 MCA Scorecard data"
        st.session_state.dataset_info = "This dataset includes scorecards for all Mayoral Combined Authorities (MCA) in the United Kingdom. These scorecards indicate how well each MCA area is performing compared to the UK weighted mean of all ITL1 regions in the UK for a broad set of indicators, including productivity performance and drivers of productivity according to the categories: Business Performance; Skills & Training; Health & Wellbeing, and, Investment, infrastructure & Connectivity."
        st.session_state.link = "https://lab.productivity.ac.uk/data/productivity-datasets/MCA-scorecards/"
        df = pd.read_csv("examples/MCA-ITL3_scorecards_data_file_modified.csv")
        if not df.empty:
                fig, mapname = get_figures(df)
                levels = []
                st.session_state.levels = levels
                st.session_state.level = 'MCA'
                st.session_state.fig = fig
                st.session_state.mapname = mapname
                st.session_state.df = df

    def button4_click():
        st.session_state.selected_button = "2024 ITL3 Scorecard data"
        st.session_state.dataset_info = "The TPI UK ITL3 scorecards are produced to assess the United Kingdom's subregional productivity performance through a range of productivity indicators and drivers. These scorecards include data for 179 regions, defined by the International Territorial Level 3 (ITL3). In addition data is available for 12 aggregate ITL1 geographies, covering the whole of the United Kingdom. Data is available for three indicators of productivity, and 12 productivity drivers."
        st.session_state.link = "https://lab.productivity.ac.uk/data/productivity-datasets/ITL3-scorecards/"
        df = pd.read_csv("examples/ITL3_scorecards_data_file_modified.csv")
        if not df.empty:
            fig, mapname = get_figures(df)
            levels = []
            st.session_state.levels = levels
            st.session_state.level = 'ITL3'
            st.session_state.fig = fig
            st.session_state.mapname = mapname
            st.session_state.df = df

    def button5_click():
        st.session_state.selected_button = "TPI MCA Digitalisation and Innovation Indicators"
        st.session_state.dataset_info = "This dataset contains two new indicators produced by the TPI Productivity Lab in collaboration with The Data City to examine disparities in the adoption of innovation practices and the concentration of digital firms within Mayoral Combined Authorities (MCA) in the UK."
        st.session_state.link = "https://lab.productivity.ac.uk/data/productivity-datasets/MCA-digitalisation-innovation-indicators/"
        df = pd.read_csv("examples/MCA_digitalisation_innovation.csv")
        if not df.empty:
            fig, mapname = get_figures(df)
            levels = []
            st.session_state.levels = levels
            st.session_state.level = 'MCA'
            st.session_state.fig = fig
            st.session_state.mapname = mapname
            st.session_state.df = df

    def button6_click():
        st.session_state.selected_button = "2025 ITL2 Regional and Global Trade"
        st.session_state.dataset_info = "This dataset contains data about regional and global trade"
        st.session_state.link = "https://www.google.com"
        df = pd.read_csv("examples/ITL2_example.csv")
        if not df.empty:
            fig, mapname = get_figures(df)
            levels = []
            st.session_state.levels = levels
            st.session_state.level = 'ITL2'
            st.session_state.fig = fig
            st.session_state.mapname = mapname
            st.session_state.df = df

    def button7_click():
        st.session_state.selected_button = "Subnational trade balance data 2022"
        st.session_state.dataset_info = "This dataset contains trade balances for goods and services for EU, non-EU and US trade"
        st.session_state.link = "https://www.ons.gov.uk/businessindustryandtrade/internationaltrade/bulletins/internationaltradeinuknationsregionsandcities/2022"
        df = pd.read_csv("examples/ITL_tradebalance.csv")
        if not df.empty:
            fig, mapname = get_figures(df)
            levels = ['ITL1', 'ITL2', 'ITL3']
            st.session_state.levels = levels
            st.session_state.level = levels[0]
            st.session_state.fig = fig
            st.session_state.mapname = mapname
            st.session_state.df = df
    
    def button8_click():
        st.session_state.selected_button = "2025 UK Measures of National Health and Well-being"
        st.session_state.dataset_info = "This dataset contains measures of health and wellbeing on the national and ITL1 level. These measures are taken from the ONS 'UK Measures of National Well-being Dashboard' where regional data is available."
        st.session_state.link = "https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/articles/ukmeasuresofnationalwellbeing/dashboard"
        df = pd.read_csv("examples/ITL1_Wellbeing.csv")
        if not df.empty:
            fig, mapname = get_figures(df)
            levels = ['ITL1', 'National']
            st.session_state.levels = levels
            st.session_state.level = levels[0]
            st.session_state.fig = fig
            st.session_state.mapname = mapname
            st.session_state.df = df

    def button9_click():
        st.session_state.selected_button = "2024 UK local authority and regional greenhouse gas emissions"
        st.session_state.dataset_info = "This data set contains greenhouse gas emissions measured in carbon dioxide equivalent. These are accredited official statistics from the Department of Energy Security and Net Zero which cover local authorities and has been aggregated to the different International Territorial Levels."
        st.session_state.link = "https://www.gov.uk/government/statistics/uk-local-authority-and-regional-greenhouse-gas-emissions-statistics-2005-to-2022"
        df = pd.read_csv("examples/all_emissions_2022.csv")
        if not df.empty:
            fig, mapname = get_figures(df)
            levels = ['ITL3', 'ITL2', 'ITL1', 'LA']
            st.session_state.levels = levels
            st.session_state.level = levels[0]
            st.session_state.fig = fig
            st.session_state.mapname = mapname
            st.session_state.df = df

    # In your main UI code:
    with st.expander(label="Pre-existing datasets from **The Productivity Institute Data Lab**", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        # Set button types
        button1_type = 'primary' if st.session_state.selected_button == "Subregional productivity data - local authoritites 2022" else 'secondary'
        button2_type = 'primary' if st.session_state.selected_button == "2024 ITL1 Scorecard Data" else 'secondary'
        button3_type = 'primary' if st.session_state.selected_button == "2024 MCA Scorecard data" else 'secondary'
        button4_type = 'primary' if st.session_state.selected_button == "2024 ITL3 Scorecard data" else 'secondary'
        button5_type = 'primary' if st.session_state.selected_button == "TPI MCA Digitalisation and Innovation Indicators" else 'secondary'
        button6_type = 'primary' if st.session_state.selected_button == "2025 ITL2 Regional and Global Trade" else 'secondary'
        button7_type = 'primary' if st.session_state.selected_button == "Subnational trade balance data 2022" else 'secondary'
        button8_type = 'primary' if st.session_state.selected_button == "2025 UK Measures of National Health and Well-being" else 'secondary'
        button9_type = 'primary' if st.session_state.selected_button == "2024 UK local authority and regional greenhouse gas emissions" else 'secondary'

        with col1:
            if st.button(label='', key='Example_button1', type=button1_type, on_click=button1_callback):
                st.rerun()
            if st.button(label='', key='Example_button5', type=button5_type, on_click=button5_click):
                st.rerun()
            if st.button(label='', key='Example_button9', type=button9_type, on_click=button9_click):
                st.rerun()
        
        with col2:
            if st.button(label='', key='Example_button2', type=button2_type, on_click=button2_click):
                st.rerun()
            if st.button(label='', key='Example_button6', type=button6_type, on_click=button6_click):
                st.rerun()
        
        with col3:
            if st.button(label='', key='Example_button3', type=button3_type, on_click=button3_click):
                st.rerun()
            if st.button(label='', key='Example_button7', type=button7_type, on_click=button7_click):
                st.rerun()
        
        with col4:
            if st.button(label='', key='Example_button4', type=button4_type, on_click=button4_click):
                st.rerun()
            if st.button(label='', key='Example_button8', type=button8_type, on_click=button8_click):
                st.rerun()

        # After buttons, if df was loaded, create figures
        # if dataset is not None:
        #     df = pd.read_csv(dataset)
        #     print(df)
        #     if not df.empty:
        #         print("testing:", df)
        #         fig, mapname = get_figures(df)
        
        if st.session_state.selected_button:
            st.markdown(f"### Currently selected: {st.session_state.selected_button}")
            st.write(st.session_state.dataset_info)
            st.markdown(f"[Click here for more information]({st.session_state.link})")

    upload_file = st.file_uploader("Upload a file", type=["csv"])

    # Button to confirm the selection
    if st.button("Upload File"):
        if upload_file:
            st.session_state.selected_button = None  # So no example datasets are selected if the user inputs their own data
            try:
                df = pd.read_csv(upload_file, encoding="utf-8", on_bad_lines='skip', low_memory=False)
                if df.empty:
                    st.error("Uploaded CSV is empty")
                else:
                    st.success(f"Successfully loaded {upload_file.name}")
            except UnicodeDecodeError:
                st.error("Encoding error: Ensure the file is UTF-8 encoded")
            except pd.errors.ParserError:
                st.error("Parsing error: check if the csv format is valid")
            except Exception as e:
                st.error(f"An unexpected error occured: {e}")


            # Find the levels in the first column
            levels = df.iloc[:, 0]
            levels['ITL_Level'] = df[df.columns[0]].apply(assign_itl_level)
            levels['CA_Level'] = df[df.columns[0]].apply(assign_ca_level)
            levels = pd.concat([levels['ITL_Level'], levels['CA_Level']]).drop_duplicates().tolist()
            if 'TLB' in list(df[df.columns[0]]):
                levels.append('National')
            if '' in levels:
                levels.remove('')
            if len(levels) > 1:
                st.session_state.levels = levels
                level = levels[0]
                st.session_state.level = levels[0]
            st.session_state.index = 0
            # Generate maps for options in menu
            fig, mapname = get_figures(df)
            reset_insights()
            if not fig:
                st.error("Region code not recognised.")
        else:
            st.error("No file uploaded yet.")

    # If there are maps to switch between then display the select box
    if mapname:
        if index >= len(mapname) or index < 0:
            index = 0
        st.session_state.index = mapname.index(st.sidebar.selectbox("Select map", options=mapname, index=index, on_change=reset_insights))
        # Text box to change current map title
        new_title = st.sidebar.text_input('Change title',value=mapname[st.session_state.index])
        # Validate input: must not be empty, must be the characters in the regex, cannot be longer than 70 characters
        valid_input = True
        if not df.empty:
            if not new_title:
                st.sidebar.error("Cannot accept empty title.")
                valid_input = False
            if valid_input:
                df = df.rename(columns={df.columns[st.session_state.index + 1]: new_title})
                
            if mapname != list(df.columns[1:]):
                st.session_state.df = df
                st.session_state.mapname = list(df.columns[1:])
                reset_insights()
                st.rerun()
    else:
        # Otherwise show empty select box
        st.sidebar.selectbox("Select map", options=mapname)
    # If there is more than one geography level in the data then allow the user to select
    if len(levels) > 1:
        level = st.sidebar.selectbox("Select geography level", options=levels, index=levels.index(level), on_change=reset_insights)
        if 'ITL' == level[:3]:
            level_to_length = {'ITL1': 3, 'ITL2': 4, 'ITL3': 5}
            st.session_state.df = df
            df = df.loc[(df[df.columns[0]].str.len() == level_to_length[level]) & (df[df.columns[0]] != 'TLB')].copy()
        elif level == 'National':
            st.session_state.df = df
            df = df[df[df.columns[0]].isin(['TLB', 'TLL', 'TLM', 'TLN'])]
        else:
            st.session_state.df = df
            if level == 'MCA':
                df = df.loc[df[df.columns[0]].str[:3].isin(['E47', 'E61'])].copy()
            else:
                df = df.loc[df[df.columns[0]].str.len() == 9].copy()
    else:
        st.session_state.df = df
        st.session_state.levels = []
    # Sidebar updates after upload
    st.sidebar.markdown("---")  # This creates a basic horizontal line (divider)
    unit_options = ['None', '%', '£', '$', '€']
    unit = st.sidebar.selectbox("Select units", options=unit_options)
    dp = st.sidebar.select_slider("Select decimal places", options=list(range(6)), value=0)
    show_missing_values = st.sidebar.toggle(label='Hide the rest of the UK', value=False)
    map_height = st.sidebar.slider("Adjust map size", min_value=0.25, max_value=float(2), value=float(1), step=0.01) * 550
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
        if discrete_colours:
            # Create evenly spaced thresholds
            if not df.empty and mapname:
                min_val = df[mapname[st.session_state.index]].min()
                max_val = df[mapname[st.session_state.index]].max()
                thresholds = np.linspace(min_val, float(max_val), num_colours+1)
            else:
                thresholds = np.linspace(0, 100, num_colours+1)
                min_val = 0
                max_val = 100
            if any(np.isnan(x) for x in thresholds):
                thresholds = np.linspace(0, 100, num_colours+1)
                min_val = 0
                max_val = 100
            thresholds = [round(x, 5) for x in thresholds]
            colour_column1, colour_column2, colour_column3, colour_column4, colour_column5 = st.columns(5)  # Create two columns
            step = float(10**-(dp+1))
            for i in range(1, num_colours + 1):
                if i > 3:
                    if i == 4:
                        if num_colours != i:
                            with colour_column4:
                                colour = st.color_picker(f"-", "#47be6d", label_visibility='hidden')
                            with colour_column5:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), float(thresholds[i+1]  - step/10), float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                        else:
                            with colour_column4:
                                colour = st.color_picker(f"-", "#47be6d", label_visibility='hidden')
                            with colour_column5:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), value=float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                    elif i == 5:
                        if num_colours != i:
                            with colour_column1:
                                st.text_input('-', f'{float(thresholds[i-1] + step/10):.{dp}f}', label_visibility='hidden', disabled=True, key=f'text_input_{i}')
                            with colour_column2:
                                colour = st.color_picker(f"-", "#f4e625", label_visibility='hidden')
                            with colour_column3:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), float(thresholds[i+1]  - step/10), float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                        else:
                            with colour_column1:
                                st.text_input('-', f'{float(thresholds[i-1] + step/10):.{dp}f}', label_visibility='hidden', disabled=True, key=f'text_input_{i}')
                            with colour_column2:
                                colour = st.color_picker(f"-", "#f4e625", label_visibility='hidden')
                            with colour_column3:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), value=float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                    else:
                        if num_colours != i:
                            with colour_column4:
                                colour = st.color_picker(f"-", "#ffffff", label_visibility='hidden')
                            with colour_column5:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), float(thresholds[i+1]  - step/10), float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                        else:
                            with colour_column4:
                                colour = st.color_picker(f"-", "#ffffff", label_visibility='hidden')
                            with colour_column5:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), value=float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                else:
                    if i == 1:
                        with colour_column1:
                            thresholds[i-1] = st.number_input('<', max_value=float(thresholds[i] - step/10), value=float(thresholds[i-1]), step=step, key=f'-input{i}', label_visibility="hidden", format=f'%.{dp}f')
                        with colour_column2:
                            colour = st.color_picker(f"-", "#440255", label_visibility='hidden')
                        with colour_column3:
                            thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), float(thresholds[i+1]  - step/10), float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                    elif i == 2:
                        if num_colours != i:
                            with colour_column4:
                                colour = st.color_picker(f"-", "#39538b", label_visibility='hidden')
                            with colour_column5:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), float(thresholds[i+1]  - step/10), float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                        else:
                            with colour_column4:
                                colour = st.color_picker(f"-", "#39538b", label_visibility='hidden')
                            with colour_column5:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), value=float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                    elif i == 3:
                        if num_colours != i:
                            with colour_column1:
                                st.text_input('-', f'{float(thresholds[i-1] + step/10):.{dp}f}', label_visibility='hidden', disabled=True, key=f'text_input_{i}')
                            with colour_column2:
                                colour = st.color_picker(f"-", "#26828e", label_visibility='hidden')
                            with colour_column3:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), float(thresholds[i+1]  - step/10), float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                        else:
                            with colour_column1:
                                st.text_input('-', f'{float(thresholds[i-1] + step/10):.{dp}f}', label_visibility='hidden', disabled=True, key=f'text_input_{i}')
                            with colour_column2:
                                colour = st.color_picker(f"-", "#26828e", label_visibility='hidden')
                            with colour_column3:
                                thresholds[i] = st.number_input('<', float(thresholds[i-1] + step/10), value=float(thresholds[i]), step=step, key=f'+input{i}', label_visibility="hidden", format=f'%.{dp}f')
                colours.append(colour)
                # print(float(thresholds[i]))
            custom_colour_scale = colours
        else:
            thresholds=[]
            colour_column1, colour_column2 = st.columns(2)  # Create two columns
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
                st.session_state.fig, st.session_state.mapname = get_figures(df, custom_colour_scale, show_missing_values, unit, dp, thresholds, map_height)
                figure.plotly_chart(st.session_state.fig[st.session_state.index], use_container_width=True,
                    config = {
                        'toImageButtonOptions': {
                            'filename': f"TPI_UK_Colour_Map_{st.session_state.mapname[st.session_state.index].replace(' ','_')}",
                            'scale': 2
                        }
                    }
                )
            map_index = st.session_state.index
            st.session_state.index = index

        # Experimental
        # with st.expander('Insights from AI', expanded=False):
        #     with st.spinner('Loading insights...'):
        #         if level[:3].lower() == 'itl':
        #             mapping = pd.read_csv('src/itlmapping.csv')[[level.lower(), f'{level.lower()}name']].set_index(level.lower()).drop_duplicates()
        #         elif level == 'National':
        #             mapping = pd.DataFrame({'itl1': ['TLB', 'TLL', 'TLM', 'TLN'],
        #                                     'itl1name': ['England', 'Wales', 'Scotland', 'Northern Ireland']}).set_index('itl1')
        #             level = 'ITL1'
        #         else:
        #             mapping = pd.read_csv('src/mcamapping.csv')[[level.lower(), f'{level.lower()}name']].set_index(level.lower()).drop_duplicates()
        #         insights_df = df[[df.columns[0], st.session_state.mapname[map_index]]].set_index(df.columns[0])
        #         insights_df = insights_df.join(mapping).set_index(f'{level.lower()}name', drop=True)[st.session_state.mapname[map_index]].to_dict()         
        #         if len(st.session_state.insights) == 0:
        #             insight = deepseek.get_insight('map of the UK', st.session_state.mapname[map_index], insights_df)
        #             st.session_state.insights = insight
        #         else:
        #             insight = st.session_state.insights
        #         st.write(insight)
            

        # filename = f"{mapname[st.session_state.index]}.png"
        # # Save the figure as PNG
        # pio.write_image(fig[st.session_state.index], filename, format="png", engine="kaleido", scale=3)

        # # Provide a download link for the PNG file
        # with open(filename, "rb") as file:
        #     st.download_button(
        #         label="Download Plot as PNG",
        #         data=file,
        #         file_name=filename,
        #         mime="image/png"
        #     )
        #     print(btn)


if __name__ == '__main__':
    pd.options.mode.copy_on_write = True
    main()